from bot import Command


class RolelessFilter(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'roleless'
        self.owner_only = True
        self.allow_pm = False
        self.help = '$[roleless-help]'
        self.format = '$[roleless-format]'

    async def handle(self, cmd):
        subcmd = 'count' if cmd.argc < 1 else cmd.args[0]

        if subcmd == 'count':
            await cmd.typing()

            rlcount = 0
            for member in cmd.guild.members:
                if len(member.roles) == 0:
                    rlcount += 1
            await cmd.answer('$[roleless-count]', locales={'count': rlcount})
        else:
            await cmd.answer(self.format)
