import discord

from bot import Command
from bot.utils import pat_channel, pat_snowflake, str_to_embed


class BotSendMessage(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'message'
        self.help = 'Envía un mensaje en el nombre del bot'
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, cmd):
        if cmd.argc < 2 or not pat_channel.match(cmd.args[0]):
            await cmd.answer('formato: $CMD <canal> <mensaje>\n'
                             'El formato de *mensaje* es `texto mensaje | titulo | description | imagen | color`')
            return

        chan = self.bot.get_channel(cmd.args[0][2:-1])
        if chan is None or chan.server.id != cmd.server.id:
            await cmd.answer('canal no encontrado')
            return

        try:
            text = ' '.join(cmd.args[1:])
            args = text.split('|')
            embed = None
            if len(args) > 2:
                embed = str_to_embed('|'.join(args[1:]))

            await self.bot.send_message(content=args[0], destination=chan, embed=embed)
        except discord.Forbidden:
            await cmd.answer('no pude enviar el mensaje al canal seleccionado')


class BotEditMessage(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'edit'
        self.help = 'Edita un mensaje enviado por el bot'
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, cmd):
        if cmd.argc < 3 or not pat_channel.match(cmd.args[0]) or not pat_snowflake.match(cmd.args[1]):
            await cmd.answer('formato: $CMD <canal> <id_mensaje> <nuevo_mensaje>\n'
                             'El formato de nuevo_mensaje es `texto mensaje | titulo | description | imagen | color`')
            return

        chan = self.bot.get_channel(cmd.args[0][2:-1])
        if chan is None or chan.server.id != cmd.server.id:
            await cmd.answer('canal no encontrado')
            return

        msg = await self.bot.get_message(chan, cmd.args[1])
        if msg is None:
            await cmd.answer('mensaje no encontrado')
            return

        text = ' '.join(cmd.args[1:])
        args = text.split('|')
        embed = None
        if len(args) > 2:
            embed = str_to_embed('|'.join(args[1:]))

        await self.bot.edit_message(msg, args[0], embed=embed)
