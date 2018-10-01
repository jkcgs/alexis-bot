from bot import Command, categories
import random

hearts = ['heart', 'hearts', 'yellow_heart', 'green_heart', 'blue_heart', 'purple_heart']


class Respects(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'respects'
        self.aliases = ['f']
        self.help = '$[respects-help]'
        self.category = categories.FUN

    async def handle(self, cmd):
        hearts_m = ''
        for x in range(random.randint(1, 3)):
            hearts_m = ' :' + random.choice(hearts) + ':'

        if cmd.text != '':
            await cmd.answer('$[respects-paid-to]', withname=False, locales={'thing': cmd.text, 'hearts': hearts_m})
        else:
            await cmd.answer('$[respects-paid]', withname=False, locales={'hearts': hearts_m})
