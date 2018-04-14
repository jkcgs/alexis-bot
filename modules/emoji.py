from bot import Command
from discord import Embed
from bot.utils import pat_emoji, pat_normal_emoji
import re


class Emoji(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'emoji'
        self.help = 'Envía la imagen en grande de un emoji custom'

    async def handle(self, cmd):
        if len(cmd.args) != 1:
            await cmd.answer('formato: $PX$NM <emoji>')
            return

        etext = cmd.args[0]
        if re.match(pat_normal_emoji, etext):
            await cmd.answer('no envíes el emoji como texto. Sólo se soportan custom emojis.')
            return

        if not re.match(pat_emoji, etext):
            await cmd.answer('formato: $PX$NM <emoji_custom>')
            return

        emoji_ext = 'gif' if etext[1] == 'a' else 'png'
        emoji_id = etext.split(':')[2][:-1]
        emoji_url = 'https://discordapp.com/api/emojis/{}.{}'.format(emoji_id, emoji_ext)
        embed = Embed()
        embed.set_image(url=emoji_url)
        await cmd.answer('', embed=embed)
