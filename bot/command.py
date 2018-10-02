import asyncio
import aiohttp
import discord

from bot.utils import get_prefix
from . import SingleLanguage
from .logger import log
from .libs.configuration import ServerConfiguration
from . import categories


class Command:
    def __init__(self, bot):
        self.bot = bot
        self.log = log
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
        self.allow_nsfw = True  # TODO
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

    def get_lang(self, svid=None):
        """
        Creates a SingleLanguage instance for a server specific or default language.
        :param svid: The server ID to get the language. If it's None, the default language is used.
        :return: The SingleLanguage instance with the determined language.
        """
        if svid is None:
            lang_code = self.bot.config['default_lang']
        else:
            svid = svid if not isinstance(svid, discord.Server) else svid.id
            lang_code = self.bot.sv_config.get(svid, 'lang', self.bot.config['default_lang'])

        return SingleLanguage(self.bot.lang, lang_code)
