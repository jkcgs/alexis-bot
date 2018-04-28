from bot import Command
from bot.libs.configuration import ServerConfiguration
from bot.utils import replace_everywhere


class CmdFilter(Command):
    def __init__(self, bot):
        super().__init__(bot)

    def pre_send_message(self, kwargs):
        dest = kwargs['destination']
        svid = dest.server.id if hasattr(dest, 'server') else None
        if svid is None:
            return

        if kwargs['locales'] is not None:
            kwargs['content'] = replace_everywhere(kwargs['content'], kwargs['locales'])
            if kwargs['embed'] is not None:
                kwargs['embed'] = replace_everywhere(kwargs['embed'], kwargs['locales'])
