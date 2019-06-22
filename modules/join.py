from bot import Command, categories
from bot.utils import get_server_role


class JoinCmd(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'
    cfg_name = 'joinrole_id'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'join'
        self.aliases = ['joinrole']
        self.help = '$[autorole-help]'
        self.format = '$[autorole-format]'
        self.allow_pm = False
        self.category = categories.OTHER
        self.user_delay = 5

    async def handle(self, cmd):
        if not self.can_manage_roles(cmd.server):
            await cmd.answer('$[autorole-error-cant]')
            return

        if cmd.name == self.aliases[0]:
            if not cmd.owner:
                return

            if cmd.text == '':
                await cmd.answer('Usage: `$CMD unset` or `$CMD <role name>` to set the role to be used with `$PXjoin`.')
                return

            if cmd.text == 'unset':
                await cmd.answer('The $PXjoin command is now disabled.')
                return

            role = get_server_role(cmd.server, ' '.join(cmd.args))
            if role is None:
                await cmd.answer('$[autorole-not-found]')
            elif role >= cmd.server.me.top_role:
                await cmd.answer('$[autorole-cant-assign]')
            else:
                cmd.config.unset(JoinCmd.cfg_name, role.id)
                await cmd.answer('$[autorole-added]')
            return
