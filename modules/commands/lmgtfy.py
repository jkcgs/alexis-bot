from urllib.parse import urlencode
from modules.base.command import Command


class LetMeGoogleThatForYou(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['lmgtfy', 'google']
        self.help = 'Te ayuda a buscar algo en google'
        self.owner_only = True

    async def handle(self, message, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('Formato: !lmgtfy <texto>')
            return

        texto = ' '.join(cmd.args)
        url = 'https://lmgtfy.com/?' + urlencode({'q': texto})

        await cmd.answer(url)
