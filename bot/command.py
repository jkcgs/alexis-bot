import asyncio
import aiohttp
import traceback
import discord

from . import SingleLanguage
from .logger import log
from .events import CommandEvent, BotMentionEvent
from .libs.configuration import ServerConfiguration


class Command:
    def __init__(self, bot):
        self.bot = bot
        self.log = log
        self.name = ''
        self.aliases = []
        self.swhandler = []
        self.swhandler_break = False
        self.mention_handler = False
        self.help = '$[missing-help]'
        self.allow_pm = True
        self.allow_nsfw = True  # TODO
        self.nsfw_only = False  # TODO
        self.pm_error = '$[disallowed-via-pm]'
        self.bot_owner_only = False
        self.owner_only = False
        self.owner_error = 'no puedes usar este comando'
        self.format = ''  # TODO
        self.default_enabled = True
        self.default_config = None

        self.user_delay = 0
        self.users_delay = {}
        self.user_delay_error = 'aún no puedes usar este comando'
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
        Genera una instancia de SingleLanguage para un servidor en específico o con el idioma predeterminado.
        :param svid: El ID del servidor para obtener el idioma. Si es None, se devuelve una instancia con el idioma
        predeterminado.
        :return: La instancia de SingleLanguage con el idioma obtenido.
        """
        if svid is None:
            lang_code = self.bot.config['default_lang']
        else:
            svid = svid if not isinstance(svid, discord.Server) else svid.id
            lang_code = self.bot.sv_config.get(svid, 'lang', self.bot.config['default_lang'])

        return SingleLanguage(self.bot.lang, lang_code)


async def message_handler(message, bot, event):
    if not bot.initialized:
        return

    # Mandar PMs al log
    if event.is_pm and message.content != '':
        if event.self:
            log.info('[PM] (-> %s): %s', message.channel.user, event.text)
        else:
            log.info('[PM] %s: %s', event.author, event.text)

    # Command handler
    try:
        # Comando válido
        if isinstance(event, (CommandEvent, BotMentionEvent)):
            if isinstance(event, CommandEvent):
                # Actualizar id del último que usó un comando (omitir al mismo bot)
                if not event.self:
                    bot.last_author = message.author.id
                log.debug('[command] %s: %s', event.author, str(event))

            event.handle()

        # 'startswith' handlers
        for swtext in bot.manager.swhandlers.keys():
            swtextrep = swtext.replace('$PX', event.prefix)
            if message.content.startswith(swtextrep):
                swhandler = bot.manager.swhandlers[swtext]
                if swhandler.bot_owner_only and not event.bot_owner:
                    continue
                if swhandler.owner_only and not (event.owner or event.bot_owner):
                    continue
                if not swhandler.allow_pm and event.is_pm:
                    continue

                await swhandler.handle(event)
                if swhandler.swhandler_break:
                    break

    except Exception as e:
        if str(e) == 'BAD REQUEST (status code: 400)':
            e = Exception('Command failed successfully')

        if bot.config['debug']:
            await event.answer('ALGO PASÓ OwO\n```{}```'.format(traceback.format_exc()))
        else:
            await event.answer('ocurr.. 1.error c0n\'el$##com@nd..\n```{}```'.format(str(e)))
        log.exception(e)
