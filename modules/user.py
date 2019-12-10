from bot import Command, categories
from modules.modlog import ModLog


class UserCommand(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'user'
        self.aliases = [bot.config['command_prefix'] + 'user']
        self.help = '$[modlog-cmd-help]'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        if cmd.cmdname == self.aliases[0] and not cmd.owner:
            return

        if cmd.argc == 0:
            user = cmd.author
        else:
            user = await cmd.get_user(cmd.text, member_only=True)
            if user is None:
                await cmd.answer('$[user-not-found]')
                return

        with_notes = cmd.cmdname == self.aliases[0] and cmd.owner
        embed = ModLog.gen_embed(user, with_notes)
        await cmd.answer('$[modlog-cmd-title]', embed=embed, locales={'user_id': user.id})
