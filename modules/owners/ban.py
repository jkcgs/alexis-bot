import discord

from bot import Command
from bot.utils import is_int
from bot import categories


class Ban(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'realban'
        self.help = '$[realban-help]'
        self.format = '$[realban-format]'
        self.category = categories.MODERATION
        self.allow_pm = False
        self.owner_only = True

    async def handle(self, cmd):
        if cmd.argc < 1:
            await cmd.answer('$[format]: $[realban-format]')
            return

        await cmd.typing()
        member = await cmd.get_user(cmd.args[0], member_only=True)
        server = cmd.message.server

        if member is None:
            await cmd.answer('$[realban-user-not-found]')
            return

        if member.id == self.bot.user.id:
            await cmd.answer('$[realban-cant-bot]')
            return

        if member.id == cmd.author.id:
            await cmd.answer('$[realban-cant-self]')
            return

        delete_days = 0
        if is_int(cmd.args[1]):
            delete_days = int(cmd.args[1])
            if delete_days < 0 or delete_days > 7:
                await cmd.answer('$[realban-error-days]')
                return
            else:
                reason = ' '.join(cmd.args[2:])
        else:
            reason = ' '.join(cmd.args[1:])

        try:
            await self.bot.ban(member, delete_days)
        except discord.Forbidden:
            await cmd.answer('$[realban-error-denied]')
            return

        # Tell about the ban to the user via PM
        try:
            if reason == '':
                await self.bot.send_message(member, '$[realban-msg]', locales={'server_name': server.name})
            else:
                await self.bot.send_message(member, '$[realban-msg-with-reason]', locales={
                    'server_name': server.name, 'ban_reason': reason
                })
        except discord.errors.Forbidden:
            await cmd.answer('$[realban-error-perms]')

        if reason == '':
            await cmd.answer('$[realban-answer]', locales={'username': member.display_name})
        else:
            await cmd.answer('$[realban-answer-with-reason]', locales={
                'username': member.display_name,
                'ban_reason': reason
            })
