from bot import Command, categories


class ReloadCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reload'
        self.help = '$[config-reload-help]'
        self.bot_owner_only = True
        self.category = categories.SETTINGS

    async def handle(self, cmd):
        if not self.bot.load_config():
            await cmd.answer('$[config-reload-err]')
            return

        nmods = len([i.load_config() for i in self.bot.manager.cmd_instances if callable(getattr(i, 'load_config', None))])
        await cmd.answer('$[config-reloaded]', locales={'rel_mods': nmods})
