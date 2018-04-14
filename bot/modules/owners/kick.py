import re

import discord

from bot import Command

pat_mention = re.compile('^<@!?[0-9]+>$')


class Kick(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'kick'
        self.help = 'Kickea a un usuario'
        self.allow_pm = False
        self.owner_only = True

    async def handle(self, cmd):
        if cmd.argc < 1:
            await cmd.answer('formato: $PX$NM @usuario [razón]')
            return

        to_kick = await cmd.get_user(cmd.args[0])
        if to_kick is None:
            await cmd.answer('usuario no encontrado')
            return

        msg_user = 'Lamentablemente has sido kickeado de {}'.format(cmd.message.server.name)
        msg_all = '{} ha sido kickead@ del servidor'.format(to_kick.display_name)
        if cmd.argc > 1:
            reason = ' '.join(cmd.args[1:])
            msg_user += ' `por **{}**'.format(reason)
            msg_all += ' `por **{}**'.format(reason)

        # Kickear al usuario
        try:
            await self.bot.kick(to_kick)
        except discord.Forbidden:
            await cmd.answer('no pude kickear al usuario :cry:')
            return

        # Avisar al usuario (no bots) que fue kickeado
        try:
            if not to_kick.bot:
                await self.bot.send_message(to_kick, msg_user)
        except discord.Forbidden:
            pass

        # all iz well
        await cmd.answer(msg_all)
        # await ModLog.send_modlog(cmd, message=msg_all)
