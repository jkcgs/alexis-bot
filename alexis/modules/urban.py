from alexis import Command
from urllib import parse as urlparse
from discord import Embed


class Urban(Command):
    url = 'http://api.urbandictionary.com/v0/define?term='

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'urban'
        self.aliases = ['ub']
        self.help = 'Obtiene una definición desde UrbanDictionary'

    async def handle(self, message, cmd):
        text = cmd.text if cmd.text != '' else 'weon'
        text = urlparse.quote(text)

        try:
            async with self.http.get(Urban.url + text) as urlresp:
                data = await urlresp.json()
                if 'result_type' not in data or data['result_type'] != 'exact':
                    await cmd.answer('no se pudo obtener la respuesta de UB')
                    return

                result = data['list'][0]
                embed = Embed()
                embed.title = result['word']
                embed.url = result['permalink']
                desc = 'por {}\n\n**Definición**\n{}\n\n**Ejemplo**\n{}\n\n**Tags**\n{}'
                embed.description = desc.format(result['author'], result['definition'], result['example'],
                                                ', '.join(set(data['tags'])))
                embed.set_footer(text='👍 {} | 👎 {}'.format(result['thumbs_up'], result['thumbs_down']))

                await cmd.answer(embed=embed)
                return
        except Exception as e:
            self.log.error(e)
            raise e
