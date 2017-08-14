from commands.base.command import Command
import sys


class ToggleConversation(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'toggleconversation'
        self.owner_only = True

    async def handle(self, message, cmd):
        self.bot.conversation = not self.bot.conversation
        resp = 'activada' if self.bot.conversation else 'desactivada'
        await cmd.answer('Conversación {}'.format(resp))


class ReloadCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reload'
        self.owner_only = True

    async def handle(self, message, cmd):
        if not self.bot.load_config():
            msg = 'No se pudo recargar la configuración'
        else:
            msg = 'Configuración recargada correctamente'

        await cmd.answer(msg)


class ShutdownCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'shutdown'
        self.owner_only = True

    async def handle(self, message, cmd):
        await cmd.answer('chao loh vimo')
        sys.exit(0)
