from discord import Embed

from bot import Command, MessageEvent, categories
from bot.regex import pat_invite


class InviteFilter(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    cfg_filter_status = 'invite_filter_enabled'
    cfg_filter_list = 'invite_filter_list'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'invitefilter'
        self.aliases = ['ifilter']
        self.help = '$[ifilter-help]'
        self.category = categories.STAFF
        self.owner_only = True

    async def handle(self, cmd):
        filter_enabled = cmd.config.get(self.cfg_filter_status, '0')
        filter_is = ['$[ifilter-enabled]', '$[ifilter-disabled]'][filter_enabled != '1']

        if cmd.argc == 0:
            await cmd.answer('$[ifilter-status]', locales={'status': filter_is})
            return

        if cmd.args[0] == 'toggle':
            filter_enabled = ['0', '1'][filter_enabled == '0']
            filter_is = ['$[ifilter-enabled]', '$[ifilter-disabled]'][filter_enabled != '1']
            cmd.config.set('invite_filter_enabled', filter_enabled)
            await cmd.answer('$[ifilter-changed]', locales={'status': filter_is})
            return
        elif cmd.args[0] in ['allow', 'disallow']:
            if cmd.argc <= 1:
                await cmd.answer('$[format]: $[ifilter-format]')
                return

            user = cmd.get_member(' '.join(cmd.args[1:]))
            if user is None:
                await cmd.answer('$[ifilter-user-not-found]')
                return

            if user.id == cmd.author.id:
                await cmd.answer('$[ifilter-not-needed]')
                return

            if cmd.is_owner(user):
                await cmd.answer('$[ifilter-err-owner]')
                return

            if cmd.args[0] == 'allow':
                if user.id in cmd.config.get_list(self.cfg_filter_list):
                    await cmd.answer('$[ifilter-already-allowed]')
                    return

                cmd.config.add(self.cfg_filter_list, user.id)
                await cmd.answer('$[ifilter-added]')
                return
            else:
                if user.id not in cmd.config.get_list(self.cfg_filter_list):
                    await cmd.answer('$[ifilter-not-allowed]')
                    return

                cmd.config.remove(self.cfg_filter_list, user.id)
                await cmd.answer('$[ifilter-removed]')
                return
        else:
            await cmd.answer('$[format]: $[ifilter-format]')

    async def on_message(self, message):
        evt = MessageEvent(message, self.bot)
        if evt.owner or evt.self or evt.is_pm:
            return

        filter_enabled = evt.config.get(self.cfg_filter_status, '0') == '1'
        if not filter_enabled or evt.author.id in evt.config.get_list(self.cfg_filter_list):
            return

        invite = pat_invite.search(message.content)
        if invite:
            self.log.debug('Removing invite in %s: %s by %s', message.guild, invite[0], message.author)
            await self.bot.delete_message(message, silent=True)

            embed = Embed(title='$[ifilter-message]')
            embed.description = '{}\nPor {} en {}'.format(invite[0], message.author.mention, message.channel.mention)
            await self.bot.send_modlog(message.guild, embed=embed, logtype='invite_filter')
