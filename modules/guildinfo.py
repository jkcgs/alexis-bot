from datetime import datetime

from discord import Embed

from bot import Command, categories
from bot.utils import format_date, deltatime_to_str, auto_int


class GuildInfo(Command):
    __version__ = '1.1.3'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'guildinfo'
        self.aliases = ['guild', 'server', 'serverinfo']
        self.format = '$[guildinfo-format]'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        if cmd.argc == 0:
            if cmd.is_pm:
                return await cmd.send_usage()
            else:
                cmd.args.append(cmd.guild.id)

        guild = self.bot.get_guild(auto_int(cmd.args[0]))
        if guild is None:
            for s in self.bot.guilds:
                if s.name == cmd.args[0]:
                    guild = s
                    break

        if guild is None:
            await cmd.answer('$[guildinfo-not-found]')
            return

        created_diff = deltatime_to_str(datetime.now() - guild.created_at)
        bot_count = len([m for m in guild.members if m.bot])
        bot_word = cmd.lang.get('guildinfo-bot' + ['s', ''][bot_count == 0])
        emoji_word = cmd.lang.get('guildinfo-emoji' + ['s', ''][len(guild.emojis) == 0])

        embed = Embed(title='$[guildinfo-title]')
        cont = '$[guildinfo-name]: {}\n'.format(guild.name)
        cont += '$[guildinfo-owner]: {}\n'.format(guild.owner)
        cont += '$[guildinfo-created]: {} \n($[guildinfo-since])\n\n'.format(format_date(guild.created_at))
        cont += '$[guildinfo-members]\n'
        cont += '$[guildinfo-voice-region]: {}\n'.format(guild.region)
        cont += '**ID**: {}'.format(guild.id)

        other = []
        if guild.large:
            other.append('$[guildinfo-feature-bigserver]')
        if 'VIP_REGIONS' in guild.features:
            other.append('$[guildinfo-feature-vipregions]')
        if 'VANITY_URL' in guild.features:
            other.append('$[guildinfo-feature-vanity]')
        if 'INVITE_SPLASH' in guild.features:
            other.append('$[guildinfo-feature-splash]')
        if guild.mfa_level > 0:
            other.append('$[guildinfo-2fa]')

        if len(other) > 0:
            cont += '\n\n**Otros**: {}'.format(', '.join(other))

        embed.set_thumbnail(url=guild.icon_url)
        embed.description = cont
        embed.set_footer(text='$[answer-for]')

        await cmd.answer(embed, withname=False, locales={
            'author': cmd.author_name,
            'creationdiff': created_diff,
            'memberscount': guild.member_count,
            'botcount': bot_count,
            'botword': bot_word,
            'emojicount': len(guild.emojis),
            'emojiword': emoji_word
        })
