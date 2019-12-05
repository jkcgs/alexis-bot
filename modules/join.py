import discord

from bot import Command, categories
from bot.utils import get_guild_role


class JoinCmd(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'
    cfg_name = 'joinrole_id'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'join'
        self.help = '$[join-help]'
        self.format = f'$PX{self.name}'
        self.allow_pm = False
        self.category = categories.OTHER
        self.user_delay = 5

    async def handle(self, cmd):
        if not cmd.can_manage_roles():
            await cmd.answer('$[join-error-cant]')
            return

        roleid = cmd.config.get(JoinCmd.cfg_name, '')
        if roleid == '':
            await cmd.answer('$[join-disabled]')
            return

        user_roles = [r.id for r in cmd.author.roles]
        if roleid in user_roles:
            await cmd.answer('$[join-already]')
            return

        role = get_guild_role(cmd.guild, roleid)
        if role is None:
            await cmd.answer('$[join-exec-role-not-found]')
            return

        try:
            await cmd.author.add_roles(role)
            await cmd.answer('$[join-joined]')
        except (discord.Forbidden, discord.HTTPException):
            await cmd.answer('$[join-could-not-assign]')


class JoinRole(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'joinrole'
        self.help = '$[join-help]'
        self.format = '$[join-format]'
        self.allow_pm = False
        self.owner_only = True
        self.category = categories.MODERATION
        self.user_delay = 5

    async def handle(self, cmd):
        if not cmd.can_manage_roles():
            await cmd.answer('$[join-error-cant]')
            return

        if cmd.text == '':
            await cmd.answer('$[usage]: $[join-format]')
            return

        if cmd.text == 'unset':
            cmd.config.unset(JoinCmd.cfg_name)
            await cmd.answer('$[join-now-disabled]')
            return

        role = get_guild_role(cmd.guild, ' '.join(cmd.args))
        if role is None:
            await cmd.answer('$[join-role-not-found]')
        elif role >= cmd.guild.me.top_role:
            await cmd.answer('$[join-cant-assign]')
        else:
            cmd.config.set(JoinCmd.cfg_name, role.id)
            await cmd.answer('$[join-role-set]', locales={'rolename': role.name})
