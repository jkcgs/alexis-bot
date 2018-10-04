from datetime import datetime

from discord import Game

from bot import Command, AlexisBot, categories
from bot.utils import deltatime_to_str_short


class BotStatus(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'status'
        self.help = '$[config-status-help]'
        self.bot_owner_only = True
        self.category = categories.SETTINGS
        self.schedule = (self.update, 30)
        self.last_status = ''

        self.count = 0
        self.status_list = [
            lambda: 'discord.cl/bot',
            lambda: 'version {}'.format(AlexisBot.__version__),
            lambda: 'add with !invite',
            lambda: '!help = commands',
            lambda: '{} guilds'.format(len(self.bot.servers)),
            lambda: '{} users'.format(len(set([u.id for u in self.bot.get_all_members() if not u.bot]))),
            lambda: 'with {} bots'.format(len(set([u.id for u in self.bot.get_all_members() if u.bot]))),
            lambda: 'uptime: {}'.format(deltatime_to_str_short(
                datetime.now() - (self.bot.start_time or datetime.now()))
            )
        ]

        self.custom_list = []

    async def handle(self, cmd):
        self.custom_list = [] if cmd.argc < 1 else [f.strip() for f in cmd.text.split('|') if f.strip() != '']
        self.count = 0

        await self.update()
        await cmd.answer('$[config-status-ok]')

    async def update(self):
        status = self.next()
        if status == self.last_status:
            return

        self.last_status = status
        self.log.debug('Changing status to "%s"', status)
        await self.bot.change_presence(game=Game(name=status))

    def next(self):
        curr_list = self.status_list if len(self.custom_list) == 0 else self.custom_list

        if self.count < 0 or self.count > (len(curr_list) - 1):
            self.count = 0

        item = curr_list[self.count]
        self.count += 1

        return item if isinstance(item, str) else item()
