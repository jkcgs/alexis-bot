import re

from discord import Embed

from bot import Command, MessageEvent, categories


class InviteFilter(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'

    cfg_filter_status = 'invite_filter_enabled'
    cfg_filter_list = 'invite_filter_list'
    pat_invite = re.compile('(?:https?://)?discord(?:app\.com/invite|.gg)/[a-zA-Z0-9]+')

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'invitefilter'
        self.help = 'Filtra invites a otros servidores de discord'
        self.category = categories.STAFF
        self.owner_only = True

    async def handle(self, cmd):
        filter_enabled = cmd.config.get(self.cfg_filter_status, '0')
        filter_is = ['activado', 'desactivado'][filter_enabled != '1']

        if cmd.argc == 0:
            await cmd.answer('el filtro está filter_is', locales={'filter_is': filter_is})
            return

        if cmd.args[0] == 'toggle':
            filter_enabled = ['0', '1'][filter_enabled == '0']
            filter_is = ['activado', 'desactivado'][filter_enabled != '1']
            cmd.config.set('invite_filter_enabled', filter_enabled)
            await cmd.answer('el filtro ahora está filter_is', locales={'filter_is': filter_is})
            return
        elif cmd.args[0] in ['allow', 'disallow']:
            if cmd.argc <= 1:
                await cmd.answer('formato: $CMD {} <usuario>'.format(cmd.args[0]))
                return

            user = await cmd.get_user(' '.join(cmd.args[1:]), True)
            if user is None:
                await cmd.answer('usuario no encontrado')
                return

            if user.id == cmd.author.id:
                await cmd.answer('no es necesario que te permitas saltar el filtro')
                return

            if cmd.is_owner(user):
                await cmd.answer('no es necesario permitir que un owner se salte el filtro')
                return

            if cmd.args[0] == 'allow':
                if user.id in cmd.config.get_list(self.cfg_filter_list):
                    await cmd.answer('el usuario ya tiene permitido saltar el filtro')
                    return

                cmd.config.add(self.cfg_filter_list, user.id)
                await cmd.answer('usuario agregado')
                return
            else:
                if user.id not in cmd.config.get_list(self.cfg_filter_list):
                    await cmd.answer('el usuario no tiene permitido saltar el filtro')
                    return

                cmd.config.remove(self.cfg_filter_list, user.id)
                await cmd.answer('usuario quitado')
                return
        else:
            await cmd.answer('formato: $CMD (toggle|allow|disallow) (args)')

    async def on_message(self, message):
        evt = MessageEvent(message, self.bot)
        if evt.owner or evt.self:
            return

        filter_enabled = evt.config.get(self.cfg_filter_status, '0') == '1'
        if not filter_enabled or evt.author.id in evt.config.get_list(self.cfg_filter_list):
            return

        invite = self.pat_invite.search(message.content)
        if invite:
            self.log.debug('deleting invite in %s: %s by %s', message.server, invite[0], message.author)
            await self.bot.delete_message_silent(message)

            embed = Embed(title='Invite automáticamente eliminado')
            embed.description = '{}\nPor {} en {}'.format(invite[0], message.author.mention, message.channel.mention)
            await self.bot.send_modlog(message.server, embed=embed)
