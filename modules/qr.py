from urllib.parse import urlencode

from bot import Command, categories
from bot.utils import img_embed


class QRCode(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'qr'
        self.help = '$[qr-help]'
        self.format = '$[qr-format]'
        self.category = categories.IMAGES

    async def handle(self, cmd):
        if cmd.text == '':
            await cmd.answer('$[format]: $[qr-format]')
            return

        url = 'http://chart.apis.google.com/chart?cht=qr&chs=500x500&chld=H|2&' + urlencode({'chl': cmd.text})
        await cmd.answer(embed=img_embed(url))
