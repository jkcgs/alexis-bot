from commands.base.command import Command


class Ping(Command):
    def __init__(self, bot, message):
        super().__init__(bot, message)

    def handle(self, cmd):
        pass
