from discord import Embed

from bot import Command, categories


class GuildList(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'guildlist'
        self.aliases = ['guilds']
        self.category = categories.SETTINGS
        self.bot_owner_only = True

    async def handle(self, cmd):
        if not cmd.is_pm:
            await cmd.answer('$[guildlist-answer]')

        if len(self.bot.guilds) == 0:
            await cmd.answer('$[guildlist-none]', to_author=True)
            return

        await cmd.answer('$[guildlist-msg]', locales={'amount': len(self.bot.guilds)}, to_author=True)

        resp_list = ''
        for guild in self.bot.guilds:
            item = '- {} ({})'.format(guild.name, guild.id)

            if len('{}\n{}'.format(resp_list, item)) > 2000:
                await cmd.answer(Embed(description=resp_list), withname=False, to_author=True)
                resp_list = ''
            else:
                resp_list = '{}\n{}'.format(resp_list, item)

        # Send remaining list
        if resp_list != '':
            await cmd.answer(Embed(description=resp_list), withname=False, to_author=True)
