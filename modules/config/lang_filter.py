from bot import Command, CommandEvent
from bot.utils import replace_everywhere


class LangFilter(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.priority = 10

    def pre_send_message(self, kwargs):
        dest = kwargs.get('destination')
        svid = dest.server.id if hasattr(dest, 'server') else None

        lang = self.get_lang(svid)
        if kwargs.get('content', '') != '':
            kwargs['content'] = lang.format(kwargs['content'], kwargs.get('locales', None))
        if kwargs.get('embed', None) is not None:
            kwargs['embed'] = lang.format(kwargs['embed'], kwargs.get('locales', None))

        if 'event' in kwargs:
            kwargs['content'] = kwargs['content'].replace('$CMD', '$PX$NM')
            kwargs['content'] = kwargs['content'].replace('$PX', kwargs['event'].prefix)

            if kwargs['embed'] is not None:
                replace_everywhere(kwargs['embed'], '$CMD', '$PX$NM')
                replace_everywhere(kwargs['embed'], '$PX', kwargs['event'].prefix)

            if isinstance(kwargs['event'], CommandEvent):
                kwargs['content'] = kwargs['content'].replace('$NM', kwargs['event'].cmdname)

                if kwargs['embed'] is not None:
                    replace_everywhere(kwargs['embed'], '$NM', kwargs['event'].cmdname)
