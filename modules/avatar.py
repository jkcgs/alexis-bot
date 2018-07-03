from bot import Command, categories
from bot.utils import img_embed


class Avatar(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'avatar'
        self.help = '$[avatar-help]'
        self.category = categories.IMAGES

    async def handle(self, cmd):
        user = cmd.author if cmd.argc == 0 else await cmd.get_user(cmd.text)
        if user is None:
            await cmd.answer('$[user-not-found]')
            return

        has_avatar = user.avatar_url != ''
        avatar_url = user.avatar_url if has_avatar else user.default_avatar_url
        ext_url = avatar_url.replace('.webp', '.png')

        text = '$[user-avatar]' if has_avatar else '$[user-avatar-no]'
        embed = img_embed(avatar_url, text, '[$[avatar-ext-link]]({})'.format(ext_url))
        await cmd.answer(embed=embed, locales={'user': user.display_name})
