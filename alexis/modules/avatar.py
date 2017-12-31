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

        if user and user.avatar_url != '':
            self.log.debug('enviando avatar: ' + user.avatar_url)
            title = 'Avatar de ' + user.display_name
            await cmd.answer(embed=img_embed(user.avatar_url, title))
        else:
            await cmd.answer('ávatar no disponible uwu')
