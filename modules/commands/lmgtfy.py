from urllib.parse import urlencode
from modules.base.command import Command


class LetMeGoogleThatForYou(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['lmgtfy', 'google']
        self.help = 'Te ayuda a buscar algo en google'

    async def handle(self, message, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('Formato: !lmgtfy <texto>')
            return

        url = 'https://lmgtfy.com/?' + urlencode({'iie': '1', 'q': cmd.text})

        await cmd.answer(url)
