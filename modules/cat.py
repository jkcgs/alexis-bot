from bot import Command, utils, categories


class Cat(Command):
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
