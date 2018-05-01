import asyncio
from datetime import datetime

from discord import Embed

from bot import Command


class Horoscopo(Command):
    __version__ = '1.0.2'
    __author__ = 'makzk'
    api_url = 'https://api.cadcc.cl/tyaas/'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'horoscopo'
        self.help = 'Muestra el horóscopo para un determinado signo.'
        self.horoscopo = None
        self.update_step = 0

    async def handle(self, cmd):
        if self.horoscopo is None:
            await cmd.answer('no hay información del horóscopo disponible')
            return

        if cmd.argc == 0:
            await cmd.answer('formato: $CMD <signo>')
            return

        if cmd.args[0] in ['update', 'reload'] and cmd.bot_owner:
            await cmd.typing()
            await self.update()
            await cmd.answer('datos cargados')
            return

        signo = self.get_sign(cmd.args[0])
        if signo is None:
            await cmd.answer('signo incorrecto')
            return

        await cmd.answer(self.make_embed(signo))

    async def on_ready(self):
        await self.update()

    def get_sign(self, name):
        if isinstance(name, dict):
            return name
        elif name in self.horoscopo['horoscopo']:
            return self.horoscopo['horoscopo'][name]
        else:
            for sign in self.horoscopo['horoscopo'].values():
                if 'nombre' in sign and sign['nombre'].lower() == name.lower():
                    return sign
            return None

    async def task(self):
        """
        Los datos se actualizarán en el minuto 0, 1 y 2 de cada hora
        :return:
        """
        await self.bot.wait_until_ready()
        now = datetime.now()
        if now.minute == self.update_step and 0 <= self.update_step < 3:
            self.log.debug('Cargando información de horóscopo...')
            await self.update()
            self.log.debug('Información de horóscopo cargada')

            self.update_step += 1
            if self.update_step > 2:
                self.update_step = 0

        if not self.bot.is_closed:
            await asyncio.sleep(30)
            self.bot.loop.create_task(self.task())

    def make_embed(self, signo):
        signo = self.get_sign(signo)
        embed = Embed(title='Horóscopo - {}'.format(self.horoscopo['titulo']))
        embed.description = '**{}** (*{}*)\n\n'.format(signo['nombre'], signo['fechaSigno'])
        embed.description += '**Amor**: {}\n'.format(signo['amor'])
        embed.description += '**Salud**: {}\n'.format(signo['salud'])
        embed.description += '**Dinero**: {}\n'.format(signo['dinero'])
        embed.description += '**Color**: {} **Número**: {}\n'.format(signo['color'], signo['numero'])
        embed.set_footer(text='Horóscopo de la Tía Yoly (TYaaS)')
        return embed

    async def update(self):
        self.log.debug('Cargando datos del horóscopo...')
        async with self.http.get(Horoscopo.api_url) as r:
            self.horoscopo = await r.json()
            self.log.debug('Datos del horóscopo cargados.')
