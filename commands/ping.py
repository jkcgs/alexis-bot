from commands.base.command import Command


class Ping(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ping'
        self.owner_only = False

    def handle(self, message):
        cmd = self.parse(message, self.bot)
        cmd.answer('Pong!')
