import json
from datetime import datetime
from json import JSONDecodeError

from discord import Embed, Forbidden, HTTPException

from bot import Command, categories
from bot.lib.guild_configuration import GuildConfiguration


class Plebiscito2020CL(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'
    url = 'http://localhost:5000/data.json'  # 'http://www.servelelecciones.cl/data/elecciones_constitucion/computo/global/19001.json'
    cfg_name = 'plebiscito2020cl_data'
    cfg_time = 'plebiscito2020cl_time'
    cfg_enabled = 'plebiscito2020cl_enabled'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'plebiscito'
        self.category = categories.INFORMATION
        self.schedule = (self.task, 5)
        self.config = GuildConfiguration.get_instance()
        self.default_config = {
            'plebiscito2020cl_channel': '351573615273312257',
        }

    async def handle(self, cmd):
        try:
            data = json.loads(self.config.get(self.cfg_name, '{}'))
            if not data:
                await cmd.answer('La información aún no está disponible.')
                return

            if cmd.argc > 0 and cmd.bot_owner:
                if cmd.args[0] == 'reload':
                    await cmd.answer('running task')
                    await self.task()
                elif cmd.args[0] == 'disable':
                    self.config.set(self.cfg_enabled, '0')
                    await cmd.answer('disabled')
                elif cmd.args[0] == 'enable':
                    self.config.set(self.cfg_enabled, '1')
                    await cmd.answer('enabled')
                else:
                    await cmd.answer('wtf')

            the_embed = self.generate_embed(data)
            await cmd.answer(embed=the_embed)
            return
        except Exception as e:
            self.log.error(e)
            await cmd.answer('No se pudo cargar la información: {}'.format(str(e)))

    async def task(self):
        if self.config.get(self.cfg_name, '1') != '1':
            return

        curr_data = json.loads(self.config.get(self.cfg_name, '{}'))
        try:
            async with self.http.get(self.url) as r:
                data = await r.json()
                if not curr_data:
                    await self.update(data)
                    return

                resumen = {d['a']: d for k, d in data['resumen']}
                resumen_curr = {d['a']: d for k, d in curr_data['resumen']}

                if resumen['Válidamente Emitidos'] != resumen_curr['Válidamente Emitidos']:
                    do_publish = True  # resumen['Válidamente Emitidos'] != '0'
                    await self.update(data, do_publish)
                    return

        except JSONDecodeError as e:
            self.log.exception(e)

    async def update(self, data, publish=False):
        dt = datetime.now()
        timestamp = dt.strftime("%d-%b-%Y %H:%M:%S")
        self.config.set(self.cfg_name, json.dumps(data))
        self.config.set(self.cfg_time, timestamp)

        if publish:
            chan = self.bot.get_channel(int(self.bot.config.get('plebiscito2020cl_channel')))
            embed = self.generate_embed(data)

            try:
                msg = await self.bot.send_message(chan, embed=embed)
                if chan.is_news():
                    await msg.publish()
                    self.log.debug('Published to news channel {}'.format(chan.name))
            except (Forbidden, HTTPException):
                self.log.debug('Could not publish the message to the news channel {}'.format(chan.name))

    @classmethod
    def generate_embed(cls, data):
        embed = Embed(title='Resultados actuales Plebiscito 2020')
        for partido in data['data']:
            embed.add_field(name=partido['a'], value='{d} ({c} votos)'.format(**partido))
        return embed
