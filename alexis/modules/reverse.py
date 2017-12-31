import random

from alexis import Command


class Reverse(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reverse'
        self.help = 'Revierte el texto enviado'

    async def handle(self, message, cmd):
        text = cmd.text if cmd.text != '' else 'formato: !reverse <texto>'
        if text.endswith(cmd.prefix):
            text = random.choice(['jaja ste men', 'oye nuuuu', 'jajaj jurai', 'que wea tramposo qlo', 'xd'])
        else:
            text = list(text)
            text.reverse()
            text = ''.join(text)

        await cmd.answer(text)
