import asyncio
import json

import aiofiles

from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Render import Mode
from gdo.core.Connector import Connector
from gdo.core.GDO_Server import GDO_Server
from gdo.whatsapp.module_whatsapp import module_whatsapp


class WhatsApp(Connector):
    """
    This connector reads lines from bin/wapp.in.fifo and executes them accordingly
    """

    @classmethod
    def instance(cls) -> "WhatsApp":
        return cls.get_server().get_connector()

    @classmethod
    def get_server(cls) -> GDO_Server:
        return GDO_Server.get_by_connector('whatsapp')

    def get_render_mode(self) -> Mode:
        return Mode.render_markdown

    def gdo_needs_authentication(self) -> bool:
        return False

    def get_path(self, in_or_out: str):
        mod = module_whatsapp.instance()
        return mod.file_path(f'bin/wapp.{in_or_out}')

    async def gdo_connect(self) -> bool:
        Logger.debug("Connecting WhatsApp")
        Application.TASKS.append(asyncio.create_task(self.run(), name='WAppIn'))
        self._outgoing: asyncio.Queue[str] = asyncio.Queue()
        Application.TASKS.append(asyncio.create_task(self.run_outgoing(), name='WAppOut'))
        return True

    async def run(self):
        try:
            fifo_in = self.get_path('in')
            async with aiofiles.open(fifo_in, 'r') as fifo:
                while True:
                    line = (await fifo.readline()).strip()
                    if line:
                        await self.process_line(line)
                    else:
                        await asyncio.sleep(0.2)  # Sleep briefly if no data
        except KeyboardInterrupt as ex:
            raise ex
        except Exception as e:
            print(f"Error reading from FIFO: {e}")

    async def run_outgoing(self):
        """Keep the FIFO writer open and reconnect it only after a pipe error."""
        while True:
            try:
                async with aiofiles.open(self.get_path('out'), 'w') as fifo:
                    while True:
                        await fifo.write(await self._outgoing.get())
                        await fifo.flush()
            except asyncio.CancelledError:
                raise
            except Exception as ex:
                Logger.exception(ex)
                await asyncio.sleep(1)

    async def process_line(self, line):
        try:
            self._connected = True
            Logger.debug(f"WAPP << {line}")
            payload = json.loads(line)
            user_name = payload['user_id']
            user_displayname = payload.get('displayname', '')
            channel_name = payload.get('channel_id', '')
            channel_displayname = payload.get('channel_name', '')
            text = payload['message']
            Logger.debug(f"WAPP << {text}")
            # Application.mode(Mode.markdown)
            message = Message(text, Mode.render_markdown)
            user = await self._server.get_or_create_user(user_name, user_displayname)
            channel = None
            trigger = self._server.get_trigger()
            if channel_name:
                channel = self._server.get_or_create_channel(channel_name, channel_displayname)
                trigger = channel.get_trigger()
            # The FIFO protocol currently carries messages rather than
            # separate membership events.  Treat each received message as a
            # fresh server/channel presence observation.
            await self._server.on_user_joined(user, channel)
            if channel:
                await channel.on_user_joined(user)
            message.env_user(user, True).env_channel(channel).env_server(self._server)
            # await Application.EVENTS.publish('new_message', message)
            if text.startswith(trigger):
                message._message = text[1:]
                try:
                    await message.execute()
                except Exception as ex:
                    Logger.exception(ex)
                    message._result = Application.get_page()._top_bar.render_markdown()
                    message._result += str(ex)
                    await message.deliver()
        except KeyboardInterrupt as ex:
            raise ex
        except Exception as ex:
            Logger.exception(ex)
            print(f"Error processing line: {line}")

    async def send_to_number(self, number: str, line: str):
        await self._outgoing.put(json.dumps({'target': number, 'message': line}) + '\n')

    async def gdo_send_to_user(self, msg: Message, notice: bool=False):
        Logger.debug(f"WAPP >> {msg._result}")
        user = msg._env_user
        await self.send_to_number(user.get_name(), msg._result)

    async def gdo_send_to_channel(self, msg: Message):
        Logger.debug(f"WAPP >> {msg._result}")
        channel = msg._env_channel
        await self._outgoing.put(json.dumps({'target': channel.get_name(), 'message': msg._result}) + '\n')
