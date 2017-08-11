from commands.base.command import Command


class Ping(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ping'
        self.owner_only = False

    async def handle(self, message):
        self.bot.log.debug('Handling !ping')
        cmd = Command.parse(message, self.bot)
        await cmd.answer('Pong!')
        self.bot.log.debug('Handled !ping')
