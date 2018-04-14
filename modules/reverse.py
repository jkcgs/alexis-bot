import random

from bot import Command


class Reverse(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reverse'
        self.help = 'Revierte el texto enviado'

    async def handle(self, cmd):
        text = cmd.no_tags() if cmd.text != '' else 'formato: {}{} <texto>'.format(cmd.prefix, cmd.cmdname)
        if cmd.text.startswith(cmd.prefix):
            text = random.choice(['jaja ste men', 'oye nuuuu', 'jajaj jurai', 'que wea tramposo qlo', 'xd'])
        else:
            text = list(text)
            text.reverse()
            text = ''.join(text)

        await cmd.answer_embed(text)
