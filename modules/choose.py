import random

from bot import Command, categories


class Choose(Command):
    __author__ = 'makzk'
    __version__ = '1.1.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'choose'
        self.help = '$[random-choose-help]'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        # Parse options and filter empty options
        separator = '|' if '|' in cmd.text else ' '
        options = [o.strip() for o in cmd.text.split(separator) if o.strip() != '']

        # At least 2 options are required
        if len(options) < 2:
            await cmd.answer('$[random-choose-not-enough]')
            return

        # Choose an option and send it
        answer = random.choice(options).strip()
        await cmd.answer('$[random-choose-answer]', as_embed=True, locales={'answer': answer})
