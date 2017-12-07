#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Este módulo contiene al bot y lo ejecuta si se corre el script."""

import platform
import re
import sqlite3
import sys

import aiohttp
import discord
import peewee
import yaml

import modules.commands
from modules import logger
from modules.base.command import Command
from modules.base.database import ServerConfigMgr

__author__ = 'Nicolás Santisteban, Jonathan Gutiérrez'
__license__ = 'MIT'
__version__ = '1.0.0-dev.4'
__status__ = "Desarrollo"


class Alexis(discord.Client):
    """Contiene al bot e inicializa su funcionamiento."""
    def __init__(self, **options):
        super().__init__(**options)
        self.http_session = aiohttp.ClientSession(loop=self.loop)
        self.sv_config = ServerConfigMgr()

        self.db = None
        self.log = logger.get_logger('Alexis')
        self.initialized = False
        self.config = {}
        self.cmds = {}
        self.cmd_instances = []
        self.swhandlers = {}
        self.pre_handlers = []
        self.mention_handlers = []
        self.db_models = []

        # Regex de mención (incluye nicks)
        self.rx_mention = None

        # El ID del último en enviar un mensaje (omite PM)
        self.last_author = None

    """Inicializa al bot"""
    def init(self):
        self.log.info('"Alexis Bot" versión %s de %s.', __version__, __status__.lower())
        self.log.info('Python %s en %s.', sys.version, sys.platform)
        self.log.info(platform.uname())
        self.log.info('Soporte SQLite3 para versión %s.', sqlite3.sqlite_version)
        self.log.info('discord.py versión %s.', discord.__version__)
        self.log.info('------')

        # Cargar configuración
        self.load_config()

        # Cargar base de datos
        self.db_connect()

        # Cargar (instanciar clases de) comandos
        self.log.debug('Cargando comandos...')
        self.cmd_instances = [self.load_command(c) for c in modules.commands.classes]
        self.log.debug('Comandos cargados: ' + ', '.join(self.cmds.keys()))

        self.log.info('Inicializando modelos de bases de datos de comandos...')
        self.db.create_tables(self.db_models, True)

        # Conectar con Discord
        try:
            self.log.info('Conectando...')
            self.run(self.config['token'])
        except Exception as ex:
            self.log.exception(ex)
            raise

    def load_command(self, cls):
        instance = cls(self)
        self.db_models += instance.db_models

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

        self.rx_mention = re.compile('^<@!?{}>'.format(self.user.id))
        self.initialized = True

    """Método ejecutado cada vez que se recibe un mensaje"""
    async def on_message(self, message):
        if not self.initialized:
            return

        await Command.message_handler(message, self)
        await self._call_handlers('on_message', message=message)

    async def on_reaction_add(self, reaction, user):
        await self._call_handlers('on_reaction_add', reaction=reaction, user=user)

    async def on_member_join(self, member):
        await self._call_handlers('on_member_join', member=member)

    async def on_member_remove(self, member):
        await self._call_handlers('on_member_remove', member=member)

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
            with open('config.yml', 'r') as file:
                config = yaml.safe_load(file)

            # Completar info con defaults
            if 'owners' not in config:
                config['owners'] = []
            if 'command_prefix' not in config or not isinstance(config['command_prefix'], str):
                config['command_prefix'] = '!'

            self.config = config
            return True
        except Exception as ex:
            self.log.exception(ex)
            return False

    async def _call_handlers(self, name, **kwargs):
        if not self.initialized:
            return

        for cmd in [getattr(c, name, None) for c in self.cmd_instances if callable(getattr(c, name, None))]:
            await cmd(**kwargs)


if __name__ == '__main__':
    ale = Alexis()
    ale.init()
    ale.http_session.close()
