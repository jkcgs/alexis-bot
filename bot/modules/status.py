from discord import Game

from bot import Command, AlexisBot, categories
from bot.utils import deltatime_to_time


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
        self.custom_list = []

        # Generated status list; they are lambdas to retrieve correct information
        self.status_list = [
            lambda: 'https://alexisbot.mak.wtf/',
            lambda: 'version {}'.format(AlexisBot.__version__),
            lambda: 'add with !invite',
            lambda: '!help = commands',
            lambda: 'in {} guilds'.format(len(self.bot.guilds)),
            lambda: 'with {} users'.format(len(set([u.id for u in self.bot.get_all_members() if not u.bot]))),
            lambda: 'with {} bots'.format(len(set([u.id for u in self.bot.get_all_members() if u.bot]))),
            lambda: 'since {}'.format(deltatime_to_time(self.bot.uptime))
        ]

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
        await self.bot.change_presence(activity=Game(status))

    def next(self):
        curr_list = self.status_list if len(self.custom_list) == 0 else self.custom_list

        if self.count < 0 or self.count > (len(curr_list) - 1):
            self.count = 0

        item = curr_list[self.count]
        self.count += 1

        return item if isinstance(item, str) else item()
