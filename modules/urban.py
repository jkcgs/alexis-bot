import re

from bot import Command, categories
from urllib import parse as urlparse
from discord import Embed

pat_subdef = re.compile('(\[([^\[\]]+)\])')
baseurl = 'http://api.urbandictionary.com/v0/define?term='


class Urban(Command):
    __author__ = 'makzk'
    __version__ = '1.0.1'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'urban'
        self.aliases = ['ub']
        self.help = '$[urban-help]'
        self.format = '$[urban-format]'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        text = cmd.text if cmd.text != '' else cmd.lang.get('urban-default-word')
        text = urlparse.quote(text)

        try:
            self.log.debug('Loading %s ...', (baseurl + text))

            await cmd.typing()
            async with self.http.get(baseurl + text) as urlresp:
                data = await urlresp.json()
                if 'list' not in data or len(data['list']) == 0:
                    await cmd.answer('$[urban-error-fetch]')
                    return

                result = data['list'][0]
                result['definition'] = Urban.reformat(result['definition'])
                result['example'] = Urban.reformat(result['example'])

                embed = Embed()
                embed.title = result['word']
                embed.url = result['permalink']
                desc = '$[urban-cont-by] {}\n\n$[urban-cont-definition]\n{}\n\n$[urban-cont-example]\n{}'
                embed.description = desc.format(result['author'], result['definition'], result['example'])
                embed.set_footer(text='👍 {}  👎 {}'.format(result['thumbs_up'], result['thumbs_down']))

                await cmd.answer(embed=embed)
                return
        except Exception as e:
            self.log.error(e)
            raise e

    @staticmethod
    def reformat(cont):
        for (f, term) in pat_subdef.findall(cont):
            link = 'http://{}.urbanup.com/'.format(re.sub(r'[^a-z\-]', '', term.lower().replace(' ', '-')))
            cont = cont.replace(f, '[{}]({})'.format(term, link))

        return cont
