import random
from datetime import datetime

from bot import Command, categories


class Ping(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ping'
        self.help = '$[ping-help]'
        self.format = '$CMD'
        self.category = categories.UTILITY
        self.user_delay = 5

    async def handle(self, cmd):
        now = datetime.now()
        msg = await cmd.answer('$[ping-answer{}]'.format(str(random.choice([1, 2, 3]))))
        if msg is None:
            return

        delay = (datetime.now() - now).microseconds / 1000
        await msg.edit(content=msg.content + ' | `delay: {:.0f} ms`'.format(delay))
