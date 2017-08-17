from commands.base.command import Command
from discord import Game
import sys
import alexis


class ReloadCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reload'
        self.help = 'Recarga la configuración'
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
        self.help = 'Detiene el proceso del bot'
        self.owner_only = True

    async def handle(self, message, cmd):
        await cmd.answer('chao loh vimo')
        await self.bot.logout()
        sys.exit(0)


class InfoCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['version', 'info']
        self.help = 'Muestra la información del bot'

    async def handle(self, message, cmd):
        info_msg = "```\nAutores: {}\nVersión: {}\nEstado: {}```"
        info_msg = info_msg.format(alexis.__author__, alexis.__version__, alexis.__status__)
        await cmd.answer(info_msg)


class SetStatus(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'status'
        self.help = 'Determina el status del bot'
        self.owner_only = True

    async def handle(self, message, cmd):
        status = '' if len(cmd.args) < 1 else cmd.text
        await self.bot.change_presence(game=Game(name=status))
        await cmd.answer('k')
