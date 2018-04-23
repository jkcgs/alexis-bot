import random
from bot import Command


class Choose(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'choose'
        self.help = 'Elige un elemento al azar de una lista separada por el símbolo "|"'

    async def handle(self, cmd):
        options = cmd.text.split("|")
        if len(options) < 2:
            return

        # Validar que no hayan opciones vacías
        for option in options:
            if option.strip() == '':
                return

        answer = random.choice(options).strip()
        text = 'yo elijo **{}**'.format(answer)
        await cmd.answer(text)
