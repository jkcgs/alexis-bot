import discord

from discord import Embed

from bot.guild_configuration import GuildConfiguration
from bot.libs.language import SingleLanguage
from bot.utils import no_tags, auto_int
from bot.regex import pat_usertag, pat_channel, pat_snowflake


class MessageEvent:
    def __init__(self, message, bot):
        if not isinstance(message, discord.Message):
            raise RuntimeError('message argument is not a discord.Message instance')

        self.bot = bot
        self.message = message
        self.channel = message.channel
        self.author = message.author
        self.author_name = message.author.display_name
        self.is_pm = isinstance(message.channel, discord.DMChannel)
        self.self = message.author.id == bot.user.id
        self.text = message.content
        self.bot_owner = message.author.id in bot.config['bot_owners']

        self.guild = None if self.is_pm else message.guild
        self.config = GuildConfiguration.get_instance(self.guild)
        self._lang = None

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
                await self.bot.delete_message(self.message, silent=True)
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
        Shortcut method. Sends the "typing..." status to the event's channel.
        """
        await self.channel.trigger_typing()

    def member_by_id(self, user_id):
        """
        (Only for guild messages) Returns the guild member, given an user ID
        :param user_id: The user's ID to lookup.
        :return: The guild's discord.Member. Returns None if it was not found.
        """
        if self.is_pm:
            return None

        for member in self.message.guild.members:
            if member.id == user_id:
                return member

        return None

    def no_tags(self, users=True, channels=True, emojis=True):
        return no_tags(self.message, self.bot, users, channels, emojis)

    def get_member(self, named_or_id):
        """
        Fetch a user given a name, @name, <@user_id> mention, user#discriminator, or it's user [@]ID.
        :param named_or_id: The user referecence string.
        :return: A discord.Member instance or None.
        """
        # There are no members on a private channel
        if self.is_pm:
            raise RuntimeError('You can\'t get users information on PMs')

        # If somehow a member object is passed, return it
        if isinstance(named_or_id, discord.Member):
            return named_or_id

        # Try to convert a tag into an ID, if not, it's probably a user name or nick
        named_or_id = auto_int(str(named_or_id).lstrip('@'))
        if not isinstance(named_or_id, int):
            u_match = pat_usertag.match(named_or_id)
            if u_match:
                named_or_id = auto_int(u_match.group(1))

        # Use the methods according to the variable type
        if isinstance(named_or_id, int):
            return self.guild.get_member(named_or_id)
        else:
            return self.guild.get_member_named(named_or_id)

    def get_member_or_author(self, named_or_id=None):
        """
        This is a shortcut for when a command is user via DM and want to return the author instead
        of a member, because there are no members over PMs.
        :param named_or_id: The user referecence string.
        :return: The message author if it's a PM (parameter is ignored), or a discord.Member instance or None.
        """
        return self.author if self.is_pm else self.get_member(named_or_id)

    def find_channel(self, channel):
        """
        Looks up for a channel given it's name, #name, channel tag or ID, for an event originated from a guild.
        :param channel: The channel reference string
        :return: The discord.Channel. If not found, None is returned.
        """
        if self.is_pm:
            return None

        guild = self.message.guild
        if pat_snowflake.match(channel):
            return guild.get_channel(channel)
        elif pat_channel.match(channel):
            return guild.get_channel(channel[2:-1])
        else:
            if channel.startswith('#'):
                channel = channel[1:]

            for chan in guild.channels:
                if chan.name == channel:
                    return chan

        return None

    def lng(self, name, **kwargs):
        return self.lang.get(name, **kwargs)

    def is_owner(self, member: discord.Member):
        return not self.is_pm and self.bot.is_guild_owner(member)

    @property
    def prefix(self):
        return self.bot.get_prefix(self.message.channel)

    @property
    def owner(self):
        return self.is_owner(self.author)

    @property
    def permissions(self):
        if self.guild is None:
            return None
        return self.guild.me.permissions_in(self.channel)

    @property
    def lang(self):
        if self._lang is None:
            if self.guild is None:
                self._lang = SingleLanguage(self.bot.lang, self.bot.config['default_lang'])
            else:
                conf = GuildConfiguration.get_instance(self.guild)
                lang_code = conf.get('lang', self.bot.config['default_lang'])
                self._lang = SingleLanguage(self.bot.lang, lang_code)

        return self._lang

    def __str__(self):
        return '[{}  channel="{}#{}" author="{}" text="{}"]'.format(
            self.__class__.__name__, self.message.guild, self.message.channel, self.message.author, self.text)
