import asyncio

import aiofiles

from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Render import Mode
from gdo.core.Connector import Connector
from gdo.core.GDO_Server import GDO_Server
from gdo.core.GDO_Session import GDO_Session
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
        return Mode.MARKDOWN

    def get_path(self, in_or_out: str):
        mod = module_whatsapp.instance()
        return mod.file_path(f'bin/wapp.{in_or_out}')

    def gdo_connect(self) -> bool:
        Logger.debug("Connecting WhatsApp")
        self._connected = True
        asyncio.run(self.run())
        return True

    async def run(self):
        try:
            fifo_in = self.get_path('in')
            with open(fifo_in, 'r') as fifo:
                while True:
                    line = fifo.readline().strip()
                    if line:
                        await self.process_line(line)
                    else:
                        await asyncio.sleep(0.2)  # Sleep briefly if no data
        except KeyboardInterrupt as ex:
            raise ex
        except Exception as e:
            print(f"Error reading from FIFO: {e}")

    async def process_line(self, line):
        try:
            Logger.debug(f"WAPP << {line}")
            user_name, user_displayname, channel_name, channel_displayname, text = line.split(':', 4)
            Logger.debug(f"WAPP << {text}")
            Application.mode(Mode.MARKDOWN)
            message = Message(text, Mode.MARKDOWN)
            user = self._server.get_or_create_user(user_name, user_displayname)
            channel = None
            trigger = self._server.get_trigger()
            if channel_name:
                channel = self._server.get_or_create_channel(channel_name, channel_displayname)
                trigger = channel.get_trigger()
            message.env_user(user).env_channel(channel).env_server(self._server).env_session(GDO_Session.for_user(user))
            Application.EVENTS.publish('new_message', message)
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
        try:
            async with aiofiles.open(self.get_path('out'), mode='w') as file:
                await file.write(f"{number}::{line}\n")
        except Exception as ex:
            Logger.exception(ex)
            print(f"Error writing to file: {ex}")

    async def gdo_send_to_user(self, msg: Message):
        Logger.debug(f"WAPP >> {msg._result}")
        user = msg._env_user
        await self.send_to_number(user.get_name(), msg._result)

    async def gdo_send_to_channel(self, msg: Message):
        Logger.debug(f"WAPP >> {msg._result}")
        channel = msg._env_channel
        try:
            async with aiofiles.open(self.get_path('out'), mode='w') as file:
                await file.write(f":{channel.get_name()}:{msg._result}\n")
        except Exception as ex:
            Logger.exception(ex)
            print(f"Error writing to file: {ex}")
