import asyncio
from datetime import datetime

from discord import Embed

from bot import Command
from bot.utils import pat_channel, format_date
from bot.libs.configuration import ServerConfig


class Sismos(Command):
    __version__ = '1.0.1'
    __author__ = 'makzk'
    cfg_channel_name = 'sismos_channel'
    api_url = 'https://api.cadcc.cl/sismo/'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'sismos'
        self.help = 'Muestra alertas sobre sismos en Chile y dispone de un comando para listar los últimos sismos'
        self.last_events = None
        self.last_update = None

    async def handle(self, cmd):
        if self.last_events is None:
            await cmd.answer('la información no ha sido cargada')
            return

        if len(self.last_events) == 0:
            await cmd.answer('no se obtuvieron registros de eventos sísmicos')
            return

        if cmd.argc > 0:
            if cmd.args[0] in ['ultimo', 'último']:
                await cmd.answer('datos del último sismo', embed=Sismos.make_embed(self.last_events[0]))
                return
            elif cmd.args[0] == 'canal' and cmd.owner:
                if cmd.argc < 2 or not pat_channel.match(cmd.args[1]):
                    await cmd.answer('formato: $CMD canal [canal]')
                    return
                else:
                    cmd.config.set(Sismos.cfg_channel_name, cmd.args[1][2:-1])
                    await cmd.answer('el canal de alertas ahora es {}'.format(cmd.args[1]))
                    return

        sismos_list = ['- [{:.1f}º] [{}]({}) ({} km)'.format(
            f['magnitudes'][0]['magnitud'], f['geoReferencia'], f['enlace'], f['profundidad']
        ) for f in self.last_events[:5]]

        embed = Embed(title='Últimos sismos', description='\n'.join(sismos_list))
        embed.set_footer(text='Última actualización: {}'.format(format_date(self.last_update)))
        await cmd.answer(embed)

    async def task(self):
        await self.bot.wait_until_ready()
        first = self.last_events is None
        if first:
            self.log.debug('Recuperando información de sismos por primera vez...')

        async with self.http.get(Sismos.api_url) as r:
            data = await r.json()
            if first:
                self.log.debug('Información de sismos recuperada. Se cargaron {} registros.'.format(len(data)))

            if self.last_events is None or len(self.last_events) == 0 or data[0]['id'] != self.last_events[0]['id']:

                self.last_events = data
                self.last_update = datetime.now()

                if not first and len(self.last_events) > 0 and len(self.last_events[0]['magnitudes']) > 0 \
                        and self.last_events[0]['magnitudes'][0]['magnitud'] >= 5:

                    query = ServerConfig.select().where(
                        ServerConfig.name == Sismos.cfg_channel_name, ServerConfig.value != ''
                    )

                    for server_config in query:
                        sv = self.bot.get_server(server_config.serverid)
                        if sv is None:
                            ServerConfig.delete_instance(server_config)
                            continue

                        chan = sv.get_channel(server_config.value)
                        if chan is None:
                            continue

                        await self.bot.send_message(
                            destination=chan,
                            content='Alerta de sismo!',
                            embed=Sismos.make_embed(self.last_events[0])
                        )

        if not self.bot.is_closed:
            await asyncio.sleep(20)
            self.bot.loop.create_task(self.task())

    @staticmethod
    def make_embed(data):
        mag = data['magnitudes'][0]
        embed = Embed(title='Sismo de grado {} {}'.format(mag['magnitud'], mag['medida']))
        embed.description = data['geoReferencia'] + '\n\n'
        embed.description += '**Fecha**: {}\n'.format(data['fechaLocal'])
        embed.description += '**Ubicación**: lat {latitud}º, long {longitud}º\n'.format(**data)
        embed.description += '**Profundidad**: {} km'.format(data['profundidad'])
        embed.url = data['enlace']

        if data['preliminar']:
            embed.title += ' (preliminar)'

        return embed
