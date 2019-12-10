from datetime import timedelta, datetime

import discord

from bot.utils import serialize_avail, no_tags
from .message_event import MessageEvent


class CommandEvent(MessageEvent):
    def __init__(self, message, bot):
        super().__init__(message, bot)

        # Command definition
        self.allargs = message.content.replace('  ', ' ').split(' ')
        cmd_parts = self.allargs[0][len(self.prefix):].split(':')
        self.cmdname = cmd_parts[0]
        self.subcmd = '' if len(cmd_parts) < 2 else cmd_parts[1]

        # Arguments definition
        self.args = [] if len(self.allargs) == 1 else [f for f in self.allargs[1:] if f.strip() != '']
        self.argc = len(self.args)
        self.text = ' '.join(self.args)

    async def answer(self, content='', to_author=False, withname=False, **kwargs):
        if 'locales' not in kwargs:
            kwargs['locales'] = {}

        kwargs['event'] = self
        return await super().answer(content, to_author, withname, **kwargs)

    def is_enabled(self):
        if self.is_pm:
            return True

        data_db = self.config.get('cmd_status', '')
        avail = serialize_avail(data_db)
        cmd = self.bot.manager[self.cmdname]
        enabled_db = avail.get(cmd.name, '+' if cmd.default_enabled else '-')
        return enabled_db == '+'

    def no_tags(self, users=True, channels=True, emojis=True):
        return no_tags(self.text, self.bot, users, channels, emojis)

    def __str__(self):
        return '[{} name="{}", channel="{}#{}", author="{}" text="{}"]'.format(
            self.__class__.__name__, self.cmdname, self.message.guild,
            self.message.channel, self.message.author, self.text
        )

    async def handle(self):
        cmd = self.bot.manager[self.cmdname]

        # Time and permissions filter
        if (cmd.bot_owner_only and not self.bot_owner) \
                or (cmd.owner_only and not self.owner) \
                or (not cmd.allow_pm and self.is_pm) \
                or (not self.is_pm and not self.is_enabled()):
            return
        elif (cmd.user_delay > 0 and self.author.id in cmd.users_delay
              and cmd.users_delay[self.author.id] + timedelta(0, cmd.user_delay) > datetime.now()
              and not self.owner):
            await self.answer(cmd.user_delay_error)
            return
        elif not self.is_pm and cmd.nsfw_only and not self.channel.is_nsfw():
            await self.answer(cmd.nsfw_only_error)
            return
        else:
            # Run the command
            result = await cmd.handle(self)
            fine = result is None or (isinstance(result, bool) and result)
            if fine and cmd.user_delay > 0:
                cmd.users_delay[self.author.id] = datetime.now()

    def can_manage_roles(self):
        if not isinstance(self.channel, discord.TextChannel):
            return False

        return self.channel.guild.me.guild_permissions.manage_roles

    @staticmethod
    def is_command(message, bot):
        prefix = bot.get_prefix(message.channel)
        if message.content.startswith(prefix):
            cmdname = message.content[len(prefix):].split(' ')[0].split(':')[0]
            return cmdname in bot.manager
        else:
            return False
