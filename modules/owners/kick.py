import re

import discord

from bot import Command, categories

pat_mention = re.compile('^<@!?[0-9]+>$')


class Kick(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'kick'
        self.help = '$[kick-help]'
        self.format = '$[kick-format]'
        self.allow_pm = False
        self.owner_only = True
        self.category = categories.MODERATION

    async def handle(self, cmd):
        if cmd.argc < 1:
            await cmd.answer('$[format]: $[kick-format]')
            return

        to_kick = await cmd.get_user(cmd.args[0])
        if to_kick is None:
            await cmd.answer('$[user-not-found]')
            return

        # Kickear al usuario
        try:
            await self.bot.kick(to_kick)
        except discord.Forbidden:
            await cmd.answer('no pude kickear al usuario :cry:')
            return

        reason = ' '.join(cmd.args[1:]) if cmd.argc > 1 else ''

        # Avisar al usuario (no bots) que fue kickeado
        try:
            if not to_kick.bot:
                if reason:
                    await self.bot.send_message(to_kick, '$[kick-msg-reason]', locales={'reason': reason})
                else:
                    await self.bot.send_message(to_kick, '$[kick-msg]')
            else:
                await cmd.answer('$[kick-err-bot]')
                return
        except discord.Forbidden:
            pass

        # all iz well
        if reason:
            await cmd.answer('$[kick-answer-reason]', locales={'username': to_kick.display_name, 'reason': reason})
        else:
            await cmd.answer('$[kick-answer]', locales={'username': to_kick.display_name})

        # await ModLog.send_modlog(cmd, message=msg_all)
