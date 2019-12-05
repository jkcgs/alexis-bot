import discord

from discord import Embed

from bot.guild_configuration import GuildConfiguration
from bot.libs.language import SingleLanguage
from bot.utils import no_tags
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
                await self.bot.delete_message(msg)
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

        if isinstance(user, int):
            return await self.bot.fetch_user(user)

        if user.startswith("@"):
            user = user[1:]

        u = self.message.guild.get_member_named(user)
        if u is not None:
            return u

        if pat_usertag.match(user):
            st = 3 if user[2] == '!' else 2
            user = user[st:-1]

        u = self.message.guild.get_member(user)
        if u is not None:
            return u

        if member_only or not pat_snowflake.match(user):
            return None

        return self.bot.get_user(user)

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
        if member.guild.owner == member or member.guild_permissions.administrator:
            return True

        owner_roles = self.config.get('owner_roles', self.bot.config['owner_role'])
        if owner_roles == '':
            owner_roles = []
        else:
            owner_roles = owner_roles.split('\n')

        for role in member.roles:
            if role.id in owner_roles \
                    or role.name in owner_roles \
                    or member.id in owner_roles:
                return True

        return False

    @property
    def prefix(self):
        return self.bot.get_prefix(self.message.channel)

    @property
    def owner(self):
        if self.guild is None:
            return False
        return self.bot.is_guild_owner(self.guild.me)

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
                conf = GuildConfiguration.get_instance(self.guild.id)
                lang_code = conf.get('lang', self.bot.config['default_lang'])
                self._lang = SingleLanguage(self.bot.lang, lang_code)

        return self._lang

    def __str__(self):
        return '[{}  channel="{}#{}" author="{}" text="{}"]'.format(
            self.__class__.__name__, self.message.guild, self.message.channel, self.message.author, self.text)
