import inspect
from discord import Embed

from bot import Command, categories


class Modules(Command):
    __version__ = '1.0.1'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'modules'
        self.aliases = ['module']
        self.help = '$[modules-help]'
        self.category = categories.SETTINGS
        self.bot_owner_only = True

    async def handle(self, cmd):
        mgr = self.bot.manager
        name = '' if cmd.argc == 0 else (cmd.args[0][1:] if cmd.args[0][0] in ['+', '-', '~', '!'] else cmd.args[0])
        if name == '':
            await cmd.answer('$[modules-loaded]\n```{}```'.format(', '.join(mgr.get_mod_names())))
            return

        if cmd.args[0][0] == '+':
            if name == self.__class__.__name__:
                await cmd.answer('$[modules-err-self]')
                return

            if mgr.has_mod(name):
                await cmd.answer('$[modules-already-loaded]')
                return

            if await mgr.activate_mod(name):
                await cmd.answer('$[module-loaded]')
            else:
                await cmd.answer('$[module-not-found]')

            return

        if cmd.args[0][0] == '-':
            if name == self.__class__.__name__:
                await cmd.answer('$[modules-err-self]')
                return

            if not mgr.has_mod(name):
                await cmd.answer('$[module-not-loaded]')
                return

            mgr.unload_instance(name)
            await cmd.answer('$[module-disabled]')
            return

        if cmd.args[0][0] == '~':
            if name == self.__class__.__name__:
                await cmd.answer('$[modules-err-self]')
                return

            if not mgr.has_mod(name):
                await cmd.answer('$[module-not-loaded]')
                return

            mgr.unload_instance(name)
            if await mgr.activate_mod(name):
                await cmd.answer('$[module-reloaded]')
            else:
                await cmd.answer('$[module-not-reactivated]')

            return

        if cmd.args[0][0] == '!':
            module = mgr.get_by_cmd(name)
        else:
            module = mgr.get_mod(name)

        if module is None:
            await cmd.answer('$[module-not-found]')
            return

        cmds = [n for n in [module.name] + module.aliases if n != '']
        cmds = ', '.join(cmds) or '$[module-none]'

        embed = Embed(title='$[module-e-title]', description='$[module-e-description]')
        embed.add_field(name='$[module-e-commands]', value=cmds)
        embed.add_field(name='$[module-e-swhandler]', value=(', '.join(module.swhandler or []) or '$[module-none]'))
        embed.add_field(name='$[module-e-mentionhandlers]', value=module.mention_handler)
        embed.add_field(name='$[module-e-owner-only]', value=str(module.owner_only))
        embed.add_field(name='$[module-e-delay]', value=(
            '$[module-e-no]' if module.user_delay == 0 else (str(module.user_delay) + 's')))
        embed.add_field(name='$[module-e-priority]', value=module.priority)
        embed.add_field(name='$[module-e-path]', value=inspect.getfile(module.__class__))

        await cmd.answer(embed, withname=False, locales={
            'mod_name': module.__class__.__name__,
            'mod_version': getattr(module, '__version__', '0.0.0'),
            'mod_author': getattr(module, '__author__', '$[module-no-author]'),
            'mod_help': module.help
        })
