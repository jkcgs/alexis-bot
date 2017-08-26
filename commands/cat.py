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
            with urllib.request.urlopen(Cat.url) as urlresp:
                data = json.loads(urlresp.read().decode())
                if 'file' in data:
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
            with urllib.request.urlopen(Dog.url) as urlresp:
                data = json.loads(urlresp.read().decode())
                if 'status' in data and data['status'] == 'success':
                    await cmd.answer('aquí está tu perrito :3', embed=Command.img_embed(data['message']))
                    return
        except Exception as e:
            self.log.error(e)
