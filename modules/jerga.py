from bot import Command, categories
from urllib import parse as urlparse
from discord import Embed
from bs4 import BeautifulSoup

baseurl = 'http://diccionariochileno.cl/term/'


class Jerga(Command):
    __author__ = 'HenrydelMal'
    __version__ = '1.0.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'jerga'
        self.aliases = ['dc']
        self.help = '$[jerga-help]'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        text = cmd.text if cmd.text != '' else 'weon'
        text_url = urlparse.quote(text)

        try:
            self.log.debug('Loading %s...', (baseurl + text_url))

            await cmd.typing()
            async with self.http.get(baseurl + text_url) as r:
                content = await r.text()
                soup = BeautifulSoup(content, 'html.parser')
                div_definition = soup.find_all('div', class_='definition')
                if len(div_definition) == 0:
                    await cmd.answer('$[jerga-not-found]')
                    return

                resultados = []
                for i in range(len(div_definition)):
                    pgraph = div_definition[i].find_all('p')
                    definition = pgraph[0].text.strip()
                    example = pgraph[1].text.strip()
                    resultados.append('**{}.- {}**\n*\"{}\"*'.format(i+1, definition, example))

                embed = Embed()
                embed.title = text
                embed.url = baseurl + text_url
                embed.description = '\n\n'.join(resultados)
                embed.set_footer(text='$[jerga-footer]')

                await cmd.answer(embed=embed, locales={
                    'site': 'Diccionario Chileno - https://www.diccionariochileno.cl/'
                })
        except Exception as e:
            self.log.error(e)
            raise e
