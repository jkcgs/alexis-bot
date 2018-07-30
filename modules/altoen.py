from bot import Command, categories
import urllib.parse as urlparse

from bot.utils import img_embed


class AltoEn(Command):
    __version__ = '0.1.0'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'altoen'
        self.help = '$[altoen-help]'
        self.category = categories.IMAGES

    async def handle(self, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('$[format]: $[altoen-format]')
            return

        if len(cmd.text) > 25:
            await cmd.answer('$[altoen-too-long]')
            return

        altourl = "https://est.ceii.ufro.cl/~jk/alto.php?size=1000&text=" + urlparse.quote(cmd.text)
        await cmd.answer(embed=img_embed(altourl))
