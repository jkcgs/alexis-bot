from alexis import Command


class LangFilter(Command):
    def __init__(self, bot):
        super().__init__(bot)

    def pre_send_message(self, kwargs):
        dest = kwargs.get('destination')
        svid = dest.server.id if hasattr(dest, 'server') else None

        lang = self.bot.get_lang(svid)
        if kwargs.get('content', '') != '':
            kwargs['content'] = lang.format(kwargs['content'])
        if kwargs.get('embed', None) is not None:
            kwargs['embed'] = lang.format(kwargs['embed'])
