from commands.base.command import Command


class Ping(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ping'

    async def handle(self, message, cmd):
        await cmd.answer('Pong!')
