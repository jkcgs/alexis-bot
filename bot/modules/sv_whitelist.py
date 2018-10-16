from discord import Embed

from bot import Command, categories


class ServerWhitelist(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'leaveserver'
        self.help = '$[leaveserver-help]'
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
            await cmd.answer('$[format]: $[leaveserver-format]')
            return

        server = self.bot.get_server(cmd.args[0])
        if server is None:
            await cmd.answer('$[leaveserver-guild-not-found]')
            return

        await self.bot.leave_server(server)
        try:
            await cmd.answer('$[leaveserver-left]', locales={'guild_name': server.name, 'guild_id': server.id})
        except Exception as e:
            self.log.exception(e)

    async def on_ready(self):
        if not self.bot.config.get('whitelist', False):
            return

        if not self.bot.config.get('whitelist_autoleave', False):
            return

        self.log.debug('I\'m in %s servers', len(self.bot.servers))
        wlist = self.bot.config.get('whitelist_servers', [])
        servers = [sv for sv in self.bot.servers if sv.id not in wlist and int(sv.id) not in wlist]
        self.log.debug('%s servers in the whitelist', len(wlist))
        self.log.debug('%s servers not on the whitelist', len(servers))
        for server in servers:
            self.log.debug('The guild "%s" (%s) is not on the whitelist, bye bye', server.name, server.id)
            await self.bot.leave_server(server)

    async def on_server_join(self, server):
        if self.join_allowed(server.id):
            self.log.debug('I joined "%s" (%s) :3', server.name, server.id)
            return

        if server.default_channel is not None:
            try:
                wcontact = self.bot.config.get('whitelist_contact', '')
                if wcontact == '':
                    await self.bot.send_message(server.default_channel, '$[leaveserver-bye] $[leaveserver-admin]')
                else:
                    await self.bot.send_message(server.default_channel, '$[leaveserver-bye] $[leaveserver-owner]',
                                                locales={'owner_id': wcontact})
            except Exception as e:
                self.log.error('I could not say goodbye to "%s" (%s)'.format(server.name, server.id))
                self.log.exception(e)

        self.log.debug('The guild "%s" (%s) is not allowed, bye bye', server.name, server.id)
        await self.bot.leave_server(server)

    def join_allowed(self, serverid):
        bl_list = self.bot.config.get('blacklist_servers', [])
        wl_enabled = self.bot.config.get('whitelist', False)
        wl_list = self.bot.config.get('whitelist_servers', [])

        return serverid not in bl_list and (not wl_enabled or serverid in wl_list)


class ServersList(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'serverslist'
        self.category = categories.SETTINGS
        self.bot_owner_only = True

    async def handle(self, cmd):
        if len(self.bot.servers) == 0:
            await cmd.answer('$[serverslist-none]')
            return

        await cmd.answer('$[serverslist-msg]', locales={'amount': len(self.bot.servers)})

        resp_list = ''
        for server in self.bot.servers:
            item = '- {} ({})'.format(server.name, server.id)
            if server.default_channel is not None:
                item += ' -> ' + server.default_channel.mention

            if len('{}\n{}'.format(resp_list, item)) > 2000:
                await cmd.answer(Embed(description=resp_list), withname=False)
                resp_list = ''
            else:
                resp_list = '{}\n{}'.format(resp_list, item)

        # Send remaining list
        if resp_list != '':
            await cmd.answer(Embed(description=resp_list), withname=False)
