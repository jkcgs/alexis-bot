from urllib.parse import urlencode

from bot import Command
from bot.utils import img_embed


class QRCode(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'qr'
        self.help = 'Entrega un código QR del texto enviado'

    async def handle(self, cmd):
        if cmd.text == '':
            await cmd.answer('formato: $PX$NM <texto>')
            return

        url = 'http://chart.apis.google.com/chart?cht=qr&chs=500x500&chld=H|2&' + urlencode({'chl': cmd.text})
        await cmd.answer(embed=img_embed(url))
