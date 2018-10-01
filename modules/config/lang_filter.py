from bot import Command, CommandEvent
from bot.utils import replace_everywhere, get_prefix


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

        if kwargs.get('event', None):
            kwargs['content'] = kwargs['content'].replace('$AU', kwargs['event'].author_name)
            kwargs['content'] = kwargs['content'].replace('$CMD', '$PX$NM')

            if kwargs['embed'] is not None:
                replace_everywhere(kwargs['embed'], '$CMD', '$PX$NM')
                replace_everywhere(kwargs['embed'], '$AU', kwargs['event'].author_name)

            if isinstance(kwargs['event'], CommandEvent):
                kwargs['content'] = kwargs['content'].replace('$NM', kwargs['event'].cmdname)

                if kwargs['embed'] is not None:
                    replace_everywhere(kwargs['embed'], '$NM', kwargs['event'].cmdname)

        prefix = get_prefix(self.bot, svid)
        kwargs['content'] = kwargs['content'].replace('$PX', prefix)
        if kwargs['embed'] is not None:
            replace_everywhere(kwargs['embed'], '$PX', prefix)
