import discord

from bot import Command
from bot.utils import is_int


class Ban(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'realban'
        self.help = 'Banear a un usuario'
        self.allow_pm = False
        self.owner_only = True

    async def handle(self, cmd):
        if cmd.argc < 1:
            await cmd.answer('Formato: $PX$NM <id, mención> [días-eliminar-mensajes (0-7)] [razón]')
            return

        await cmd.typing()
        member = await cmd.get_user(cmd.args[0], member_only=True)
        server = cmd.message.server

        if member is None:
            await cmd.answer('no se encontró al usuario')
            return

        if member.id == self.bot.user.id:
            await cmd.answer('como me vas a banear a mi! owo')
            return

        if member.id == cmd.author.id:
            await cmd.answer('de verdad querías banearte a ti mismo? xd')
            return

        delete_days = 0
        if is_int(cmd.args[1]):
            delete_days = int(cmd.args[1])
            if delete_days < 0 or delete_days > 7:
                await cmd.answer('el tiempo de eliminación de mensajes debe ser entre 0 y 7 (días)')
                return
            else:
                reason = ' '.join(cmd.args[2:])
        else:
            reason = ' '.join(cmd.args[1:])

        try:
            await self.bot.ban(member, delete_days)
        except discord.Forbidden:
            await cmd.answer('no tengo permiso para banear a al usuario!')
            return

        str_reason = ' debido a: **{}**'.format(reason) if reason != '' else ''

        # Enviar PM con el aviso del ban
        try:
            await self.bot.send_message(member, 'Hola! Lamentablemente has sido expulsad@ del servidor **{}**{}.'
                                        .format(server.name, str_reason))
        except discord.errors.Forbidden as e:
            self.log.exception(e)

        # Avisar por el canal donde se envió el comando
        await cmd.answer('**{}** ha sido banead@{}!'.format(member.display_name, str_reason))
