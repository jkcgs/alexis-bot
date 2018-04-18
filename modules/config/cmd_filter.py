from bot import Command
from bot.libs.configuration import ServerConfiguration
from bot.utils import replace_everywhere


class CmdFilter(Command):
    def __init__(self, bot):
        super().__init__(bot)

    def pre_send_message(self, kwargs):
        dest = kwargs.get('destination')
        svid = dest.server.id if hasattr(dest, 'server') else None
        if svid is None:
            return

        svconfig = ServerConfiguration(self.bot.sv_config, svid)
        prefix = svconfig.get('command_prefix', self.bot.config['command_prefix'])
        kwargs['content'] = kwargs['content'].replace('$PX', prefix)
        if kwargs.get('content', '').startswith(prefix):
            kwargs['content'] = kwargs['content'][len(prefix):]

        if kwargs.get('embed', None) is not None:
            embed = kwargs.get('embed')
            kwargs.set('embed', replace_everywhere(embed, '$PX', prefix))
