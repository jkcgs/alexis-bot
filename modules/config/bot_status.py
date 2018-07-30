from datetime import datetime

from discord import Game

from bot import Command, AlexisBot
from bot.utils import deltatime_to_str_short


class BotStatus(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.count = 0

    async def on_ready(self):
        self.bot.schedule(self.task_other, 30)

    async def task_other(self):
        status_list = [
            lambda: 'discord.cl/bot',
            lambda: 'version {}'.format(AlexisBot.__version__),
            lambda: 'add with !invite',
            lambda: '!help = avail. commands',
            lambda: '{} guilds'.format(len(self.bot.servers)),
            lambda: '{} users'.format(len(set([u.id for u in self.bot.get_all_members() if not u.bot]))),
            lambda: 'with {} bots'.format(len(set([u.id for u in self.bot.get_all_members() if u.bot]))),
            lambda: 'uptime: {}'.format(deltatime_to_str_short(
                datetime.now() - (self.bot.start_time or datetime.now()))
            )
        ]

        status = status_list[self.count]()
        await self.bot.change_presence(game=Game(name=status))

        self.count += 1
        if self.count >= len(status_list):
            self.count = 0
