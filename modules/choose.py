import random

from bot import Command, categories


class Choose(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'choose'
        self.help = '$[random-choose-help]'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        # Parse options and filter empty options
        options = [o.strip() for o in cmd.text.split("|") if o.strip() != '']

        # At least 2 options are required
        if len(options) < 2:
            await cmd.answer('$[random-choose-not-enough]')
            return

        # Choose an option and send it
        answer = random.choice(options).strip()
        await cmd.answer_embed('$[random-choose-answer]', locales={'answer': answer})
