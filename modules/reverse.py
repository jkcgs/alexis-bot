from bot import Command, categories


class Reverse(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reverse'
        self.help = 'Revierte el texto enviado'
        self.category = categories.UTILITY

    async def handle(self, cmd):
        if cmd.text == '':
            text = '{}: {}'.format(
                cmd.lang.get('format'), cmd.lang.get('reverse-format').replace('$CMD', cmd.prefix + self.name)
            )
        else:
            text = cmd.no_tags()

        text = list(text)
        text.reverse()
        text = ''.join(text)

        await cmd.answer_embed(text)
