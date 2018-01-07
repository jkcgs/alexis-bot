from alexis import Command
from alexis.base.utils import img_embed


class Avatar(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'avatar'
        self.help = 'Envia el ávatar del usuario que envió el comando o del usuario mencionado'

    async def handle(self, message, cmd):
        user = cmd.author if cmd.argc == 0 else await cmd.get_user(cmd.text)
        if user is None:
            await cmd.answer('usuario no encontrado')
            return

        has_avatar = user.avatar_url != ''
        avatar_url = user.avatar_url if has_avatar else user.default_avatar_url

        title = 'Avatar de ' + user.display_name
        if not has_avatar:
            title += ' (no tiene xd)'

        await cmd.answer(embed=img_embed(avatar_url, title))
