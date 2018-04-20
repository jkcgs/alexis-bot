import inspect
from discord import Embed

from bot import Command


class Modules(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'modules'
        self.help = 'Gestión de módulos'
        self.bot_owner_only = True

    async def handle(self, cmd):
        name = '' if cmd.argc == 0 else (cmd.args[0][1:] if cmd.args[0][0] in ['+', '-', '~', '!'] else cmd.args[0])
        if name == '':
            await cmd.answer('Módulos cargados:\n```{}```'.format(', '.join(self.bot.manager.get_mod_names())))
            return

        if cmd.args[0][0] == '+':
            if name == self.__class__.__name__:
                await cmd.answer('no puedes manejar este módulo!')
                return

            if self.bot.manager.has_mod(name):
                await cmd.answer('módulo ya cargado')
                return

            if await self.bot.manager.activate_mod(name):
                await cmd.answer('módulo cargado')
            else:
                await cmd.answer('módulo no encontrado')

            return

        if cmd.args[0][0] == '-':
            if name == self.__class__.__name__:
                await cmd.answer('no puedes manejar este módulo!')
                return

            if not self.bot.manager.has_mod(name):
                await cmd.answer('módulo no cargado')
                return

            self.bot.manager.unload_instance(name)
            await cmd.answer('módulo desactivado')
            return

        if cmd.args[0][0] == '~':
            if name == self.__class__.__name__:
                await cmd.answer('no puedes manejar este módulo!')
                return

            if not self.bot.manager.has_mod(name):
                await cmd.answer('módulo no cargado')
                return

            self.bot.manager.unload_instance(name)
            if await self.bot.manager.activate_mod(name):
                await cmd.answer('módulo reiniciado')
            else:
                await cmd.answer('el módulo no pudo ser reactivado')

            return

        if cmd.args[0][0] == '!':
            module = self.bot.manager.get_by_cmd(name)
        else:
            module = self.bot.manager.get_mod(name)

        if module is None:
            await cmd.answer('módulo no encontrado')
            return

        cmds = [n for n in [module.name] + module.aliases if n != '']
        cmds = ', '.join(cmds) or '(ninguno)'

        embed = Embed(title='Información de módulo')
        embed.description = '**{}** v{} por {}\n*{}*'.format(
            module.__class__.__name__, getattr(module, '__version__', '0.0.0'),
            getattr(module, '__author__', '*(sin autor)*'), module.help
        )

        embed.add_field(name='Comando(s)', value=cmds)
        embed.add_field(name='SW Handler', value=(', '.join(module.mention_handler or []) or '(ninguno)'))
        embed.add_field(name='Mention Handler', value=(', '.join(module.mention_handler or []) or '(ninguno)'))
        embed.add_field(name='Owner Only', value=str(module.owner_only))
        embed.add_field(name='Delay', value=('No' if module.user_delay == 0 else (str(module.user_delay) + 's')))
        embed.add_field(name='Ubicación', value=inspect.getfile(module.__class__))
        await cmd.answer(embed, withname=False)