from discord import Embed

from bot import Command


class ServerWhitelist(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'leaveserver'
        self.bot_owner_only = True

    async def handle(self, cmd):
        if cmd.argc == 0:
            await cmd.answer('formato: $PX$NM <server_id>')
            return

        server = self.bot.get_server(cmd.args[0])
        if server is None:
            await cmd.answer('server no encontrado')
            return

        await self.bot.leave_server(server)
        try:
            await cmd.answer('dejé el server "{}" ({})'.format(server.name, server.id))
        except Exception as e:
            self.log.exception(e)

    async def on_ready(self):
        if not self.bot.config.get('whitelist', False):
            return

        if not self.bot.config.get('whitelist_autoleave', False):
            return

        self.log.debug('estoy en %s servers', len(self.bot.servers))
        wlist = self.bot.config.get('whitelist_servers', [])
        servers = [sv for sv in self.bot.servers if sv.id not in wlist and int(sv.id) not in wlist]
        self.log.debug('%s servers en la whitelist', len(wlist))
        self.log.debug('%s servers que no están en la whitelist', len(servers))
        for server in servers:
            self.log.debug('La guild "%s" (%s) no está en la whitelist, bye bye', server.name, server.id)
            await self.bot.leave_server(server)

    async def on_server_join(self, server):
        if not self.bot.config.get('whitelist', False):
            self.log.debug('whitelist not enabled')
            return

        wlist = self.bot.config.get('whitelist_servers', [])
        wcontact = self.bot.config.get('whitelist_contact', '')

        if server.id in wlist or int(server.id) in wlist:
            self.log.debug('Entré a "%s" (%s) :3', server.name, server.id)
            return

        msg = 'Hola! Gracias por agregarme a esta guild, pero no se me ha permitido ingresar, aún. ' \
              'Para ello, debes entrar a discord.gg/chile y '
        if wcontact == '':
            msg += 'consultar con admin. Saludos!'
        else:
            msg += 'hablar con <@{}>. Saludos!'.format(wcontact)

        if server.default_channel is not None:
            try:
                await self.bot.send_message(server.default_channel, msg)
            except Exception as e:
                self.log.error('No pude enviar un mensaje de despedida a "%s" (%s)'.format(server.name, server.id))
                self.log.exception(e)

        self.log.debug('La guild "%s" (%s) no está en la whitelist, bye bye', server.name, server.id)
        await self.bot.leave_server(server)


class ServersList(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'serverslist'
        self.bot_owner_only = True

    async def handle(self, cmd):
        if len(self.bot.servers) == 0:
            await cmd.answer('no estoy en ningún servidor uwu')
            return

        await cmd.answer('estoy en los siguientes servidores:')

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

        # Enviar lista restante
        if resp_list != '':
            await cmd.answer(Embed(description=resp_list), withname=False)
