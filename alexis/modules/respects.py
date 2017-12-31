from alexis import Command
import random


class Respects(Command):
    hearts = ['heart', 'hearts', 'yellow_heart', 'green_heart', 'blue_heart', 'purple_heart']

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'respects'
        self.aliases = ['f']
        self.help = 'Muestra que el usuario que ejecuta el comando ha dado respetos'

    async def handle(self, message, cmd):
        msg = '**$AU** ha pedido respetos '
        if cmd.text != '':
            msg += 'por **{}** '.format(cmd.text)

        for x in range(random.randint(1, 3)):
            msg += ':' + random.choice(Respects.hearts) + ':'

        await cmd.answer(msg, withname=False)
