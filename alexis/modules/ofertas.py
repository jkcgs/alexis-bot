import asyncio

import math

import aiohttp

from alexis import Command
from bs4 import BeautifulSoup
from discord import Embed


class Ofertas(Command):
    baseurl = 'http://45.55.240.116/'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ofertas'
        self.aliases = ['papa']
        self.help = 'xd'

        self.lastfile = None
        self.data = []

    async def handle(self, cmd):
        if self.lastfile is None:
            await cmd.answer('data not available')
            return

        # 0 nombre, 1 preciooferta, 2 precioreal, 3 desc, 4 tienda
        parsed = [Ofertas.filter(p) for p in self.data[:20]]
        embed = Embed(description='\n'.join(parsed))
        embed.set_footer(text=self.lastfile.split('/')[-1].split('.')[0])
        await cmd.answer(embed)

    async def last(self):
        async with self.http.get(Ofertas.baseurl + 'ofertas.jsp') as r:
            dom = BeautifulSoup(await r.text(), 'html.parser')
            links = [Ofertas.baseurl + a.get('href') for a in dom.find_all('a') if a.text.endswith('csv')]
            if len(links) == 0:
                return None

            links.sort()
            return links[-1]

    async def get_data(self, link):
        async with self.http.get(link) as r:
            return [x.split(',') for x in (await r.text()).split('\n') if x.strip() != '']

    async def task(self):
        try:
            await self.bot.wait_until_ready()
            file = await self.last()
            if file == self.lastfile:
                return

            self.lastfile = file
            self.data = await self.get_data(file)
            await asyncio.sleep(60)

            if not self.bot.is_closed:
                self.bot.loop.create_task(self.task())
        except Exception as e:
            self.log.debug('No fue posible obtener datos de las ofertas: %s', str(e))

    @staticmethod
    def filter(line):
        if line[0].startswith('-' + line[3]):
            line[0] = line[0][2+len(line[3]):]

        dif = math.ceil((1 - int(line[1][:-2]) / int(line[2][:-2])) * 100)
        if line[0].startswith('-' + str(dif) + '%'):
            line[0] = line[0][2+len(str(dif)):]

        return '[{} (${} ~~${}~~)] {} ({})'.format(line[3], line[1][:-2], line[2][:-2], line[0].strip(), line[4])
