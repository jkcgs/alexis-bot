import asyncio
import aiohttp
import discord

from . import SingleLanguage
from .logger import log, TaggedLogger
from .libs.configuration import ServerConfiguration
from . import categories


class Command:
    def __init__(self, bot):
        self.bot = bot
        self.log = TaggedLogger(log, self.__class__.__name__)
        self.name = ''
        self.aliases = []
        self.swhandler = []
        self.swhandler_break = False
        self.mention_handler = False
        self.help = '$[help-not-available]'
        self.pm_error = '$[disallowed-via-pm]'
        self.owner_error = '$[command-not-authorized]'
        self.format = '$[help-format-not-available]'
        self.category = categories.OTHER
        self.allow_pm = True
        self.nsfw_only = False
        self.bot_owner_only = False
        self.owner_only = False
        self.default_enabled = True
        self.default_config = None
        self.priority = 100

        self.user_delay = 0
        self.users_delay = {}
        self.user_delay_error = '$[command-delayed]'
        self.nsfw_only_error = '$[nsfw-only]'
        self.db_models = []
        self.schedule = []

        headers = {'User-Agent': '{}/{} +discord.cl/alexis'.format(bot.__class__.name, bot.__class__.__version__)}
        self.http = aiohttp.ClientSession(
            loop=asyncio.get_event_loop(), headers=headers, cookie_jar=aiohttp.CookieJar(unsafe=True)
        )

    def can_manage_roles(self, server):
        self_member = server.get_member(self.bot.user.id)
        return self_member.server_permissions.manage_roles

    def config_mgr(self, serverid):
        return ServerConfiguration(self.bot.sv_config, serverid)

    def right_cmd(self, cmd):
        return cmd.is_cmd and cmd.cmdname == self.name or cmd.cmdname in self.aliases

    def handle(self, cmd):
        pass

    def get_lang(self, svid=None, channel=None):
        """
        Creates a SingleLanguage instance for a specific server or server channel or default language.
        :param svid: The discord.Server instance or server ID to get the language.
        If it's None, the default language is used.
        :param channel: The channel ID or instance to get channel-specific language.
        If not set, the server language is used.
        :return: The SingleLanguage instance with the determined language.
        """
        lang_code = self.bot.config['default_lang']

        if svid is not None and isinstance(svid, (discord.Server, str)):

            svid = svid if not isinstance(svid, discord.Server) else svid.id
            lang_code = self.bot.sv_config.get(svid, 'lang', self.bot.config['default_lang'], create=False)

            if channel is not None and isinstance(channel, (discord.Channel, str)):
                chanid = channel if not isinstance(channel, discord.Channel) else channel.id
                lang_code = self.bot.sv_config.get(svid, 'lang#'+chanid, lang_code, create=False)

        return SingleLanguage(self.bot.lang, lang_code)
