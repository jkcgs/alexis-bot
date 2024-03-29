import json
from datetime import datetime
from json import JSONDecodeError

from discord import Embed, Forbidden, HTTPException

from bot import Command, categories
from bot.lib.guild_configuration import GuildConfiguration


def nf(val):
    return '.'.join([str(val)[::-1][i:i + 3] for i in range(0, len(str(val)), 3)])[::-1].replace('-.', '-')


def embed(data):
    the_embed = Embed(title='Estado del Coronavirus COVID-19 en Chile', description=data['message_md'])
    the_embed.set_footer(text='Información actualizada al: {}'.format(data['ts_capturado']))
    return the_embed


class Covid19CL(Command):
    __author__ = 'makzk'
    __version__ = '3.0.1'
    url = 'https://api.mak.wtf/covid'
    _last_day = datetime.now().day

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'covid19cl'
        self.aliases = ['covid', 'coronavirus']
        self.category = categories.INFORMATION
        self.config = GuildConfiguration.get_instance()

        self.schedule = (self.task, 30)

    async def handle(self, cmd):
        try:
            data = json.loads(self.config.get('covid19cl_data', '{}'))
            if not data:
                await cmd.answer('La información aún no está disponible.')
                return

            if cmd.argc > 0 and cmd.bot_owner and cmd.args[0] == 'reload':
                await cmd.answer('running task')
                await self.task(True)

            the_embed = embed(data)
            await cmd.answer(embed=the_embed)
            return
        except Exception as e:
            self.log.error(e)
            await cmd.answer('No se pudo cargar la información: {}'.format(str(e)))

    async def publish(self, data):
        the_embed = embed(data)

        self.log.debug('Publishing Covid19 data to Discord...')
        chan = self.bot.get_channel(int(self.bot.config.get('covid19cl_discord_channel')))
        try:
            msg = await self.bot.send_message(chan, embed=the_embed)
            if chan.is_news():
                await msg.publish()
                self.log.debug('Published to news channel {}'.format(chan.name))
        except (Forbidden, HTTPException):
            self.log.debug('Could not publish the message to the news channel {}'.format(chan.name))

    async def task(self, force=False):
        now = datetime.now()
        curr_data = self.config.get('covid19cl_data', '{}')
        try:
            curr_data = json.loads(curr_data)
        except JSONDecodeError:
            self.log.debug('Se encontraron datos erróneos en la caché de datos.')

        if force or not curr_data or (self._last_day != now.day and now.hour >= 10):
            try:
                self.log.debug('Loading Covid19 data...')
                async with self.http.get(self.url) as r:
                    if r.status != 200:
                        raise RuntimeError('status ' + str(r.status))
                    data = await r.json()
                    if 'ts_capturado' not in data:
                        raise RuntimeError('invalid data')

                    if curr_data.get('fecha', '') != data['fecha'] and data['listo']:
                        self.config.set('covid19cl_data', json.dumps(data))
                        self._last_day = now.day
                        if curr_data:
                            self.log.debug('New data found! Publishing Covid19 data...')
                            await self.publish(data)
                        else:
                            self.log.debug('New data found! Ignoring publishing because of fresh start.')
                    else:
                        self.log.debug('No new data found')
            except (JSONDecodeError, RuntimeError) as e:
                self.log.warning('No se pudo obtener la información ({}).'.format(e))
