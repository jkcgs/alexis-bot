from modules.base.command import Command


class CmdOwner(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ownertest'
        self.help = 'Comando sólo para owners'
        self.allow_pm = False
        self.owner_only = True

    async def handle(self, message, cmd):
        await cmd.answer('eres owner o.o')


class CmdBotOwner(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'bonertest'
        self.help = 'Comando sólo para bot owners'
        self.allow_pm = False
        self.bot_owner_only = True

    async def handle(self, message, cmd):
        await cmd.answer('eres mi amo y señor <3')
