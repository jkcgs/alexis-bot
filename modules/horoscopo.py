import asyncio

from discord import Embed

from bot import Command


class Horoscopo(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'
    api_url = 'https://api.cadcc.cl/tyaas/'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'horoscopo'
        self.help = 'Muestra el horóscopo para un determinado signo'
        self.horoscopo = None

    async def handle(self, cmd):
        if self.horoscopo is None:
            await cmd.answer('no hay información del horóscopo disponible')
            return

        if cmd.argc == 0:
            await cmd.answer('formato: $CMD <signo>')
            return

        signo = cmd.args[0].lower()
        if signo not in self.horoscopo['horoscopo']:
            await cmd.answer('signo incorrecto')
            return

        await cmd.answer(self.make_embed(signo))

    def make_embed(self, nombre_signo):
        signo = self.horoscopo['horoscopo'][nombre_signo]
        embed = Embed(title='Horóscopo - {}'.format(self.horoscopo['titulo']))
        embed.description = '**{}** (*{}*)\n\n'.format(signo['nombre'], signo['fechaSigno'])
        embed.description += '**Amor**: {}\n'.format(signo['amor'])
        embed.description += '**Salud**: {}\n'.format(signo['salud'])
        embed.description += '**Dinero**: {}\n'.format(signo['dinero'])
        embed.description += '**Color**: {} **Número**: {}\n'.format(signo['color'], signo['numero'])
        embed.set_footer(text='Horóscopo de la Tía Yoly (TYaaS)')
        return embed

    async def task(self):
        await self.bot.wait_until_ready()
        self.log.debug('Cargando información de horóscopo...')
        async with self.http.get(Horoscopo.api_url) as r:
            self.horoscopo = await r.json()
            self.log.debug('Información de horóscopo cargada')

        if not self.bot.is_closed:
            await asyncio.sleep(14400)  # 4h así como por ser
            self.bot.loop.create_task(self.task())
