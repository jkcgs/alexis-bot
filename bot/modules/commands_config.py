from bot import Command, categories
from bot.utils import unserialize_avail, serialize_avail


class CommandConfig(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'cmd'
        self.help = '$[cmd-help]'
        self.format = '$[cmd-format]'
        self.owner_only = True
        self.category = categories.STAFF

    async def handle(self, cmd):
        if cmd.argc == 1 and any(cmd.args[0].startswith(i) for i in ['+', '-']):
            cmd.args = [['enable', 'disable'][cmd.args[0][0] == '-'], cmd.args[0][1:], *cmd.args[1:]]
            cmd.argc = len(cmd.args)

        if cmd.argc < 2 or cmd.args[0] not in ['enable', 'disable']:
            return await cmd.send_usage()

        if cmd.args[1] not in self.bot.manager:
            await cmd.answer('$[cmd-not-found]')
            return

        if cmd.args[1] == self.name:
            await cmd.answer('$[cmd-not-allowed]')
            return

        avail = serialize_avail(cmd.config.get('cmd_status', ''))
        cmd_ins = self.bot.manager[cmd.args[1]]
        current = avail.get(cmd_ins.name, '+' if cmd_ins.default_enabled else '-')

        if cmd.args[0] == 'enable':
            if current == '+':
                return await cmd.answer('$[cmd-already-enabled]', locales={'command': cmd_ins.name})

            else:
                avail[cmd_ins.name] = '+'
                cmd.config.set('cmd_status', unserialize_avail(avail))
                return await cmd.answer('$[cmd-enabled]', locales={'command': cmd_ins.name})

        elif cmd.args[0] == 'disable':
            if current == '-':
                return await cmd.answer('$[cmd-already-disabled]', locales={'command': cmd_ins.name})
            else:
                avail[cmd_ins.name] = '-'
                cmd.config.set('cmd_status', unserialize_avail(avail))
                return await cmd.answer('$[cmd-disabled]', locales={'command': cmd_ins.name})
        else:
            return await cmd.send_usage()
