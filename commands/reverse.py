from commands.base.command import Command


class Reverse(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reverse'
        self.help = 'Revierte el texto enviado'

    async def handle(self, message, cmd):
        text = cmd.text if cmd.text != '' else 'Formato: !reverse <texto>'
        text = list(text)
        text.reverse()
        await cmd.answer(''.join(text))
