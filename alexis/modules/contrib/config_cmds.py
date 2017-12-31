import sys

from discord import Game

from alexis import Command
from alexis.base.utils import is_float, is_int


class ConfigCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'config'
        self.help = 'Administración de configuración'
        self.bot_owner_only = True

    async def handle(self, message, cmd):
        if cmd.argc < 2 or (cmd.args[0] != 'get' and cmd.argc < 3):
            await cmd.answer('$PX$NM (get|set|add|remove) (name) [value]')
            return

        cfg = self.bot.config
        arg = cmd.args[0]
        name = cmd.args[1]
        val = cfg[name]

        if arg == 'get':
            if name not in cfg:
                await cmd.answer('esa configuración no existe')
                return

            if isinstance(val, list):
                if len(val) == 0:
                    await cmd.answer('la lista "{}" está vacía'.format(name))
                else:
                    await cmd.answer('valores de "{}":\n```- {}```'.format(name, '\n- '.join(val)))
            else:
                await cmd.answer('valor de "{}": **{}**'.format(name, str(val)))
        elif arg == 'set':
            if isinstance(val, list):
                await cmd.answer('"{}" es una lista, para manejar sus valores, utiliza "add" o "remove"')
                return

            argvalue = ' '.join(cmd.args[2:])
            if isinstance(val, bool):
                if argvalue.lower() in ['0', 'false', 'no', 'disabled', 'off']:
                    argvalue = False
                elif argvalue.lower() in ['1', 'true', 'yes', 'enabled', 'on']:
                    argvalue = True
                else:
                    await cmd.answer('el valor de "{}" sólo acepta valores booleanos. Prueba con 0 o 1.'.format(name))
                    return
            elif isinstance(val, float):
                if not is_float(argvalue):
                    await cmd.answer('el valor de "{}" sólo acepta decimales'.format(name))
                    return
                else:
                    argvalue = float(argvalue)
            elif isinstance(val, int):
                if not is_int(argvalue):
                    await cmd.answer('el valor de "{}" sólo acepta números enteros'.format(name))
                    return
                else:
                    argvalue = int(argvalue)

            self.bot.config[name] = argvalue
            await cmd.answer('valor de "{}" actualizado'.format(name))
        elif arg == 'add' or arg == 'remove':
            if not isinstance(val, list):
                await cmd.answer('"{}" no es una lista, para manejar sus valor, utiliza el subcomando "set"')
                return

            argvalue = ' '.join(cmd.args[2:])
            if arg == 'add':
                if argvalue in val:
                    await cmd.answer('ese valor ya está en la lista')
                    return

                val.append(argvalue)
                self.bot.config[name] = val
                await cmd.answer('valor agregado a la lista')
                return
            elif arg == 'remove':
                if argvalue not in val:
                    await cmd.answer('ese valor no está en la lista')
                    return

                val.remove(argvalue)
                self.bot.config[name] = val
                await cmd.answer('valor eliminado de la lista')
                return
        else:
            await cmd.answer('comando incorrecto')


class ReloadCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reload'
        self.help = 'Recarga la configuración'
        self.bot_owner_only = True

    async def handle(self, message, cmd):
        if not self.bot.load_config():
            msg = 'no se pudo recargar la configuración'
        else:
            msg = 'configuración recargada correctamente'

        nmods = len([i.load_config() for i in self.bot.cmd_instances if callable(getattr(i, 'load_config', None))])
        if nmods > 0:
            msg += ', incluyendo {} módulo{}'.format(nmods, ['s', ''][int(nmods == 1)])

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