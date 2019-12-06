from bot import Command, categories, BotMentionEvent
from bot.events import is_bot_command


class ChangePrefix(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.mention_handler = True
        self.name = 'prefix'
        self.aliases = ['changeprefix']
        self.help = '$[prefix-help]'
        self.owner_only = True
        self.category = categories.STAFF

    async def handle(self, cmd):
        if not is_bot_command(cmd):
            return

        if cmd.argc < 1 or (isinstance(cmd, BotMentionEvent) and cmd.argc == 1 and cmd.args[0] == self.name):
            await cmd.answer('$[prefix-current]',
                             locales={'command_name': self.name, 'self_mention': self.bot.user.mention})
            return

        if (isinstance(cmd, BotMentionEvent) and (cmd.argc != 2 or cmd.args[0] != self.name)) \
                or (not isinstance(cmd, BotMentionEvent) and cmd.argc != 1):
            return

        prefix = cmd.args[1 if isinstance(cmd, BotMentionEvent) else 0]
        if len(prefix) > 3:
            return

        cmd.config.set('command_prefix', prefix)
        await cmd.answer('$[prefix-set]', locales={'new_prefix': prefix})
