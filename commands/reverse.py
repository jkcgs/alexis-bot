from commands.base.command import Command


class Reverse(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reverse'
        self.help = 'Revierte el texto enviado'

    async def handle(self, message, cmd):
        text = cmd.text if cmd.text != '' else 'Formato: !reverse <texto>'
        if text.endswith(self.bot.config['command_prefix']):
            text = 'jaja ste men xd'
        else:
            text = list(text)
            text.reverse()
            text = ''.join(text)

        await cmd.answer(text)
