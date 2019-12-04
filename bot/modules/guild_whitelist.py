from bot import Command


class GuildWhitelist(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.default_config = {
            'whitelist': False,
            'whitelist_autoleave': False,
            'whitelist_servers': [],
            'blacklist_servers': []
        }

    async def on_ready(self):
        if not self.bot.config.get('whitelist', False):
            return

        if not self.bot.config.get('whitelist_autoleave', False):
            return

        self.log.debug('I\'m in %s guilds', len(self.bot.servers))
        wlist = self.bot.config.get('whitelist_servers', [])
        guilds = [guild for guild in self.bot.guilds if guild.id not in wlist and int(guild.id) not in wlist]
        self.log.debug('%s guilds in the whitelist', len(wlist))
        self.log.debug('%s guilds not on the whitelist', len(guilds))
        for guild in guilds:
            self.log.debug('The guild "%s" (%s) is not on the whitelist, bye bye', guild.name, guild.id)
            await guild.leave()

    async def on_guild_join(self, guild):
        if self.join_allowed(guild.id):
            self.log.debug('I joined "%s" (%s) :3', guild.name, guild.id)
            return

        if guild.default_channel is not None:
            try:
                wcontact = self.bot.config.get('whitelist_contact', '')
                if wcontact == '':
                    message = '$[guildwl-bye] $[guildwl-admin]'
                    locales = None
                else:
                    message = '$[guildwl-bye] $[guildwl-admin]'
                    locales = {'owner_id': wcontact}

                await self.bot.send_message(guild.default_channel, message, locales=locales)
            except Exception as e:
                self.log.error('I could not say goodbye to "%s" (%s)'.format(guild.name, guild.id))
                self.log.exception(e)

        self.log.debug('The guild "%s" (%s) is not allowed, bye bye', guild.name, guild.id)
        await guild.leave()

    def join_allowed(self, guild_id):
        bl_list = self.bot.config.get('blacklist_servers', [])
        wl_enabled = self.bot.config.get('whitelist', False)
        wl_list = self.bot.config.get('whitelist_servers', [])

        return guild_id not in bl_list and (not wl_enabled or guild_id in wl_list)
