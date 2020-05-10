from datetime import datetime
from discord import Embed

from bot import Command, categories
from bot.utils import format_date
from bot.regex import pat_channel
from bot.database import ServerConfig


class Sismos(Command):
    __version__ = '1.0.3'
    __author__ = 'makzk'
    cfg_channel_name = 'sismos_channel'
    api_url = 'https://api.mak.wtf/sismos'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'sismos'
        self.help = '$[sismos-help]'
        self.format = '$[sismos-format]'
        self.last_events = None
        self.last_update = None
        self.category = categories.INFORMATION
        self.schedule = (self.update_info, 20)

    async def handle(self, cmd):
        if self.last_events is None:
            await cmd.answer('$[sismos-not-loaded]')
            return

        if len(self.last_events) == 0:
            await cmd.answer('$[sismos-no-last]')
            return

        if cmd.argc > 0:
            if cmd.args[0] in cmd.lang.get_list('sismos-last-cmds'):
                await cmd.answer('$[sismos-last]', embed=Sismos.make_embed(self.last_events[0]))
                return
            elif cmd.owner and cmd.args[0] in cmd.lang.get_list('sismos-channel-cmds'):
                if cmd.argc < 2 or not pat_channel.match(cmd.args[1]):
                    await cmd.answer('$[format]: $[sismos-channel-format]')
                    return
                else:
                    cmd.config.set(Sismos.cfg_channel_name, cmd.args[1][2:-1])
                    await cmd.answer('$[sismos-channel-set]', locales={'channel': cmd.args[1]})
                    return

        sismos_list = ['- [{:.1f}º] [{}]({}) ({} km)'.format(
            f['magnitud'], f['referencia'], f['enlace'], f['profundidad']
        ) for f in self.last_events[:5]]

        embed = Embed(title='$[sismos-last-earthquakes]', description='\n'.join(sismos_list))
        embed.set_footer(text='$[sismos-last-update]')
        await cmd.answer(embed, locales={'update': format_date(self.last_update)})

    async def update_info(self):
        await self.bot.wait_until_ready()
        first = self.last_events is None
        if first:
            self.log.debug('Loading earthquakes information...')

        async with self.http.get(Sismos.api_url) as r:
            data = await r.json()

            if 'sismos' not in data:
                self.log.error('Wrong data received')
                return

            data = data['sismos']
            if not isinstance(data, list) or len(data) == 0:
                self.log.debug('No data retrieved')
                return

            if first:
                self.log.debug('Earthquakes information loaded. {} entries loaded.'.format(len(data)))

            if self.last_events is None or len(self.last_events) == 0 or data[0]['id'] != self.last_events[0]['id']:
                self.last_events = data
                self.last_update = datetime.now()

                if not first and len(self.last_events) > 0 and self.last_events[0]['magnitud'] >= 5:
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
                            content='$[sismos-alert-title]',
                            embed=Sismos.make_embed(self.last_events[0])
                        )

    @staticmethod
    def make_embed(data):
        embed = Embed(title='$[sismos-grade] {} {}'.format(data['magnitud'], data['escala']), url=data['enlace'])
        embed.description = data['referencia'] + '\n\n'
        embed.description += '$[sismos-date]: {}\n'.format(data['fecha'])
        embed.description += '$[sismos-location]: lat {latitud}º, long {longitud}º\n'.format(**data)
        embed.description += '$[sismos-depth]: {} km'.format(data['profundidad'])
        embed.set_thumbnail(url=data['mapa'])

        if data['preliminar']:
            embed.title += ' $[sismos-preliminary]'

        return embed
