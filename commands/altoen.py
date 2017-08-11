from commands.base.command import Command
import urllib.parse as urlparse
import discord


class AltoEn(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'altoen'

    async def handle(self, message):
        cmd = self.parse(message)
        if len(cmd.args) < 1:
            await cmd.answer('Formato: !altoen <str>')
            return

        altotext = ' '.join(cmd.args[1:])

        if len(altotext) > 25:
            await cmd.answer('mucho texto, máximo 25 carácteres plix ty')
            return

        altourl = "https://desu.cl/alto.php?size=1000&text=" + urlparse.quote(altotext)
        emb = discord.Embed()
        emb.set_image(url=altourl)
        await self.bot.send_message(message.channel, embed=emb)
