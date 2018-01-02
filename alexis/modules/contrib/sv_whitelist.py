import discord

from alexis import Command


class ServerWhitelist(Command):
    def __init__(self, bot):
        super().__init__(bot)

    async def on_server_join(self, server):
        if not self.bot.config.get('whitelist', False):
            self.log.debug('whitelist not enabled')
            return

        wlist = self.bot.config.get('whitelist_servers', [])
        wcontact = self.bot.config.get('whitelist_contact', '')

        if server.id in wlist:
            self.log.debug('Entré a "%s" (%s) :3', server.name, server.id)
            return

        msg = 'Hola! Gracias por agregarme a esta guild, pero no se me ha permitido ingresar, aún. ' \
              'Para ello, debes entrar a discord.gg/chile y '
        if wcontact == '':
            msg += 'consultar con admin. Saludos!'
        else:
            msg += 'hablar con <@{}>. Saludos!'.format(wcontact)

        try:
            await self.bot.send_message(server.default_channel, msg)
        except discord.Forbidden:
            pass

        self.log.debug('La guild "%s" (%s) no está en la whitelist, bye bye', server.name, server.id)
        await self.bot.leave_server(server)
