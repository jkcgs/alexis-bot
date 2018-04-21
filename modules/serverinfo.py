from discord import Embed

from bot import Command
from bot.utils import format_date


class ServerInfo(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'serverinfo'
        self.aliases = ['server']

    async def handle(self, cmd):
        if cmd.argc == 0:
            if cmd.is_pm:
                await cmd.answer('formato: $CMD <(nombre|id) de servidor>')
                return
            else:
                cmd.args.append(cmd.server.id)

        server = self.bot.get_server(cmd.args[0])
        if server is None:
            for s in self.bot.servers:
                if s.name == cmd.args[0]:
                    server = s
                    break

        if server is None:
            await cmd.answer('servidor no encontrado')
            return

        embed = Embed()
        embed.add_field(name='Nombre', value=server.name)
        embed.add_field(name='ID', value=server.id)
        embed.add_field(name='Miembros', value=str(server.member_count))
        embed.add_field(name='Bots', value=str(len([m for m in server.members if m.bot])))
        embed.add_field(name='Emojis', value=str(len(server.emojis)))
        embed.add_field(name='Dueño/a', value=str(server.owner))
        embed.add_field(name='Región de voz', value=server.region)
        embed.add_field(name='Creado', value=format_date(server.created_at))
        embed.set_thumbnail(url=server.icon_url)

        other = []
        if server.large:
            other.append('servidor grande')
        if 'VIP_REGIONS' in server.features:
            other.append('regiones VIP de voz')
        if 'VANITY_URL' in server.features:
            other.append('vanity URL (invite corto)')
        if 'INVITE_SPLASH' in server.features:
            other.append('imagen de fondo de invite')
        if server.mfa_level > 0:
            other.append('requiere autentificación en dos pasos')

        if len(other) > 0:
            embed.set_footer(text='Otros: {}'.format(', '.join(other)))

        await cmd.answer('información de {}'.format(server.id), embed=embed)
