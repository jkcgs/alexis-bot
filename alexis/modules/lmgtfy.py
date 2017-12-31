from urllib.parse import urlencode
from alexis import Command


class LetMeGoogleThatForYou(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'lmgtfy'
        self.aliases = ['google', 'comandoqueteayudaraabuscarloquenecesitasdeunaformamuyfacilydivertida']
        self.help = 'Te ayuda a buscar algo en Google'

    async def handle(self, message, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('formato: $PX$NM <texto>')
            return

        url = 'https://lmgtfy.com/?' + urlencode({'q': cmd.text})

        await cmd.answer(url)
