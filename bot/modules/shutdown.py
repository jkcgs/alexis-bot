import sys

from bot import Command, categories


class ShutdownCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'shutdown'
        self.help = '$[shutdown-help]'
        self.bot_owner_only = True
        self.category = categories.SETTINGS

    async def handle(self, cmd):
        await cmd.answer('$[shutdown-goodbye]')
        await self.bot.close()
        sys.exit(0)
