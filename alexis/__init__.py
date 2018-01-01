#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Este módulo contiene al bot y lo ejecuta si se corre el script."""

import platform
import sqlite3
import sys

import aiohttp
import discord
import peewee
import re

import alexis.modules
from alexis import logger
from alexis.base.command import Command
from alexis.base.configuration import StaticConfig
from alexis.base.database import ServerConfigMgr
from alexis.base.message_cmd import MessageCmd


class Alexis(discord.Client):
    __author__ = 'Nicolás Santisteban, Jonathan Gutiérrez'
    __license__ = 'MIT'
    __version__ = '1.0.0-dev.14'

    def __init__(self, **options):
        """
        Inicializa la configuración, el log, una sesión aiohttp y atributos de la clase.
        :param options: Las opciones correspondientes de discord.Client
        """
        super().__init__(**options)
        self.sv_config = None
        self.log = logger.get_logger('Alexis')
        self.config = StaticConfig('config.yml')
        self.http_session = aiohttp.ClientSession(
            loop=self.loop, headers={'User-Agent': 'AlexisBot/' + Alexis.__version__})

        self.db = None
        self.last_author = None  # El ID del último en enviar un mensaje (omite PM)
        self.initialized = False
        self.pat_self_mention = None

        self.cmds = {}
        self.swhandlers = {}
        self.cmd_instances = []
        self.mention_handlers = []

    def init(self):
        """
        Inicializa la conexión del bot con Discord, además de cargar los módulos y la base de datos
        :return:
        """
        self.log.info('alexis-bot v%s.', Alexis.__version__)
        self.log.info('Python %s en %s.', sys.version, sys.platform)
        self.log.info(platform.uname())
        self.log.info('Soporte SQLite3 para versión %s.', sqlite3.sqlite_version)
        self.log.info('discord.py versión %s.', discord.__version__)
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
        self.log.debug('Cargando comandos...')
        self.cmd_instances = [self.load_command(c) for c in alexis.modules.get_mods(self.config.get('ext_modpath', ''))]
        self.log.debug('Se cargaron %i módulos', len(self.cmd_instances))
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
        self.log.info('Conectando a base de datos...')
        self.db = peewee.SqliteDatabase('database.db')
        self.db.connect()
        self.log.info('Conectado correctamente a la base de datos.')

    """Esto se ejecuta cuando el bot está conectado y listo"""
    async def on_ready(self):
        self.log.info('Conectado como "%s", ID %s', self.user.name, self.user.id)
        self.log.info('------')
        await self.change_presence(game=discord.Game(name=self.config['playing']))
        self.pat_self_mention = re.compile('^<@!?{}>$'.format(self.user.id))

        self.initialized = True
        await self._call_handlers('on_ready')

    async def send_message(self, destination, content=None, **kwargs):
        svid = destination.server.id if isinstance(destination, discord.Channel) else 'PM?'
        dest_str = destination.id if isinstance(destination, discord.Object) else str(destination)
        msg = 'Sending message "{}" to {}#{}'.format(content, svid, dest_str)
        if isinstance(kwargs.get('embed'), discord.Embed):
            msg += ' (with embed: {})'.format(kwargs.get('embed').to_dict())

        self.log.debug(msg)
        await super(Alexis, self).send_message(destination, content, **kwargs)

    def load_config(self):
        try:
            defaults = {
                'token': '',
                'debug': False,
                'command_prefix': '!',
                'playing': '!help',
                'bot_owners': ['130324995984326656'],
                'owner_role': 'AlexisMaster',
                'ext_modpath': '',
                'subreddit': [],
                'default_channel': ''
            }

            self.log.debug('Cargando configuración...')
            self.config.load(defaults)
            self.log.debug('Configuración cargada')
            return True
        except Exception as ex:
            self.log.exception(ex)
            return False

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
