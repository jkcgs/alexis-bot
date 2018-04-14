import inspect
from discord import Embed

from modules import get_mods
from bot import Command


class Modules(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'modules'
        self.bot_owner_only = True

    async def handle(self, cmd):
        name = '' if cmd.argc == 0 else (cmd.args[0][1:] if cmd.args[0][0] in ['+', '-', '~'] else cmd.args[0])
        if name == '':
            await cmd.answer('Módulos cargados:\n```{}```'.format(', '.join(self.get_mod_names())))
            return

        if cmd.args[0][0] == '+':
            if name == self.__class__.__name__:
                await cmd.answer('no puedes manejar este módulo!')
                return

            if self.get_mod(name) is not None:
                await cmd.answer('módulo ya cargado')
                return

            if await self.activate_mod(name):
                await cmd.answer('módulo cargado')
            else:
                await cmd.answer('módulo no encontrado')

            return

        if cmd.args[0][0] == '-':
            if name == self.__class__.__name__:
                await cmd.answer('no puedes manejar este módulo!')
                return

            if self.get_mod(name) is None:
                await cmd.answer('módulo no cargado')
                return

            self.bot.unload_instance(name)
            await cmd.answer('módulo desactivado')
            return

        if cmd.args[0][0] == '~':
            if name == self.__class__.__name__:
                await cmd.answer('no puedes manejar este módulo!')
                return

            if self.get_mod(name) is None:
                await cmd.answer('módulo no cargado')
                return

            self.bot.unload_instance(name)
            if await self.activate_mod(name):
                await cmd.answer('módulo reiniciado')
            else:
                await cmd.answer('el módulo no pudo ser reactivado')

            return

        module = self.get_mod(name)
        if module is None:
            await cmd.answer('módulo no encontrado')
            return

        cmds = [n for n in [module.name] + module.aliases if n != '']
        cmds = ', '.join(cmds) or '(ninguno)'

        embed = Embed(title='Información de módulo')
        embed.description = '**{}** v{} por {}\n*{}*'.format(
            name, getattr(module, '__version__', '0.0.0'), getattr(module, '__author__', '(sin autor)'),
            module.help
        )
        embed.add_field(name='Comando(s)', value=cmds)
        embed.add_field(name='SW Handler', value=(', '.join(module.mention_handler or []) or '(ninguno)'))
        embed.add_field(name='Mention Handler', value=(', '.join(module.mention_handler or []) or '(ninguno)'))
        embed.add_field(name='Owner Only', value=str(module.owner_only))
        embed.add_field(name='Delay', value=('No' if module.user_delay == 0 else (str(module.user_delay) + 's')))
        embed.add_field(name='Ubicación', value=inspect.getfile(module.__class__))
        await cmd.answer(embed, withname=False)

    def get_mod_names(self):
        names = [i.__class__.__name__ for i in self.bot.cmd_instances]
        names.sort()
        return names

    def get_mod(self, name):
        for i in self.bot.cmd_instances:
            if i.__class__.__name__ == name:
                return i

        return None

    async def activate_mod(self, name):
        classes = get_mods(self.bot.config.get('ext_modpath', ''))
        for cls in classes:
            if cls.__name__ == name:
                self.log.debug('Cargando módulo "%s"...', name)
                ins = self.bot.load_command(cls)
                if hasattr(ins, 'on_loaded'):
                    self.log.debug('Llamando on_loaded para "%s"', name)
                    ins.on_loaded()
                if hasattr(ins, 'on_ready'):
                    self.log.debug('Llamando on_ready para "%s"', name)
                    await ins.on_ready()

                self.bot.cmd_instances.append(ins)
                self.log.debug('Módulo "%s" cargado', name)
                return True

        return False
