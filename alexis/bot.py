#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Este módulo contiene al bot y lo ejecuta si se corre el script."""

import platform
import sys
import aiohttp
import discord
import re

import alexis.modules
from alexis.configuration import StaticConfig
from alexis.command import Command
from alexis.language import Language, SingleLanguage
from alexis.message_cmd import MessageCmd
from alexis.database import ServerConfigMgr
from alexis.logger import log
from alexis.database import get_database, init_db


class AlexisBot(discord.Client):
    __author__ = 'ibk (github.com/santisteban), makzk (github.com/jkcgs)'
    __license__ = 'MIT'
    __version__ = '1.0.0-dev.34~f10'
    name = 'AlexisBot'

    default_config = {
        'token': '',
        'debug': False,
        'command_prefix': '!',
        'database_url': 'sqlite:///database.db',
        'playing': '!help',
        'bot_owners': ['130324995984326656'],
        'owner_role': 'AlexisMaster',
        'ext_modpath': '',
        'subreddit': [],
        'default_lang': 'es'
    }

    def __init__(self, **options):
        """
        Inicializa la configuración, el log, una sesión aiohttp y atributos de la clase.
        :param options: Las opciones correspondientes de discord.Client
        """
        super().__init__(**options)
        self.sv_config = None
        self.log = log
        self.config = StaticConfig('config.yml')
        self.http_session = aiohttp.ClientSession(
            loop=self.loop, headers={'User-Agent': '{}/{} +discord.cl/pages/alexis'.format(
                AlexisBot.name, AlexisBot.__version__)})

        self.db = None
        self.last_author = None  # El ID del último en enviar un mensaje (omite PM)
        self.initialized = False
        self.pat_self_mention = None

        self.cmds = {}
        self.lang = {}
        self.swhandlers = {}
        self.cmd_instances = []
        self.mention_handlers = []
        self.deleted_messages = []

    def init(self):
        """
        Inicializa la conexión del bot con Discord, además de cargar los módulos y la base de datos
        :return:
        """
        self.log.info('%s v%s, discord.py v%s', AlexisBot.name, AlexisBot.__version__, discord.__version__)
        self.log.info('Python %s en %s.', sys.version.replace('\n', ''), sys.platform)
        self.log.info(platform.uname())
        self.log.info('------')

        # Cargar configuración
        self.load_config()

        if self.config.get('token', '') == '':
            raise RuntimeError('SHOTTO MATTE KUDASAI - ¿Donde está el token para el bot? Agrega el valor "token" a la '
                               'configuración con el token del bot de Discord.')

        # Cargar base de datos
        self.db_connect()
        self.sv_config = ServerConfigMgr()

        # Cargar (instanciar clases de) comandos
        self.log.info('Cargando comandos...')
        self.cmd_instances = [self.load_command(c) for c in alexis.modules.get_mods(self.config.get('ext_modpath', ''))]
        self.log.info('Se cargaron %i módulos', len(self.cmd_instances))
        self.log.debug('Comandos cargados: ' + ', '.join(self.cmds.keys()))

        self._call_handlers_sync('on_loaded', force=True)

        # Conectar con Discord
        try:
            self.log.info('Conectando...')
            self.run(self.config['token'])
        except discord.errors.LoginFailure:
            raise RuntimeError('El token de Discord es incorrecto!')
        except Exception as ex:
            self.log.exception(ex)
            raise

    def load_command(self, cls):
        """
        Carga un módulo de comando en el bot
        :param cls: Clase-módulo a cargar
        :return: La instancia del módulo cargado
        """

        instance = cls(self)
        if len(instance.db_models) > 0:
            self.db.create_tables(instance.db_models, True)

        if isinstance(instance.default_config, dict):
            self.config.load_defaults(instance.default_config)

        # Comandos
        for name in [instance.name] + instance.aliases:
            if name != '':
                self.cmds[name] = instance

        # Handlers startswith
        if isinstance(instance.swhandler, str) or isinstance(instance.swhandler, list):
            swh = [instance.swhandler] if isinstance(instance.swhandler, str) else instance.swhandler
            for swtext in swh:
                if swtext != '':
                    self.log.debug('Registrando sw_handler "%s"', swtext)
                    self.swhandlers[swtext] = instance

        # Comandos que se activan con una mención
        if isinstance(instance.mention_handler, bool) and instance.mention_handler:
            self.mention_handlers.append(instance)

        # Call task
        if callable(getattr(instance, 'task', None)):
            self.loop.create_task(instance.task())

        return instance

    def db_connect(self):
        """
        Ejecuta la conexión a la base de datos
        """
        self.log.info('Conectando con la base de datos...')
        self.db = get_database()
        init_db()
        self.log.info('Conectado correctamente a la base de datos.')
        self.log.info('Clase de base de datos: %s', self.db.__class__.__name__)

    async def on_ready(self):
        """Esto se ejecuta cuando el bot está conectado y listo"""

        self.log.info('Conectado como "%s", ID %s', self.user.name, self.user.id)
        self.log.info('------')
        await self.change_presence(game=discord.Game(name=self.config['playing']))
        self.pat_self_mention = re.compile('^<@!?{}>$'.format(self.user.id))

        self.initialized = True
        await self._call_handlers('on_ready')

    async def send_message(self, destination, content=None, **kwargs):
        """
        Sobrecarga la llamada original de discord.Client para enviar mensajes para accionar otras llamadas
        como handlers de modificación de mensajes y registros del bot. Soporta los mismos parámetros del
        método original.
        :param destination: Dónde enviar un mensaje, como discord.Channel, discord.User, discord.Object, entre otros.
        :param content: El contenido textual a enviar
        :param kwargs: El resto de parámetros del método original.
        :return:
        """
        # Call pre_send_message handlers, append destination
        kwargs = {'destination': destination, 'content': content, **kwargs}
        self._call_handlers_ref('pre_send_message', kwargs)

        # Log the message
        destination = kwargs['destination']
        if getattr(destination, 'server', None) is None:
            dest = '{} (ID: {})'.format(str(destination), destination.id)
        else:
            dest = '{}#{} (IDS {}#{})'.format(destination.server, str(destination), destination.id,
                                              destination.server.id)

        msg = 'Sending message "{}" to {} '.format(kwargs['content'], dest)
        if isinstance(kwargs.get('embed'), discord.Embed):
            msg += ' (with embed: {})'.format(kwargs.get('embed').to_dict())

        self.log.debug(msg)

        # Send the actual message
        return await super(AlexisBot, self).send_message(**kwargs)

    async def delete_message(self, message):
        """
        Elimina un mensaje, y además registra los IDs de los últimos 10 mensajes guardados
        :param message: El mensaje a eliminar
        """
        await super().delete_message(message)
        self.deleted_messages.append(message.id)
        if len(self.deleted_messages) > 10:
            del self.deleted_messages[0]

    def load_config(self):
        """
        Carga la configuración estática y de idioma
        :return: Un valor booleano dependiente del éxito de la carga de los datos.
        """
        try:
            self.log.info('Cargando configuración...')
            self.config.load(AlexisBot.default_config)
            self.lang = Language('lang', default=self.config['default_lang'], autoload=True)
            self.log.info('Configuración cargada')
            return True
        except Exception as ex:
            self.log.exception(ex)
            return False

    def get_lang(self, svid=None):
        """
        Genera una instancia de SingleLanguage para un servidor en específico o con el idioma predeterminado.
        :param svid: El ID del servidor para obtener el idioma. Si es None, se devuelve una instancia con el idioma
        predeterminado.
        :return: La instancia de SingleLanguage con el idioma obtenido.
        """
        if svid is None:
            lang_code = self.config['default_lang']
        else:
            svid = svid if not isinstance(svid, discord.Server) else svid.id
            lang_code = self.sv_config.get(svid, 'lang', self.config['default_lang'])

        return SingleLanguage(self.lang, lang_code)

    async def _call_handlers(self, name, **kwargs):
        if not self.initialized:
            return

        cmd = None
        if name == 'on_message':
            cmd = MessageCmd(kwargs.get('message'), self)

        for x in self._get_handlers('pre_' + name):
            if name == 'on_message':
                y = await x(cmd=cmd, **kwargs)
            else:
                y = await x(**kwargs)

            if y is not None and isinstance(y, bool) and not y:
                return

        if name == 'on_message':
            await Command.message_handler(kwargs.get('message'), self, cmd)

        for z in self._get_handlers(name):
            await z(**kwargs)

    def _call_handlers_sync(self, name, force=False, **kwargs):
        if not self.initialized and not force:
            return

        for z in self._get_handlers(name):
            z(**kwargs)

    def _call_handlers_ref(self, name, kwargs):
        if not self.initialized:
            return

        for z in self._get_handlers(name):
            z(kwargs)

    def _get_handlers(self, name):
        return [getattr(c, name, None) for c in self.cmd_instances if callable(getattr(c, name, None))]

    async def close(self):
        # self.log.debug('Cerrando...')
        super().close()
        await self.http_session.close()
        await self.http.close()

    """
    ===== EVENT HANDLERS =====
    """

    async def on_message(self, message):
        await self._call_handlers('on_message', message=message)

    async def on_reaction_add(self, reaction, user):
        await self._call_handlers('on_reaction_add', reaction=reaction, user=user)

    async def on_reaction_remove(self, reaction, user):
        await self._call_handlers('on_reaction_remove', reaction=reaction, user=user)

    async def on_reaction_clear(self, message, reactions):
        await self._call_handlers('on_reaction_clear', message=message, reactions=reactions)

    async def on_member_join(self, member):
        await self._call_handlers('on_member_join', member=member)

    async def on_member_remove(self, member):
        await self._call_handlers('on_member_remove', member=member)

    async def on_member_update(self, before, after):
        await self._call_handlers('on_member_update', before=before, after=after)

    async def on_message_delete(self, message):
        await self._call_handlers('on_message_delete', message=message)

    async def on_message_edit(self, before, after):
        await self._call_handlers('on_message_edit', before=before, after=after)

    async def on_server_join(self, server):
        await self._call_handlers('on_server_join', server=server)

    async def on_server_remove(self, server):
        await self._call_handlers('on_server_remove', server=server)

    async def on_member_ban(self, member):
        await self._call_handlers('on_member_ban', member=member)

    async def on_member_unban(self, member):
        await self._call_handlers('on_member_unban', member=member)

    async def on_typing(self, channel, user, when):
        await self._call_handlers('on_server_remove', channel=channel, user=user, when=when)
