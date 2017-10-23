from modules.base.command import Command, ConfigError
from modules.base.database import ServerConfig


class ConfigCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'config'
        self.help = 'Define una configuración para servidor'
        self.allow_pm = False
        self.owner_only = True
        self.db_models = [ServerConfig]

    async def handle(self, message, cmd):
        if len(cmd.args) < 2:
            cmd.answer('Formato: !config <nombre> <valor>')
            return

        name = cmd.args[0]
        value = ' '.join(cmd.args[1:])

        # Verificar si existe esa configuración
        if name not in self.bot.config_handlers:
            await cmd.answer('No existe esa configuración :o')
            return

        sconfig, created = ServerConfig.get_or_create(serverid=message.server.id, name=name)
        if created:
            sconfig.value = self.bot.config_defaults[name]

        try:
            await self.bot.config_handlers[name](name, value, cmd)
        except ConfigError as e:
            await cmd.answer('Error en la configuración: ' + str(e))
