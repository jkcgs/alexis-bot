from modules.base.command import Command
from discord import Embed


class UserCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'user'
        self.help = 'Entrega información sobre un usuario'
        self.allow_pm = False

    async def handle(self, message, cmd):
        if len(cmd.args) > 1 and len(message.mentions) == 1:
            user = message.mentions[0]
        else:
            user = cmd.author

        embed = Embed()
        embed.add_field(name='Nombre', value=str(user))
        embed.add_field(name='Nick', value=user.nick if user.nick is not None else 'Ninguno :c')
        embed.add_field(name='Usuario creado el', value=UserCmd.parsedate(user.created_at))
        embed.add_field(name='Se unió al server el', value=UserCmd.parsedate(user.joined_at))
        if user.avatar_url != '':
            embed.set_thumbnail(url=user.avatar_url)

        await cmd.answer('Acerca de **{}**'.format(user.id), embed=embed)

    @staticmethod
    def parsedate(the_date):
        return the_date.strftime('%d de %B de %Y, %H:%M:%S')
