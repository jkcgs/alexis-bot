from alexis import Command
import urllib.parse as urlparse

from alexis.base.utils import img_embed


class AltoEn(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'altoen'
        self.help = 'Muestra una imagen basada en el logo "ALTO EN"'

    async def handle(self, message, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('formato: !altoen <str>')
            return

        if len(cmd.text) > 25:
            await cmd.answer('mucho texto, máximo 25 carácteres plix ty')
            return

        altourl = "https://desu.cl/alto.php?size=1000&text=" + urlparse.quote(cmd.text)
        await cmd.answer(embed=img_embed(altourl))
