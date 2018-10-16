import random

from bot import Command, categories


class Flipcoin(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'
    __description__ = 'Generates a number between 0 and 1, then given its value, returns a side of a coin.'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'flipcoin'
        self.aliases = ['coinflip', 'coin', 'moneda']
        self.help = '$[random-coin-help]'
        self.format = '$CMD'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        # Generate the random number, translate it to a coin side
        prob = random.random()
        if prob < .01:
            resp = '$[random-coin-side]'
        elif prob <= .5:
            resp = '$[random-coin-head]'
        else:
            resp = '$[random-coin-tails]'

        # Log the random number, and send the coin side back
        self.log.debug('Probability: {} ({})'.format(prob, resp))
        await cmd.answer('**{}**'.format(resp))
