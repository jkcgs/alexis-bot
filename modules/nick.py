import discord

from bot import Command


class Nick(Command):
    __version__ = '0.0.1'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'nick'
        self.allow_pm = False
        self.user_delay = 60
        self.default_enabled = False

    async def handle(self, cmd):
        self.log.debug(cmd.permissions.manage_nicknames)
        if not cmd.permissions.manage_nicknames:
            await cmd.answer('I don\'t have permissions to manage nicks in this guild, so this command is disabled.')
            return

        new_nick = '' if cmd.argc == 0 else cmd.text
        if len(cmd.text) > 20:
            await cmd.answer('The nick can\'t have more than 20 characters')
            return

        try:
            await cmd.author.edit(nick=new_nick)
            await cmd.answer('There you go')
        except discord.Forbidden:
            await cmd.answer('I couldn\'t change your nick. You probably have a higher role than me.')
