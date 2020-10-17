from bot import Command, categories
from bot.utils import auto_int


class LeaveGuild(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'leaveguild'
        self.aliases = ['leaveserver']
        self.help = '$[leaveguild-help]'
        self.category = categories.SETTINGS
        self.bot_owner_only = True
        self.default_config = {
            'whitelist': False,
            'whitelist_autoleave': False,
            'whitelist_servers': [],
            'blacklist_servers': []
        }

    async def handle(self, cmd):
        if cmd.argc == 0:
            return await cmd.send_usage()

        guild = self.bot.get_guild(auto_int(cmd.args[0]))
        if guild is None:
            await cmd.answer('$[leaveguild-guild-not-found]')
            return

        await guild.leave()
        try:
            await cmd.answer('$[leaveguild-left]', locales={'guild_name': guild.name, 'guild_id': guild.id})
        except Exception as e:
            self.log.exception(e)
