from urllib.parse import urlencode
from xml.etree.ElementTree import fromstring as parsexml
from random import choice

from bot import Command
from bot.utils import img_embed


class Rule34(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'rule34'
        self.aliases = ['r34']
        self.help = 'Busca imágenes en rule34.xxx'
        self.nsfw_only = True

    async def handle(self, cmd):
        await cmd.typing()

        query = {
            'page': 'dapi',
            's': 'post',
            'q': 'index',
            'tags': '*' if cmd.argc < 1 else cmd.text
        }

        q_url = 'https://rule34.xxx/index.php?' + urlencode(query)
        async with self.http.get(q_url) as r:
            posts = parsexml(await r.text()).findall('post')
            if len(posts) == 0:
                await cmd.answer('sin resultados :c')
                return

            post = choice(posts)
            await cmd.answer(img_embed(post.get('file_url')))
