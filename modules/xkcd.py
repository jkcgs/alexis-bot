from bot import Command, categories
from discord import Embed
import random

baseurl = 'https://xkcd.com/{}/info.0.json'


class XKCD(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'xkcd'
        self.help = '$[xkcd-help]'
        self.format = '$[xkcd-format]'
        self.category = categories.FUN
        self.xkcd_current = None
        self.xkcd_comic = []

    async def handle(self, cmd):
        if self.xkcd_current is None:
            return

        arg = cmd.text
        if arg.isdigit():
            if 0 < int(arg) <= self.xkcd_current['num']:
                await cmd.typing()
                async with self.http.get(baseurl.format(arg)) as r:
                    self.xkcd_comic = await r.json()
            else:
                await cmd.answer('$[xkcd-err-outofbounds]')
                return
        elif arg == 'random':
            xkcd_random = random.randint(1, self.xkcd_current['num'])
            async with self.http.get(baseurl.format(xkcd_random)) as r:
                self.xkcd_comic = await r.json()
        elif len(arg) == 0 or arg == 'current':
            await cmd.typing()
            self.xkcd_comic = self.xkcd_current
        else:
            await cmd.answer('$[format]: $[xkcd-format]')
            return

        embed = Embed(color=0x929591)
        embed.title = self.xkcd_comic['safe_title']
        embed.set_image(url=self.xkcd_comic['img'])
        embed.description = self.xkcd_comic['alt']
        embed.set_footer(text='xkcd n° {}'.format(self.xkcd_comic['num']))
        await cmd.answer(embed=embed)

    async def on_ready(self):
        self.log.debug('Loading last xkcd comic...')
        async with self.http.get('https://xkcd.com/info.0.json') as r:
            self.xkcd_current = await r.json()
            self.log.debug('Last xkcd comic loaded')
