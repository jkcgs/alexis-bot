import json
from datetime import datetime
from json import JSONDecodeError

from discord import Embed, Forbidden, HTTPException

from bot import Command, categories
from bot.lib.guild_configuration import GuildConfiguration


class Plebiscito2020CL(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'
    url = 'http://www.servelelecciones.cl/data/elecciones_constitucion/computo/global/19001.json'
    url2 = 'http://www.servelelecciones.cl/data/elecciones_convencion/computo/global/19001.json'
    cfg_name = 'plebiscito2020cl_data'
    cfg_name2 = 'plebiscito2020cl_data2'
    cfg_time = 'plebiscito2020cl_time'
    cfg_enabled = 'plebiscito2020cl_enabled'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'plebiscito'
        self.category = categories.INFORMATION
        self.schedule = (self.task, 30)
        self.config = GuildConfiguration.get_instance()
        self.default_config = {
            'plebiscito2020cl_channel': '766333643827445782',
        }

        self.data1 = None
        self.data2 = None

    async def handle(self, cmd):
        try:
            data = json.loads(self.config.get(self.cfg_name, '{}'))
            data2 = json.loads(self.config.get(self.cfg_name2, '{}'))
            if not data or not data2:
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

            the_embed = self.generate_embed(data, data2)
            await cmd.answer(embed=the_embed)
            return
        except Exception as e:
            self.log.exception(e)
            await cmd.answer('No se pudo cargar la información: {}'.format(str(e)))

    async def task(self):
        if self.config.get(self.cfg_enabled, '1') != '1':
            return

        try:
            cont = 0
            async with self.http.get(self.url) as r:
                self.data1 = await r.json()
                cont += 1
                if cont == 2:
                    await self.check()
                    return
            async with self.http.get(self.url2) as r:
                self.data2 = await r.json()
                cont += 1
                if cont == 2:
                    await self.check()
                    return
        except JSONDecodeError as e:
            self.log.exception(e)

    async def check(self):
        curr_data = json.loads(self.config.get(self.cfg_name, '{}'))
        curr_data2 = json.loads(self.config.get(self.cfg_name2, '{}'))

        if not curr_data or not curr_data2:
            await self.update(self.data1, self.data2)
            return

        resumen1 = {d['a']: d for d in self.data1['resumen']}
        resumen_curr1 = {d['a']: d for d in curr_data['resumen']}
        resumen2 = {d['a']: d for d in self.data2['resumen']}
        resumen_curr2 = {d['a']: d for d in curr_data2['resumen']}

        if resumen1['Válidamente Emitidos'] != resumen_curr1['Válidamente Emitidos']\
                or resumen2['Válidamente Emitidos'] != resumen_curr2['Válidamente Emitidos']:
            await self.update(self.data1, self.data2)
            return

    async def update(self, data, data2):
        dt = datetime.now()
        timestamp = dt.strftime("%d-%b-%Y %H:%M:%S")
        self.config.set(self.cfg_name, json.dumps(data))
        self.config.set(self.cfg_name2, json.dumps(data2))
        self.config.set(self.cfg_time, timestamp)

        chan = self.bot.get_channel(int(self.bot.config.get('plebiscito2020cl_channel')))
        embed = self.generate_embed(data, data2)

        try:
            msg = await self.bot.send_message(chan, embed=embed)
            if chan.is_news():
                await msg.publish()
                self.log.debug('Published to news channel {}'.format(chan.name))
        except (Forbidden, HTTPException):
            self.log.debug('Could not publish the message to the news channel {}'.format(chan.name))

    def generate_embed(self, data, data2):
        embed = Embed(title='Resultados actuales Plebiscito 2020')

        embed.description = '**__Constitución política__**\n'
        embed.description += 'Con {mesasEscrutadas} mesas escrutadas ({totalMesasPorcent})\n'.format(**data)
        for partido in (data['data']):
            embed.description += '**{nombre}**: {cant} ({porc})\n'.format(
                nombre=partido['a'], cant=partido['d'], porc=partido['c']
            )

        embed.description += '\n**__Tipo de órgano__**\n'
        embed.description += 'Con {mesasEscrutadas} mesas escrutadas ({totalMesasPorcent})\n'.format(**data2)
        for partido in (data2['data']):
            embed.description += '**{nombre}**: {cant} ({porc})\n'.format(
                nombre=partido['a'], cant=partido['d'], porc=partido['c']
            )

        ts = self.config.get(self.cfg_time)
        embed.description += '\nActualizado al: ' + ts
        return embed
