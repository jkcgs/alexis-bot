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
        user = cmd.author if cmd.argc == 0 else cmd.get_member_or_author(cmd.text)
        if user is None:
            await cmd.answer('$[user-not-found]')
            return

        ext_url = str(user.avatar_url_as(static_format='png'))
        text = '$[user-avatar]' if bool(user.avatar_url) else '$[user-avatar-no]'
        embed = img_embed(str(user.avatar_url), text, '[$[avatar-ext-link]]({})'.format(ext_url))
        await cmd.answer(embed=embed, locales={'user': user.display_name})
