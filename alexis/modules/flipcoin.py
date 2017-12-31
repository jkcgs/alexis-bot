import random

from alexis import Command


class Flipcoin(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'flipcoin'
        self.aliases = ['coinflip', 'coin', 'moneda']
        self.help = 'Lanza una moneda y muestra el resultado'

    async def handle(self, message, cmd):
        prob = random.random()
        if prob < .01:
            resp = 'CANTO WN, EN SERIO XDDDD'
        elif prob <= .5:
            resp = 'Cara'
        else:
            resp = 'Sello'

        self.log.debug('probabilidad: {} ({})'.format(prob, resp))
        await cmd.answer('**{}**'.format(resp))
