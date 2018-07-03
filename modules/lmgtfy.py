from urllib.parse import urlencode
from bot import Command, categories


class LetMeGoogleThatForYou(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'lmgtfy'
        self.aliases = ['google']
        self.help = 'Te ayuda a buscar algo en Google'
        self.category = categories.FUN

    async def handle(self, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('formato: $PX$NM <texto>')
            return

        url = 'https://lmgtfy.com/?' + urlencode({'q': cmd.text})

        await cmd.answer(url)
