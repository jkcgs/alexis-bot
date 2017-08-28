import json
import urllib.request
from discord import Embed

from commands.base.command import Command


class Cat(Command):
    url = 'http://random.cat/meow'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['cat', 'gato']
        self.help = 'Entrega un gato'

    async def handle(self, message, cmd):
        try:
            await cmd.typing()
            async with self.http.get(Cat.url) as r:
                if r.status == 200:
                    data = await r.json()
                    await cmd.answer('aquí está tu gatito :3', embed=Command.img_embed(data['file']))
                    return
        except Exception as e:
            self.log.error(e)


# porque puedo
class Dog(Command):
    url = 'https://dog.ceo/api/breeds/image/random'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['dog', 'perro']
        self.help = 'Entrega un perro'

    async def handle(self, message, cmd):
        try:
            await cmd.typing()
            async with self.http.get(Dog.url) as r:
                if r.status == 200:
                    data = await r.json()
                    await cmd.answer('aquí está tu perrito :3', embed=Command.img_embed(data['message']))
                    return
        except Exception as e:
            self.log.error(e)
