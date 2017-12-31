from alexis import Command
from discord import Embed
import random
import requests


class xkcd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'xkcd'
        self.help = 'Muestra un comic xkcd.'
        self.xkcd_current = requests.get('https://xkcd.com/info.0.json').json()
        self.xkcd_comic = []

    async def handle(self, message, cmd):
        # TODO: Usar aiohttp
        arg = cmd.text
        if arg.isdigit() and 0 < int(arg) < self.xkcd_current['num']:
            self.xkcd_comic = requests.get('https://xkcd.com/{}/info.0.json'.format(arg)).json()
        elif arg == 'random':
            xkcd_random = random.randint(1, self.xkcd_current['num'])
            self.xkcd_comic = requests.get('https://xkcd.com/{}/info.0.json'.format(xkcd_random)).json()
        elif len(arg) == 0 or arg == 'current':
            self.xkcd_comic = self.xkcd_current
        else:
            return
        embed = Embed(color=0x929591)
        embed.title = self.xkcd_comic['safe_title']
        embed.set_image(url=self.xkcd_comic['img'])
        embed.description = self.xkcd_comic['alt']
        embed.set_footer(text='xkcd n° {}'.format(self.xkcd_comic['num']))
        await cmd.answer(embed=embed)
