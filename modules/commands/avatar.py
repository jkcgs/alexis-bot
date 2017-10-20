from modules.base.command import Command


class Avatar(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'avatar'
        self.help = 'Envia el ávatar del usuario que envió el comando o del usuario mencionado'

    async def handle(self, message, cmd):
        if len(cmd.args) > 0:
            if len(message.mentions) == 0:
                await cmd.answer('Formato: !avatar [@mención]')
                return
            else:
                user = message.mentions[0]
        else:
            user = cmd.author

        if user and user.avatar_url != '':
            self.log.debug('enviando avatar: ' + user.avatar_url)
            title = 'Ávatar de ' + user.display_name
            await cmd.answer(embed=Command.img_embed(user.avatar_url, title))
        else:
            await cmd.answer('Ávatar no disponible uwu')
