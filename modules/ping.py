import random
from datetime import datetime

from bot import Command


class Ping(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ping'
        self.help = 'Responde al comando *ping*'
        self.user_delay = 5

    async def handle(self, cmd):
        now = datetime.now()
        msg = await cmd.answer(['wena xoro', 'pong!'][int(random.random() >= .5)])
        if msg is None:
            return

        delay = (datetime.now() - now).microseconds / 1000
        await self.bot.edit_message(msg, new_content=msg.content + ' | `delay: {:.0f} ms`'.format(delay))
