import random

from bot import Command, utils, categories

url_settings = {
    'cat': ['http://aws.random.cat/meow', ['gato', 'gatito', 'neko'], 'file'],
    'dog': ['https://dog.ceo/api/breeds/image/random', ['perro', 'perrito', 'doggo'], 'message'],
    'shiba': ['http://shibe.online/api/shibes', ['shibe', 'shibainu'], 0],
    'fox': ['https://randomfox.ca/floof/', ['foxxo'], 'image'],
    'duck': ['https://random-d.uk/api/random', ['pato'], 'url'],
    'bunny': ['https://api.bunnies.io/v2/loop/random/?media=gif', ['conejo'], 'media.gif'],
    'owl': ['http://pics.floofybot.moe/owl', ['buho'], 'image'],
}

alias_map = {k: v[1] + [k] for k, v in url_settings.items()}
aliases = [item for x in alias_map.values() for item in x]


class RandomAnimal(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'animal'
        self.format = '$[animal-usage]'
        self.aliases = aliases
        self.category = categories.IMAGES

    async def handle(self, cmd):
        if cmd.argc < 1 and cmd.cmdname in aliases:
            cmd.args = [cmd.cmdname]
            cmd.argc = 1

        if cmd.argc > 0 and cmd.args[0] == 'help':
            return await cmd.send_usage('$[animal-usage-help]', locales={'types': ', '.join(list(url_settings.keys()))})

        if cmd.argc < 1:
            atype = random.choice(list(url_settings.keys()))
        elif cmd.args[0] in aliases:
            atype = list(url_settings.keys())[0]
            for k, v in alias_map.items():
                if cmd.args[0] in v:
                    atype = k
                    break
        else:
            return await cmd.send_usage()

        try:
            config = url_settings[atype]
            await cmd.typing()
            async with self.http.get(config[0]) as r:
                if r.status == 200:
                    data = await r.json()
                    if isinstance(config[2], int):
                        data = data[config[2]]
                    else:
                        for prop in config[2].split('.'):
                            data = data.get(prop, '')
                    embed = utils.img_embed(data, f'$[animal-{atype}-title]')
                    return await cmd.answer(embed)
        except Exception as e:
            self.log.error(e)
            await cmd.answer(f'$[animal-{atype}-error]')
