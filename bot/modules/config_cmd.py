from bot import Command, Configuration, categories
from bot.utils import split_list


class ConfigCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'config'
        self.help = '$[config-admin]'
        self.bot_owner_only = True
        self.category = categories.SETTINGS

    async def handle(self, cmd):
        if cmd.argc < 2 or (cmd.args[0] != 'get' and cmd.argc < 3):
            await cmd.answer('$[config-format]')
            return

        if cmd.subcmd == '':
            cfg = self.bot.config
        else:
            if not Configuration.exists(cmd.subcmd):
                await cmd.answer('$[config-not-exists]')
                return
            cfg = Configuration.get_config(cmd.subcmd)

        arg = cmd.args[0]
        name = cmd.args[1]

        if name not in cfg:
            await cmd.answer('$[config-value-not-exists]')
            return

        val = cfg[name]

        if arg == 'get':
            if name not in cfg:
                await cmd.answer('$[config-not-exists]')
                return

            if isinstance(val, list):
                if len(val) == 0:
                    await cmd.answer('$[config-empty-list]', locales={'list_name': name})
                else:
                    await cmd.answer('$[config-list-values]:', locales={'list_name': name})
                    items = ['- ' + str(f) for f in val]
                    for chunk in split_list(items, 1800):
                        cont = '\n'.join(chunk)
                        await cmd.answer('```{}```'.format(cont))
            else:
                await cmd.answer('$[config-value]', locales={'config_name': name, 'config_value': str(val)})
        else:
            await cmd.answer('$[config-err-sub]')
