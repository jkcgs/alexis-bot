import discord

from discord import Embed

from bot.libs.configuration import ServerConfiguration
from bot.libs.language import SingleLanguage
from bot.utils import is_owner, pat_channel, pat_usertag, pat_snowflake, get_prefix, no_tags


class MessageEvent:
    def __init__(self, message, bot):
        if not isinstance(message, discord.Message):
            raise RuntimeError('message argument is not a discord.Message instance')

        self.bot = bot
        self.message = message
        self.channel = message.channel
        self.author = message.author
        self.author_name = message.author.display_name
        self.is_pm = message.server is None
        self.self = message.author.id == bot.user.id
        self.text = message.content
        self.bot_owner = message.author.id in bot.config['bot_owners']

        self.server = None
        self.config = None
        self._lang = None

        if not self.is_pm:
            self.server = message.server
            self.config = ServerConfiguration(self.bot.sv_config, message.server.id)
        else:
            self.config = ServerConfiguration(self.bot.sv_config, 'all')

    async def answer(self, content='', to_author=False, withname=True, **kwargs):
        """
        Sends a message where the event was created
        :param content: The message content. If it's a discord.Embed, then it's used as the embed parameter.
        :param to_author: If set to True, it's will be sent to the author instead of the event's channel.
        :param withname: Sets if the message will contain the author's name as prefix.
        :param kwargs: Additional parameters to pass to send_message method.
        """
        if isinstance(content, Embed):
            kwargs['embed'] = content
            content = ''

        if 'locales' not in kwargs:
            kwargs['locales'] = {}

        kwargs['event'] = self

        if withname:
            if content != '':
                content = ', ' + content
            content = self.author_name + content

        dest = self.message.author if to_author else self.message.channel
        return await self.bot.send_message(dest, content, **kwargs)

    async def answer_embed(self, msg, title=None, *, delete_trigger=False, withname=True, **kwargs):
        if delete_trigger:
            try:
                await self.bot.delete_message(self.message)
            except discord.Forbidden:
                pass

        if not isinstance(msg, Embed):
            msg = Embed(description=msg)
            if title is not None:
                msg.title = title

        if withname:
            msg.set_footer(text=self.lang.format('$[answer-for]', locales={'author': self.author_name}))

        await self.answer(embed=msg, withname=False, **kwargs)

    async def typing(self):
        """
        Sends the "typing..." status to the event's channel.
        """
        await self.bot.send_typing(self.message.channel)

    def member_by_id(self, user_id):
        """
        (Only for guild messages) Returns the guild member, given an user ID
        :param user_id: The user's ID to lookup.
        :return: The guild's discord.Member. Returns None if it was not found.
        """
        if self.is_pm:
            return None

        for member in self.message.server.members:
            if member.id == user_id:
                return member

        return None

    def is_owner(self, user):
        return is_owner(self.bot, user, self.message.server)

    def no_tags(self, users=True, channels=True, emojis=True):
        return no_tags(self.message, self.bot, users, channels, emojis)

    async def get_user(self, user, member_only=False):
        """
        Fetch a user given a name, mention, it's ID or the user#discriminator string.
        :param user: The user referecence string.
        :param member_only: Guild members only.
        :return: If the event came from a guild, then a discord.Member is returned. Else, a discord.User is returned.
        In any case, if the user could not be found, None is returned.
        """
        if self.is_pm:
            raise RuntimeError('You can\'t get users information on PMs')

        if isinstance(user, discord.Member) or isinstance(user, discord.User):
            return user

        if user.startswith("@"):
            user = user[1:]

        u = self.message.server.get_member_named(user)
        if u is not None:
            return u

        if pat_usertag.match(user):
            st = 3 if user[2] == '!' else 2
            user = user[st:-1]

        u = self.message.server.get_member(user)
        if u is not None:
            return u

        if member_only or not pat_snowflake.match(user):
            return None

        return await self.bot.get_user_info(user)

    def find_channel(self, channel):
        """
        Looks up for a channel given it's name, #name, channel tag or ID, for an event originated from a guild.
        :param channel: The channel reference string
        :return: The discord.Channel. If not found, None is returned.
        """
        if self.is_pm:
            return None

        sv = self.message.server
        if pat_snowflake.match(channel):
            return sv.get_channel(channel)
        elif pat_channel.match(channel):
            return sv.get_channel(channel[2:-1])
        else:
            if channel.startswith('#'):
                channel = channel[1:]

            for chan in sv.channels:
                if chan.name == channel:
                    return chan

        return None

    def lng(self, name, **kwargs):
        return self.lang.get(name, **kwargs)

    @property
    def prefix(self):
        return MessageEvent.get_prefix(self.message, self.bot)

    @property
    def owner(self):
        if self.server is None:
            return False
        return is_owner(self.bot, self.author, self.server)

    @property
    def server_member(self):
        if self.server is None:
            return None
        return self.server.get_member(self.bot.user.id)

    @property
    def permissions(self):
        if self.server is None:
            return None
        return self.server_member.permissions_in(self.channel)

    @property
    def lang(self):
        if self._lang is None:
            if self.server is None:
                self._lang = SingleLanguage(self.bot.lang, self.bot.config['default_lang'])
            else:
                lang_code = self.bot.sv_config.get(self.server.id, 'lang', self.bot.config['default_lang'])
                self._lang = SingleLanguage(self.bot.lang, lang_code)

        return self._lang

    def __str__(self):
        return '[{}  channel="{}#{}" author="{}" text="{}"]'.format(
            self.__class__.__name__, self.message.server, self.message.channel, self.message.author, self.text)

    @staticmethod
    def get_prefix(message, bot):
        return get_prefix(bot, None if message.server is None else message.server.id)
