from bot import Command, utils, categories


class Cat(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'
    url = 'http://aws.random.cat/meow'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'cat'
        self.aliases = ['gato', 'gatito', 'neko']
        self.help = '$[animal-cats-help]'
        self.category = categories.IMAGES

    async def handle(self, cmd):
        try:
            await cmd.typing()
            async with self.http.get(Cat.url) as r:
                if r.status == 200:
                    data = await r.json()
                    await cmd.answer(embed=utils.img_embed(data['file'], '$[animal-cats-title]'))
                    return
        except Exception as e:
            self.log.error(e)
            await cmd.answer('$[animal-cats-error]')


class Dog(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'
    url = 'https://dog.ceo/api/breeds/image/random'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'dog'
        self.aliases = ['perro', 'perrito', 'doggo']
        self.help = '$[animal-dogs-help]'
        self.category = categories.IMAGES

    async def handle(self, cmd):
        try:
            await cmd.typing()
            async with self.http.get(Dog.url) as r:
                if r.status == 200:
                    data = await r.json()
                    await cmd.answer(embed=utils.img_embed(data['message'], '$[animal-dogs-title]'))
                    return
        except Exception as e:
            self.log.error(e)
            await cmd.answer('$[animal-dogs-error]')


class Shibes(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'
    url = 'http://shibe.online/api/shibes'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'shiba'
        self.aliases = ['shibe', 'shibainu']
        self.help = '$[animal-shiba-help]'
        self.category = categories.IMAGES

    async def handle(self, cmd):
        try:
            await cmd.typing()
            async with self.http.get(self.url) as r:
                if r.status == 200:
                    data = await r.json()
                    await cmd.answer(embed=utils.img_embed(data[0], '$[animal-shiba-title]'))
                    return
        except Exception as e:
            self.log.error(e)
            await cmd.answer('$[animal-shiba-error]')


class RandomFox(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'
    url = 'https://randomfox.ca/floof/'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'fox'
        self.help = '$[animal-fox-help]'
        self.category = categories.IMAGES

    async def handle(self, cmd):
        try:
            await cmd.typing()
            async with self.http.get(self.url) as r:
                if r.status == 200:
                    data = await r.json()
                    await cmd.answer(embed=utils.img_embed(data['image'], '$[animal-fox-title]'))
                    return
        except Exception as e:
            self.log.error(e)
            await cmd.answer('$[animal-fox-error]')
