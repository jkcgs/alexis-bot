import platform

import discord

from bot import AlexisBot, Command, categories, constants
from bot.utils import deltatime_to_time


class BotStats(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'stats'
        self.bot_owner_only = True

    async def handle(self, cmd):
        data = {
            'python_version': platform.python_version(),
            'dpy_version': discord.__version__,
            'bot_class': self.bot.__class__.__name__,
            'bot_version': self.bot.__version__,
            'num_users': len(self.bot.users),
            'num_bots': len([x for x in self.bot.users if x.bot]),
            'num_guilds': len(self.bot.guilds),
            'uptime': deltatime_to_time(self.bot.uptime),
        }

        machine_info = '{system} {release} ({machine}) @ {node}'.format(**platform.uname()._asdict())
        await cmd.answer(
            '```yml\n'
            f'Machine: {machine_info}\n'
            'Version: Python {python_version}, discord.py {dpy_version}, {bot_class} {bot_version}\n'
            'Users: {num_users} ({num_bots} bots), {num_guilds} guilds\n'
            'Uptime: {uptime}'
            '```'.format(**data),
            as_embed=True,
            title=':desktop: Bot system information'
        )


class InfoCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'info'
        self.aliases = ['version']
        self.help = '$[info-help]'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        info_msg = f'**{AlexisBot.name}** $[info-version]: {AlexisBot.__version__}\n' \
                   f'{constants.REPOSITORY_URL}\n\n$[info-invite]'

        invite_link = 'https://discord.com/oauth2/authorize?client_id={}&scope=bot'.format(self.bot.user.id)
        await cmd.answer(info_msg, as_embed=True, locales={'invitelink': invite_link})
