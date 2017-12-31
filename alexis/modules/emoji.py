from alexis import Command
from discord import Embed
import re


class Emoji(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'emoji'
        self.help = 'Envía la imagen en grande de un emoji custom'
        self.rx_custom_emoji = re.compile('^<:[a-zA-Z0-9\-_]+:[0-9]+>$')
        self.rx_normal_emoji = re.compile('^:[a-zA-Z\-_]+:$')

    async def handle(self, message, cmd):
        if len(cmd.args) != 1:
            await cmd.answer('formato: !emoji <emoji>')
            return

        etext = cmd.args[0]
        if re.match(self.rx_normal_emoji, etext):
            await cmd.answer('no envíes el emoji como texto. Sólo se soportan custom emojis.')
            return

        if not re.match(self.rx_custom_emoji, etext):
            await cmd.answer('formato: $PX$NM <emoji_custom>')
            return

        emoji_id = etext.split(':')[2][:-1]
        emoji_url = 'https://discordapp.com/api/emojis/{}.png'.format(emoji_id)
        embed = Embed()
        embed.set_image(url=emoji_url)
        await cmd.answer('', embed=embed)
