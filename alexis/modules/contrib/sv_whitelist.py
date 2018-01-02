import discord

from alexis import Command


class ServerWhitelist(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'leaveserver'
        self.bot_owner_only = True

    async def handle(self, message, cmd):
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

        if server.default_channel is not None:
            try:
                await self.bot.send_message(server.default_channel, msg)
            except Exception as e:
                self.log.error('No pude enviar un mensaje de despedida a "%s" (%s)'.format(server.name, server.id))
                self.log.exception(e)
                pass

        self.log.debug('La guild "%s" (%s) no está en la whitelist, bye bye', server.name, server.id)
        await self.bot.leave_server(server)
