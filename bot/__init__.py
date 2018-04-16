#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Este módulo contiene al bot y lo ejecuta si se corre el script."""

import platform
import sys
import aiohttp
import discord
import re

from .libs.configuration import StaticConfig, Configuration, BaseModel
from .libs.language import Language, SingleLanguage
from .message_cmd import MessageCmd
from .command import Command

from .libs.configuration import get_database, init_db
from .command import message_handler
from .logger import log
from . import defaults


class AlexisBot(discord.Client):
    __author__ = 'ibk (github.com/santisteban), makzk (github.com/jkcgs)'
    __license__ = 'MIT'
    __version__ = '1.0.0-dev.51~f34'
    name = 'AlexisBot'

    def __init__(self, **options):
        """
        Inicializa la configuración, el log, una sesión aiohttp y atributos de la clase.
        :param options: Las opciones correspondientes de discord.Client
        """
        super().__init__(**options)

        self.db = None
        self.sv_config = None
        self.last_author = None
        self.initialized = False
        self.pat_self_mention = None
        self.cmds = {}
        self.lang = {}
        self.swhandlers = {}
        self.cmd_instances = []
        self.mention_handlers = []
        self.deleted_messages = []
        self.tasks = []

        self.log = log
        self.config = StaticConfig('config.yml')

        # Cliente HTTP disponible para los módulos
        headers = {'User-Agent': '{}/{} +discord.cl/alexis'.format(AlexisBot.name, AlexisBot.__version__)}
        self.http_session = aiohttp.ClientSession(
            loop=self.loop, headers=headers, cookie_jar=aiohttp.CookieJar(unsafe=True)
        )

    def init(self):
        """
        Carga la configuración, se conecta a la base de datos, y luego se conecta con Discord.
        :return:
        """
        log.info('%s v%s, discord.py v%s', AlexisBot.name, AlexisBot.__version__, discord.__version__)
        log.info('Python %s en %s.', sys.version.replace('\n', ''), sys.platform)
        log.info(platform.uname())
        log.info('------')

        # Cargar configuración
        self.load_config()
        if self.config.get('token', '') == '':
            raise RuntimeError('No se ha definido el tóken de Discord. Debe estar en e')

        # Cargar base de datos
        log.info('Conectando con la base de datos...')
        self.connect_db()
        self.sv_config = Configuration()

        # Cargar instancias de las clases de comandos cargadas en bots.modules
        log.info('Cargando comandos...')
        self.load_instances()

        self._call_handlers_sync('on_loaded', force=True)

        # Conectar con Discord
        try:
            log.info('Conectando...')
            self.run(self.config['token'])
        except discord.errors.LoginFailure:
            raise RuntimeError('El token de Discord es incorrecto!')
        except Exception as ex:
            log.exception(ex)
            raise

    def load_instances(self):
        """Carga las instancias de las clases de comandos cargadas"""
        import modules
        self.cmd_instances = []
        for c in modules.get_mods(self.config.get('ext_modpath', '')):
            self.cmd_instances.append(self.load_command(c))

        log.info('Se cargaron %i módulos', len(self.cmd_instances))
        log.debug('Comandos cargados: ' + ', '.join(self.cmds.keys()))
        log.debug('Módulos cargados: ' + ', '.join([i.__class__.__name__ for i in self.cmd_instances]))

    def unload_instance(self, name):
        """
        Saca de la memoria una instancia de un módulo, desactivando todos sus comandos y event handlers.
        :param name: El nombre del módulo.
        """
        instance = None
        for i in self.cmd_instances:
            if i.__class__.__name__ == name:
                instance = i

        if instance is None:
            return

        log.debug('Desactivando módulo %s...', name)

        # Unload commands
        cmd_names = [n for n in [instance.name] + instance.aliases if n != '']
        for cmd_name in cmd_names:
            if cmd_name not in self.cmds:
                continue
            else:
                del self.cmds[cmd_name]

        # Unload startswith handlers
        for swname in instance.swhandler:
            if swname not in self.swhandlers:
                continue
            else:
                del self.swhandlers[swname]

        # Unload mention handlers
        for mhandler in self.mention_handlers:
            if mhandler.__class__.__name__ == name:
                self.mention_handlers.remove(mhandler)

        # Hackily unload task
        for task in self.tasks:
            if 'coro=<{}.task()'.format(name) in str(task):
                log.debug('Cancelling task %s', str(task))
                task.cancel()
                self.tasks.remove(task)

        # Remove from instances list
        self.cmd_instances.remove(instance)
        log.info('Módulo "%s" desactivado', name)

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
        for swtext in instance.swhandler:
            if swtext != '':
                log.debug('Registrando sw_handler "%s"', swtext)
                self.swhandlers[swtext] = instance

        # Comandos que se activan con una mención
        if isinstance(instance.mention_handler, bool) and instance.mention_handler:
            self.mention_handlers.append(instance)

        # Call task
        if callable(getattr(instance, 'task', None)):
            self.tasks.append(self.loop.create_task(instance.task()))

        return instance

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
        Elimina un mensaje, y además registra los IDs de los últimos 20 mensajes guardados
        :param message: El mensaje a eliminar
        """
        self.deleted_messages.append(message.id)

        try:
            await super().delete_message(message)
        except discord.Forbidden as e:
            del self.deleted_messages[-1]
            raise e

        if len(self.deleted_messages) > 20:
            del self.deleted_messages[0]

    def connect_db(self):
        """
        Ejecuta la conexión a la base de datos
        """
        self.db = get_database()
        init_db()
        log.info('Conectado correctamente a la base de datos mediante %s', self.db.__class__.__name__)

    def load_config(self):
        """
        Carga la configuración estática y de idioma
        :return: Un valor booleano dependiente del éxito de la carga de los datos.
        """
        try:
            log.info('Cargando configuración...')
            self.config.load(defaults.config)
            self.lang = Language('lang', default=self.config['default_lang'], autoload=True)
            log.info('Configuración cargada')
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

    async def close(self):
        super().close()
        await self.http_session.close()
        await self.http.close()

    async def _call_handlers(self, name, **kwargs):
        """
        Llama a funciones "handlers" en los módulos cargados.
        :param name: El nombre del handler
        :param kwargs: Los parámetros del evento
        """
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
            await message_handler(kwargs.get('message'), self, cmd)

        for z in self._get_handlers(name):
            await z(**kwargs)

    def _call_handlers_sync(self, name, force=False, **kwargs):
        """
        Llama a funciones "handlers" en los módulos cargados.
        :param name: El nombre del handler
        :param force: Llamar a los handlers aunque no se haya inicializado al bot
        :param kwargs: Los parámetros del evento
        """
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
