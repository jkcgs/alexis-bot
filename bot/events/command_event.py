from datetime import timedelta, datetime

import discord

from bot.utils import serialize_avail, no_tags
from .message_event import MessageEvent
from ..lib.guild_configuration import GuildConfiguration
from ..regex import pat_usertag


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

    async def answer(self, content='', withname=None, **kwargs):
        # Set the event to this one
        kwargs['event'] = self
        if withname is None:
            withname = isinstance(content, discord.Embed) or kwargs.get('as_embed', False)
        return await super().answer(content, withname=withname, **kwargs)

    async def send_usage(self, usage=None, **kwargs):
        if usage is None:
            usage = self.command.format

        title = ':information_source: $[cmd-usage]: `$CMD`'
        return await self.answer(usage, title=title, as_embed=True, colour=discord.Colour.light_gray(), **kwargs)

    def is_enabled(self):
        if self.is_pm:
            return True

        data_db = self.config.get('cmd_status', '')
        avail = serialize_avail(data_db)
        cmd = self.bot.manager[self.cmdname]
        enabled_db = avail.get(cmd.name, '+' if cmd.default_enabled else '-')
        return enabled_db == '+'

    def no_tags(self, users=True, channels=True, emojis=True):
        text = self.text
        if users:
            for m in pat_usertag.finditer(text):
                tag, uid = m.group(0), m.group(1)
                user = self.guild.get_member(int(uid))
                text = text.replace(m.group(0), user.display_name if user else '@unknown-user')

        return no_tags(text, self.bot, False, channels, emojis)

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

    @property
    def command(self):
        return self.bot.manager[self.cmdname]

    @staticmethod
    def is_command(message, bot):
        if isinstance(message.channel, discord.DMChannel):
            prefix = bot.config.prefix
        else:
            prefix = GuildConfiguration.get_instance(message.channel.guild).prefix

        if message.content.startswith(prefix):
            cmdname = message.content[len(prefix):].split(' ')[0].split(':')[0]
            return cmdname in bot.manager
        else:
            return False
