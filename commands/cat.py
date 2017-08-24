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
                    emb = Embed()
                    emb.set_image(url=data['file'])
                    await cmd.answer('aquí está tu gatito :3', embed=emb)
                    return
        except Exception as e:
            self.log.error(e)
