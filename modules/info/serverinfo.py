from datetime import datetime

from discord import Embed

from bot import Command, categories
from bot.utils import format_date, deltatime_to_str


class ServerInfo(Command):
    __version__ = '1.1.1'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'serverinfo'
        self.aliases = ['server', 'guild', 'guildinfo']
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        if cmd.argc == 0:
            if cmd.is_pm:
                await cmd.answer('$[format]: $[serverinfo-format]')
                return
            else:
                cmd.args.append(cmd.server.id)

        server = self.bot.get_server(cmd.args[0])
        if server is None:
            for s in self.bot.servers:
                if s.name == cmd.args[0]:
                    server = s
                    break

        if server is None:
            await cmd.answer('$[serverinfo-not-found]')
            return

        created_diff = deltatime_to_str(datetime.now() - server.created_at)
        bot_count = len([m for m in server.members if m.bot])
        bot_word = cmd.lang.get('serverinfo-bot' + ['s', ''][bot_count == 0])
        emoji_word = cmd.lang.get('serverinfo-emoji' + ['s', ''][len(server.emojis) == 0])

        embed = Embed(title='$[serverinfo-title]')
        cont = '$[serverinfo-name]: {}\n'.format(server.name)
        cont += '$[serverinfo-owner]: {}\n'.format(server.owner)
        cont += '$[serverinfo-created]: {} \n($[serverinfo-since])\n\n'.format(format_date(server.created_at))
        cont += '$[serverinfo-members]\n'
        cont += '$[serverinfo-voice-region]: {}\n'.format(server.region)
        cont += '**ID**: {}'.format(server.id)

        other = []
        if server.large:
            other.append('$[serverinfo-feature-bigserver]')
        if 'VIP_REGIONS' in server.features:
            other.append('$[serverinfo-feature-vipregions]')
        if 'VANITY_URL' in server.features:
            other.append('$[serverinfo-feature-vanity')
        if 'INVITE_SPLASH' in server.features:
            other.append('$[serverinfo-feature-splash]')
        if server.mfa_level > 0:
            other.append('$[serverinfo-2fa]')

        if len(other) > 0:
            cont += '\n\n**Otros**: {}'.format(', '.join(other))

        embed.set_thumbnail(url=server.icon_url)
        embed.description = cont
        embed.set_footer(text='$[answer-for]')

        await cmd.answer(embed, withname=False, locales={
            'author': cmd.author_name,
            'creationdiff': created_diff,
            'memberscount': server.member_count,
            'botcount': bot_count,
            'botword': bot_word,
            'emojicount': len(server.emojis),
            'emojiword': emoji_word
        })
