from urllib.parse import urlencode
from xml.etree.ElementTree import fromstring as parsexml
from random import choice

from bot import Command
from bot.utils import img_embed


class Gelbooru(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'gelbooru'
        self.help = 'Busca imágenes en el imageboard gelbooru (animé y hentai)'
        self.nsfw_only = True

    async def handle(self, cmd):
        await cmd.typing()

        query = {
            'page': 'dapi',
            's': 'post',
            'q': 'index',
            'tags': '*' if cmd.argc < 1 else cmd.text
        }

        q_url = 'https://gelbooru.com/index.php?' + urlencode(query)
        async with self.http.get(q_url) as r:
            posts = parsexml(await r.text()).findall('post')
            if len(posts) == 0:
                await cmd.answer('sin resultados :c')
                return

            post = choice(posts)
            await cmd.answer(img_embed(post.get('file_url')))
