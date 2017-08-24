#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Este módulo contiene al bot y lo ejecuta si se corre el script."""

import platform
import sqlite3
import sys
import re
import yaml
from discord import Embed

import logger
import discord
import commands
from commands.base.command import Command
from models import db, Post, Ban, Redditor, Meme
from tasks import posts_loop

__author__ = 'Nicolás Santisteban, Jonathan Gutiérrez'
__license__ = 'MIT'
__version__ = '0.3.3'
__status__ = "Desarrollo"


class Alexis(discord.Client):
    """Contiene al bot e inicializa su funcionamiento."""
    def __init__(self, **options):
        super().__init__(**options)

        self.log = logger.get_logger('Alexis')
        self.initialized = False
        self.config = {}
        self.sharedcfg = {}
        self.cmds = {}
        self.swhandlers = {}
        self.mention_handlers = []

        db.connect()
        db.create_tables([Post, Ban, Redditor, Meme], True)

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
        cmd_instances = []
        for cmd in commands.classes:
            cmd_instances.append(cmd(self))

        # Guardar instancias de módulos de comandos
        for i in cmd_instances:
            # Comandos
            names = [i.name] if isinstance(i.name, str) else list(i.name)
            for name in names:
                name = name.strip()
                if name == '':
                    continue

                if name not in self.cmds:
                    self.cmds[name] = []

                self.cmds[name].append(i)

            # Handlers startswith
            if isinstance(i.swhandler, str) or isinstance(i.swhandler, list):
                swh = [i.swhandler] if isinstance(i.swhandler, str) else i.swhandler
                for swtext in swh:
                    swtext = swtext.strip()
                    if swtext == '':
                        continue

                    if swtext not in self.swhandlers:
                        self.swhandlers[swtext] = []

                    self.swhandlers[swtext].append(i)

            # Comandos que se activan con una mención
            if isinstance(i.mention_handler, bool) and i.mention_handler:
                self.mention_handlers.append(i)

        self.log.debug('Comandos cargados: ' + ', '.join(self.cmds.keys()))

        # Valores ("memes")
        num_memes = len(self.config['default_memes'])
        if num_memes > 0:
            self.log.info('Inicializando base de datos...')
            for meme_name, meme_cont in self.config['default_memes'].items():
                Meme.get_or_create(name=meme_name, content=meme_cont)

        self.log.info('Conectando...')

        try:
            self.loop.create_task(posts_loop(self))
            self.run(self.config['token'])
        except Exception as ex:
            self.log.exception(ex)
            raise

    """Esto se ejecuta cuando el bot está conectado y listo"""
    async def on_ready(self):
        self.log.info('Conectado como:')
        self.log.info(self.user.name)
        self.log.info(self.user.id)
        self.log.info('------')
        await self.change_presence(game=discord.Game(name=self.config['playing']))

        self.rx_mention = re.compile('^<@!?{}>'.format(self.user.id))
        self.initialized = True

    """Método ejecutado cada vez que se recibe un mensaje"""
    async def on_message(self, message):
        if not self.initialized:
            return

        # Info sobre el mensaje
        text = message.content
        author = Command.final_name(message.author)
        chan = message.channel
        is_pm = message.server is None
        is_owner = self.is_owner(message.author, message.server)
        own_message = message.author.id == self.user.id

        # Mandar PMs al log
        if is_pm:
            if own_message:
                self.log.info('[PM] (-> %s): %s', message.channel.user, text)
            else:
                self.log.info('[PM] %s: %s', author, text)

        # Command handler
        if text.startswith('!') and len(text) > 1:
            cmd = text.split(' ')[0][1:]
            if cmd in self.cmds:
                self.log.debug('[command] %s sent message: "%s" command %s', message.author, text, cmd)
                for i in self.cmds[cmd]:
                    if i.owner_only and not is_owner:
                        await self.send_message(chan, i.owner_error)
                    elif not i.allow_pm and is_pm:
                        await self.send_message(chan, i.pm_error)
                    else:
                        await i.handle(message, i.parse(message))
                return

        # 'startswith' handlers
        for swtext in self.swhandlers.keys():
            if message.content.startswith(swtext):
                for cmd in self.swhandlers[swtext]:
                    if cmd.owner_only and not is_owner:
                        await self.send_message(chan, cmd.owner_error)
                    elif not cmd.allow_pm and is_pm:
                        await self.send_message(chan, cmd.pm_error)
                    else:
                        await cmd.handle(message, cmd.parse(message))

        # Mention handlers
        if self.user.mentioned_in(message):
            for i in self.mention_handlers:
                if i.owner_only and not is_owner:
                    await self.send_message(chan, i.owner_error)
                elif not i.allow_pm and is_pm:
                    await self.send_message(chan, i.pm_error)
                else:
                    await i.handle(message, i.parse(message))

    def load_config(self):
        try:
            with open('config.yml', 'r') as file:
                config = yaml.safe_load(file)

            # Completar info con defaults
            if 'owners' not in config:
                config['owners'] = []
            if 'default_memes' not in config:
                config['default_memes'] = []
            if 'frases' not in config:
                config['frases'] = []

            self.config = config
            return True
        except Exception as ex:
            self.log.exception(ex)
            return False

    def is_owner(self, member, server):
        if server is None:
            return False

        if member.id in self.config['owners']:
            return True

        for role in member.roles:
            owner_role = server.id + "@" + role.id
            if owner_role in self.config['owners']:
                return True

        return False

    async def send_message(self, destination, content=None, **kwargs):
        svid = destination.server.id if destination.server is not None else 'PM'
        msg = 'Sending message "{}" to {}#{}'.format(content, destination, svid)
        if isinstance(kwargs.get('embed'), Embed):
            msg += ' (with embed: {})'.format(kwargs.get('embed').to_dict())

        self.log.debug(msg)
        await super(Alexis, self).send_message(destination, content, **kwargs)


if __name__ == '__main__':
    Alexis().init()
