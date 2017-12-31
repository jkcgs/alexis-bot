from alexis import Command
from alexis.base import utils


class Cat(Command):
    url = 'http://random.cat/meow'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'cat'
        self.aliases = ['gato', 'gatito', 'neko']
        self.help = 'Entrega un gato'

    async def handle(self, message, cmd):
        try:
            await cmd.typing()
            async with self.http.get(Cat.url) as r:
                if r.status == 200:
                    data = await r.json()
                    await cmd.answer(embed=utils.img_embed(data['file'], 'aquí está tu gatito :3'))
                    return
        except Exception as e:
            self.log.error(e)
            await cmd.answer('no pude encontrar un gatito uwu')


# porque puedo
class Dog(Command):
    url = 'https://dog.ceo/api/breeds/image/random'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'dog'
        self.aliases = ['perro', 'perrito', 'doggo']
        self.help = 'Entrega un perro'

    async def handle(self, message, cmd):
        try:
            await cmd.typing()
            async with self.http.get(Dog.url) as r:
                if r.status == 200:
                    data = await r.json()
                    await cmd.answer(embed=utils.img_embed(data['message'], 'aquí está tu doggo :3'))
                    return
        except Exception as e:
            self.log.error(e)
            await cmd.answer('no pude encontrar un doggo :c')
