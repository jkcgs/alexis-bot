from alexis import Command
from alexis.libs.configuration import ServerConfigMgrSingle


class CmdFilter(Command):
    def __init__(self, bot):
        super().__init__(bot)

    def pre_send_message(self, kwargs):
        dest = kwargs.get('destination')
        svid = dest.server.id if hasattr(dest, 'server') else None
        if svid is None:
            return

        svconfig = ServerConfigMgrSingle(self.bot.sv_config, svid)
        prefix = svconfig.get('command_prefix', self.bot.config['command_prefix'])
        if prefix == '':
            return

        if kwargs.get('content', '').startswith(prefix):
            kwargs['content'] = kwargs['content'][len(prefix):]
