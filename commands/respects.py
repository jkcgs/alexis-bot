from commands.base.command import Command
import random


class Respects(Command):
    hearts = ['heart', 'hearts', 'yellow_heart', 'green_heart', 'blue_heart', 'purple_heart']

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'f'

    async def handle(self, message):
        cmd = self.parse(message)
        msg = '**{}** ha pedido respetos {}'
        heart = random.choice(Respects.hearts)

        if cmd.text == '':
            msg = msg.format(cmd.author_name, ':{}:'.format(heart))
        else:
            msg = msg.format(cmd.author_name, 'por **{}** :{}:'.format(cmd.text, heart))

        await cmd.answer(msg)
