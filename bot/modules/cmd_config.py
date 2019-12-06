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
        if cmd.argc < 2:
            await cmd.answer('$[format]: $[cmd-format]')
            return

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
                await cmd.answer('$[cmd-already-enabled]')
                return
            else:
                avail[cmd_ins.name] = '+'
                cmd.config.set('cmd_status', unserialize_avail(avail))
                await cmd.answer('$[cmd-enabled]')
                return
        elif cmd.args[0] == 'disable':
            if current == '-':
                await cmd.answer('$[cmd-already-disabled]')
                return
            else:
                avail[cmd_ins.name] = '-'
                cmd.config.set('cmd_status', unserialize_avail(avail))
                await cmd.answer('$[cmd-disabled]')
                return
        else:
            await cmd.answer('$[format]: $[cmd-format]')


