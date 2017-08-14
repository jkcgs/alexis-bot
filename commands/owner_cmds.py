from commands.base.command import Command
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