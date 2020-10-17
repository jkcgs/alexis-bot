from bot import Command, categories
from bot.utils import img_embed
from bot.regex import pat_emoji, pat_normal_emoji
import re


class Emoji(Command):
    __author__ = 'makzk'
    __version__ = '0.0.2'
    __description__ = 'Retrieves the URL of an emoji and sends it back to the user in an embed.'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'emoji'
        self.help = '$[emoji-help]'
        self.format = '$[emoji-format]'
        self.category = categories.IMAGES

    async def handle(self, cmd):
        if len(cmd.args) != 1:
            return await cmd.send_usage()

        # Check if it's a unicode emoji and send a proper error message back
        etext = cmd.args[0]
        if re.match(pat_normal_emoji, etext):
            await cmd.answer('$[emoji-unsupported]')
            return

        # Validate if the argument it's a custom emoji
        if not re.match(pat_emoji, etext):
            return await cmd.send_usage()

        # Determine wether the emoji is animated or not, and determine it's url, to send it in an Embed
        emoji_ext = 'gif' if etext[1] == 'a' else 'png'
        emoji_id = etext.split(':')[2][:-1]
        emoji_url = 'https://cdn.discordapp.com/emojis/{}.{}'.format(emoji_id, emoji_ext)
        await cmd.answer(img_embed(emoji_url))
