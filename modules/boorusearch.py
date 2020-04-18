from collections import ChainMap
from random import choice
from xml.etree.ElementTree import fromstring as parsexml

from bot import Command, categories
from bot.utils import img_embed

search_types = {
    'e621': {
        'url': 'https://e621.net/posts.json?limit=30&tags={}',
        'name': 'e621.net'
    },
    'gelbooru': {
        'url': 'https://gelbooru.com/index.php?page=dapi&s=post&q=index&tags={}',
        'aliases': ['gelb', 'gb']
    },
    'rule34': {
        'url': 'https://rule34.xxx/index.php?page=dapi&s=post&q=index&tags={}',
        'aliases': ['r34'],
        'format': 'xml'
    },
    'danbooru': {
        'url': 'https://danbooru.donmai.us/posts.json?limit=30&tags={}',
        'aliases': ['danb']
    },
    'konachan': {
        'url': 'https://konachan.net/post.json?limit=30&tags={}',
        'aliases': ['kona'],
        'name': 'konachan.net (sfw)'
    },
    'konachan18': {
        'url': 'https://konachan.com/post.json?limit=30&tags={}',
        'aliases': ['kona18'],
        'name': 'konachan.com (nsfw)'
    },
    'hypnohub': {
        'url': 'https://hypnohub.net/post/index.json?limit=30&tags={}',
        'aliases': ['hypno'],
        'image_format': 'https:{}'
    },
    'xbooru': {
        'url': 'https://xbooru.com/index.php?page=dapi&s=post&q=index&tags={}',
        'format': 'xml'
    },
    'realbooru': {
        'url': 'https://realbooru.com/index.php?page=dapi&s=post&q=index&tags={}',
        'format': 'xml'
    },
    'furrybooru': {
        'url': 'https://furry.booru.org/index.php?page=dapi&s=post&q=index&tags={}',
        'format': 'xml'
    }
}

aliases_map = ChainMap(*[{j: x for j in v.get('aliases', [])} for x, v in search_types.items()])
aliases = [*aliases_map] + [*search_types]


class BooruSearch(Command):
    __author__ = 'makzk'
    __version__ = '1.0.1'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'booru'
        self.aliases = aliases
        self.help = '$[booru-help]'
        self.format = '$[booru-format]'
        self.nsfw_only = True
        self.category = categories.IMAGES

    async def handle(self, cmd):
        if cmd.cmdname in self.name:
            if cmd.argc > 0:
                if cmd.args[0] in aliases:
                    search_type = cmd.args[0]
                    search_text = ' '.join(cmd.args[1:])
                elif cmd.args[0] == 'list':
                    await cmd.answer('$[booru-list]', locales={'types': ', '.join([*search_types])})
                    return
                else:
                    search_type = choice([*search_types])
                    search_text = cmd.text
            else:
                search_type = choice([*search_types])
                search_text = cmd.text
        else:
            search_type = cmd.cmdname
            search_text = cmd.text

        if search_type in aliases_map:
            search_type = aliases_map[search_type]

        if search_text == '':
            search_text = search_types[search_type].get('default_search', '*')

        search_url = search_types[search_type]['url'].format(search_text)

        self.log.debug('Loading %s', search_url)
        await cmd.typing()
        async with self.http.get(search_url) as r:
            if search_types[search_type].get('format', 'json') == 'xml':
                posts = parsexml(await r.text()).findall('post')
            else:
                posts = await r.json()
                if search_type == 'e621':
                    posts = filter(lambda x: x['file']['ext'] != 'webm', posts['posts'])

            if len(posts) == 0:
                await cmd.answer('$[booru-no-results]')
                return

            post = choice(posts)
            image_url = post['file']['url'] if search_type == 'e621' else post.get('file_url')

            if 'image_format' in search_types[search_type]:
                image_url = search_types[search_type]['image_format'].format(post.get('file_url'))

            await cmd.answer(
                img_embed(image_url, footer='$[booru-results-footer]'),
                locales={'site': search_types[search_type].get('name', search_type)}
            )
