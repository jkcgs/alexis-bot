from datetime import datetime

from discord import Embed

from bot import Command
from bot.utils import format_date, deltatime_to_str


class ServerInfo(Command):
    __version__ = '1.1.0'
    __author__ = 'makzk'

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

        created_diff = deltatime_to_str(datetime.now() - server.created_at)
        bot_count = len([m for m in server.members if m.bot])
        bot_word = ['bots', 'bot'][bool(bot_count == 0)]
        emoji_word = ['emojis', 'emoji'][bool(len(server.emojis) == 0)]

        embed = Embed(title='Información del servidor')
        cont = '**Nombre**: {}\n'.format(server.name)
        cont += '**Dueño**: {}\n'.format(server.owner)
        cont += '**Creado**: {} \n(*hace {}*)\n\n'.format(format_date(server.created_at), created_diff)
        cont += 'Tiene **{} miembros**, *{} {}* y *{} {}*.\n'.format(
            server.member_count, bot_count, bot_word, len(server.emojis), emoji_word
        )
        cont += '**Región de voz**: {}\n'.format(server.region)
        cont += '**ID**: {}'.format(server.id)

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
            cont += '\n\n**Otros**: {}'.format(', '.join(other))

        embed.set_thumbnail(url=server.icon_url)
        embed.description = cont
        embed.set_footer(text='Solicitado por {}'.format(cmd.author_name))

        await cmd.answer(embed, withname=False)
