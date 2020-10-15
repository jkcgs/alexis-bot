from bot import Command, categories


class Fullwidth(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'
    __description__ = 'Translate a set of allowed characters (below) to the fullwidth format.'

    supported = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&()+,-./:;<=>?@[\\]^`{|}'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'fullwidth'
        self.aliases = ['full']
        self.help = '$[fullwidth-help]'
        self.category = categories.UTILITY

    async def handle(self, cmd):
        # Fetch the text to convert
        text = [cmd.no_tags(), cmd.lng('fullwidth-default')][cmd.text == ''].replace(' ', '   ')

        # Translate the characters to the fullwidth format
        converted = [chr(0xFEE0 + ord(i)) if i in Fullwidth.supported else i for i in list(text)]

        # Send the result and remove the author's message
        await cmd.answer(''.join(converted), delete_trigger=True, as_embed=True)
