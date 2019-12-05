import random

from bot import Command, categories


class RandomNum(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'random'
        self.aliases = ['rand']
        self.help = '$[random-help]'
        self.format = '$CMD <n1> <n2>'
        self.category = categories.UTILITY

    async def handle(self, cmd):
        nmin = 1
        nmax = 10

        if cmd.argc >= 1:
            if not cmd.args[0].isnumeric() or (cmd.argc >= 2 and not cmd.args[1].isnumeric()):
                await cmd.answer('$[random-error-number-only]')
                return

            if cmd.argc == 1:
                nmax = int(cmd.args[0])
            else:
                nmin = int(cmd.args[0])

            if cmd.argc >= 2:
                nmax = int(cmd.args[1])

        if nmax < nmin:
            ntemp = nmax
            nmax = nmin
            nmin = ntemp
            del ntemp

        if nmin == nmax:
            await cmd.answer('$[random-single-answer]', locales={'num1': nmin, 'num2': nmax, 'result': nmin})
        else:
            rand = random.randint(nmin, nmax)
            answ = 'random({}, {}) => **{}**'.format(nmin, nmax, rand)

            await cmd.answer(answ)
