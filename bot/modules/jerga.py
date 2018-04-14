from bot import Command
from urllib import parse as urlparse
from discord import Embed
from bs4 import BeautifulSoup


class Jerga(Command):
    url = 'http://diccionariochileno.cl/term/'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'jerga'
        self.aliases = ['dc']
        self.help = 'Obtiene una definición desde Diccionario Chileno'

    async def handle(self, cmd):
        text = cmd.text if cmd.text != '' else 'weon'
        text_url = urlparse.quote(text)

        try:
            async with self.http.get(Jerga.url + text_url) as r:
                content = await r.text()
                soup = BeautifulSoup(content, 'html.parser')
                div_definition = soup.find_all('div', class_='definition')
                resultado = ""
                if len(div_definition) == 0:
                    await cmd.answer('la palabra no existe en Diccionario Chileno')
                    return

                for i in range(len(div_definition)):
                    pgraph = div_definition[i].find_all('p')
                    resultado = resultado + "**" + str(i+1) + ".- " + str(pgraph[0]).strip('<p>\n\t\t').strip('\t</p>').replace('<br/>\r\n','\n') + "**\n*\"" + str(pgraph[1]).strip('<p>\n<i>').strip('</i>\n</p>').replace('<br/>\r\n','\n') + "\"*\n\n"
                embed = Embed()
                embed.title = text
                embed.url = Jerga.url + text_url
                embed.description = resultado

                await cmd.answer(embed=embed)
        except Exception as e:
            self.log.error(e)
            raise e
