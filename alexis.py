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
__version__ = '1.0.0-dev.2'
__status__ = "Desarrollo"


class Alexis(discord.Client):
    """Contiene al bot e inicializa su funcionamiento."""
    def __init__(self, **options):
        super().__init__(**options)
        self.http_session = aiohttp.ClientSession(loop=self.loop)
        self.sv_config = ServerConfigMgr()

        self.log = logger.get_logger('Alexis')
        self.initialized = False
        self.config = {}
        self.sharedcfg = {}
        self.cmds = {}
        self.cmd_instances = []
        self.swhandlers = {}
        self.pre_handlers = []
        self.mention_handlers = []
        self.config_handlers = {}
        self.config_defaults = {}

        self.db = peewee.SqliteDatabase('database.db')
        self.db.connect()

        self.load_config()

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

        # Cargar (instanciar clases de) comandos
        self.log.debug('Cargando comandos...')

        # Si mal no me equivoco, aquí no se puede hacer list comprehension
        self.cmd_instances = [f(self) for f in modules.commands.classes]
        db_models = []

        for cmd in modules.commands.classes:
            self.cmd_instances.append(cmd(self))

        # Guardar instancias de módulos de comandos
        for i in self.cmd_instances:
            db_models += i.db_models

            # Comandos
            for name in [i.name] + i.aliases:
                if name != '':
                    self.cmds[name] = i

            # Handlers startswith
            if isinstance(i.swhandler, str) or isinstance(i.swhandler, list):
                swh = [i.swhandler] if isinstance(i.swhandler, str) else i.swhandler
                for swtext in swh:
                    if swtext == '':
                        continue

                    if swtext not in self.swhandlers:
                        self.swhandlers[swtext] = []

                    self.swhandlers[swtext].append(i)

            # Comandos que se activan con una mención
            if isinstance(i.mention_handler, bool) and i.mention_handler:
                self.mention_handlers.append(i)

            # Call task
            if callable(getattr(i, 'task', None)):
                self.loop.create_task(i.task())

            for conf_name, default_val in i.configurations.items():
                if conf_name not in self.config_handlers:
                    self.config_handlers[conf_name] = i.config_handler
                    self.config_defaults[conf_name] = default_val

        self.log.info('Inicializando base de datos...')
        self.db.create_tables(db_models, True)

        self.log.debug('Comandos cargados: ' + ', '.join(self.cmds.keys()))
        self.log.info('Conectando...')

        try:
            self.run(self.config['token'])
        except Exception as ex:
            self.log.exception(ex)
            raise

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

    async def send_message(self, destination, content=None, **kwargs):
        svid = destination.server.id if isinstance(destination, discord.Channel) else 'PM?'
        dest_str = destination.id if isinstance(destination, discord.Object) else str(destination)
        msg = 'Sending message "{}" to {}#{}'.format(content, svid, dest_str)
        if isinstance(kwargs.get('embed'), discord.Embed):
            msg += ' (with embed: {})'.format(kwargs.get('embed').to_dict())

        self.log.debug(msg)
        if content is not None:
            content = content.replace('$PX', self.config['command_prefix'])

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
