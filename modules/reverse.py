from bot import Command, categories


class Reverse(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reverse'
        self.help = '$[reverse-help]'
        self.category = categories.UTILITY

    async def handle(self, cmd):
        if cmd.text == '':
            text = '{}: {}'.format(
                cmd.lng('format'), cmd.lng('reverse-format').replace('$CMD', cmd.prefix + self.name)
            )
        else:
            text = cmd.no_tags()

        text = list(text)
        text.reverse()
        text = ''.join(text)

        await cmd.answer(text, as_embed=True)
