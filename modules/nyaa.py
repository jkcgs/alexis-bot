import feedparser
from urllib.parse import urlencode
from discord import Embed
from bot import Command


class Nyaa(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'nyaa'
        self.help = '$[nyaa-help]'
        self.format = '$[nyaa-format]'
        self.default_enabled = False

    async def handle(self, cmd):
        if cmd.argc == 0:
            await cmd.answer('$[format]: $[nyaa-format]')
            return

        if cmd.args[0] == 'hs':
            query = 'horriblesubs 1080p ' + ' '.join(cmd.args[1:])
        else:
            query = cmd.text

        url = 'https://nyaa.si/?page=rss&c=0_0&f=0&' + urlencode({'q': query})
        self.log.debug('Loading %s ...', url)
        await cmd.typing()
        async with self.http.get(url) as r:
            p = feedparser.parse(await r.text())

            if len(p.entries) == 0:
                await cmd.answer('$[nyaa-no-results]')
                return

            embed = Embed(title='$[nyaa-title]')
            for entry in p.entries[:10]:
                details = '[[info]({link})] [[torrent]({torrent})] - S: {seeders} - L: {leechers} - {date}'
                details = details.format(
                    seeders=entry.nyaa_seeders,
                    leechers=entry.nyaa_leechers,
                    link=entry.guid,
                    torrent=entry.link,
                    date=entry.published
                )

                embed.add_field(name=entry.title, value=details)

            await cmd.answer(embed)
