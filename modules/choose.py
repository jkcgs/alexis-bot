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


class RandomNum(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'random'
        self.aliases = ['rand']
        self.help = 'Elige un número al azar'

    async def handle(self, cmd):
        nmin = 0
        nmax = 10

        if cmd.argc >= 1:
            if not cmd.args[0].isnumeric() or (cmd.argc >= 2 and not cmd.args[1].isnumeric()):
                await cmd.answer('por favor ingresa sólo números')
                return

            nmin = int(cmd.args[0])

            if cmd.argc >= 2:
                nmax = int(cmd.args[1])

        if nmax < nmin:
            ntemp = nmax
            nmax = nmin
            nmin = ntemp
            del ntemp

        if nmin == nmax:
            jaja = 'tu número entre {} y {}, *AUNQUE NO LO PUEDAS CREER*, es el **{}** :open_mouth:'
            await cmd.answer(jaja.format(nmin, nmax, nmin))
        else:
            rand = random.randint(nmin, nmax)
            answ = 'tu número entre {} y {} es el **{}**'.format(nmin, nmax, rand)

            await cmd.answer(answ)
