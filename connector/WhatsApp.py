import asyncio

import aiofiles

from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Render import Mode
from gdo.core.Connector import Connector
from gdo.core.GDO_Session import GDO_Session
from gdo.whatsapp.module_whatsapp import module_whatsapp


class WhatsApp(Connector):
    """
    This connector reads lines from bin/wapp.in.fifo and executes them accordingly
    """

    def get_path(self, in_or_out: str):
        mod = module_whatsapp.instance()
        return mod.file_path(f'bin/wapp.{in_or_out}')

    async def gdo_connect(self):
        await self.read_lines()

    async def read_lines(self):
        file_path = self.get_path('in')
        while True:
            try:
                async with aiofiles.open(file_path, mode='r') as file:
                    async for line in file:
                        await self.process_line(line.strip())
                await asyncio.sleep(0.33)
            except Exception as e:
                print(f"Error reading from file: {e}")
                await asyncio.sleep(1)

    async def process_line(self, line):
        try:
            user_name, user_displayname, channel_name, channel_displayname, text = line.split(':', 5)
            Application.mode(Mode.MARKDOWN)
            Application.fresh_page()
            message = Message(text, Mode.MARKDOWN)
            user = self._server.get_or_create_user(user_name, user_displayname)
            channel = None
            trigger = self._server.get_trigger()
            if channel_name:
                channel = self._server.get_or_create_channel(channel_name, channel_displayname)
                trigger = channel.get_trigger()
            message.env_user(user).env_channel(channel).env_server(self._server).env_session(GDO_Session.for_user(user))
            Application.EVENTS.publish('new_message', message)
            if line.startswith(trigger):
                message._message = line[1:]
                try:
                    asyncio.run(message.execute())
                except Exception as ex:
                    Logger.exception(ex)
                    message._result = Application.get_page()._top_bar.render_irc()
                    message._result += str(ex)
                    asyncio.run(message.deliver())
        except ValueError as e:
            print(f"Error processing line: {line} - {e}")

    async def gdo_send_to_user(self, msg: Message):
        user = msg._env_user
        try:
            async with aiofiles.open(self.get_path('out'), mode='a') as file:
                await file.write(f"{user.get_name()}::{msg._result}\n")
        except Exception as e:
            print(f"Error writing to file: {e}")

    async def gdo_send_to_channel(self, msg: Message):
        channel = msg._env_channel
        try:
            async with aiofiles.open(self.get_path('out'), mode='a') as file:
                await file.write(f":{channel.get_name()}:{msg._result}\n")
        except Exception as e:
            print(f"Error writing to file: {e}")

