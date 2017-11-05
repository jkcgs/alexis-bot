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

from datetime import datetime as dt
from datetime import timedelta

import modules.commands
from modules import logger
from modules.reaction_hook import reaction_hook

__author__ = 'Nicolás Santisteban, Jonathan Gutiérrez'
__license__ = 'MIT'
__version__ = '0.7.0-dev'
__status__ = "Desarrollo"


class Alexis(discord.Client):
    """Contiene al bot e inicializa su funcionamiento."""
    def __init__(self, **options):
        super().__init__(**options)
        self.http_session = aiohttp.ClientSession(loop=self.loop)

        self.log = logger.get_logger('Alexis')
        self.initialized = False
        self.config = {}
        self.sharedcfg = {}
        self.cmds = {}
        self.cmd_instances = []
        self.swhandlers = {}
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
        db_models = []

        for cmd in modules.commands.classes:
            self.cmd_instances.append(cmd(self))

        # Guardar instancias de módulos de comandos
        for i in self.cmd_instances:
            db_models += i.db_models

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
                    swtext = swtext
                    if swtext == '':
                        continue

                    if swtext not in self.swhandlers:
                        self.swhandlers[swtext] = []

                    self.swhandlers[swtext].append(i)

            # Comandos que se activan con una mención
            if isinstance(i.mention_handler, bool) and i.mention_handler:
                self.mention_handlers.append(i)

            # Tasks
            if i.run_task:
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

        # Info sobre el mensaje
        text = message.content
        author = message.author.display_name
        chan = message.channel
        is_pm = message.server is None
        is_owner = self.is_owner(message.author, message.server)
        author_id = message.author.id
        own_message = author_id == self.user.id

        # Mandar PMs al log
        if is_pm:
            if own_message:
                self.log.info('[PM] (-> %s): %s', message.channel.user, text)
            else:
                self.log.info('[PM] %s: %s', author, text)

        # Command handler
        if text.startswith(self.config['command_prefix']) and len(text) > 1:
            try:
                cmd = text.split(' ')[0][1:]
                if cmd in self.cmds:
                    # Si es posible, revisar que el canal no ha sido bloqueado
                    if not is_pm and not is_owner and 'lockbot' in self.cmds:
                        lbinstance = self.cmds['lockbot'][0]
                        lbname = lbinstance.name
                        lbnames = [lbname] if isinstance(lbname, str) else lbname
                        if cmd not in lbname and lbinstance.is_locked(message.server.id, chan.id):
                            return

                    self.log.debug('[command] %s sent message: "%s" command %s', message.author, text, cmd)
                    for i in self.cmds[cmd]:
                        if i.owner_only and not is_owner:
                            await self.send_message(chan, i.owner_error)
                        elif not i.allow_pm and is_pm:
                            await self.send_message(chan, i.pm_error)
                        elif i.user_delay > 0 and author_id in i.users_delay \
                                and i.users_delay[author_id] + timedelta(0, i.user_delay) > dt.now() \
                                and not is_owner:
                            await self.send_message(chan, i.user_delay_error)
                        else:
                            i.users_delay[author_id] = dt.now()
                            await i.handle(message, i.parse(message))
                    return
            except Exception as e:
                await self.send_message(chan, 'ocurr.. 1.error c0n\'el$##com@nd..\n```{}```'.format(str(e)))
                self.log.exception(e)

        # 'startswith' handlers
        swbreak = False
        for swtext in self.swhandlers.keys():
            if swbreak:
                break

            if message.content.startswith(swtext):
                self.log.debug('[sw] %s sent message: "%s" handler "%s"', message.author, text, swtext)
                for cmd in self.swhandlers[swtext]:
                    if cmd.owner_only and not is_owner:
                        await self.send_message(chan, cmd.owner_error)
                    elif not cmd.allow_pm and is_pm:
                        await self.send_message(chan, cmd.pm_error)
                    else:
                        await cmd.handle(message, cmd.parse(message))

                    if cmd.swhandler_break:
                        swbreak = True
                        break

        # Mention handlers
        if self.user.mentioned_in(message):
            for i in self.mention_handlers:
                if i.owner_only and not is_owner:
                    await self.send_message(chan, i.owner_error)
                elif not i.allow_pm and is_pm:
                    await self.send_message(chan, i.pm_error)
                else:
                    await i.handle(message, i.parse(message))

    """Esta función es llamada cuando un mensaje recibe una reacción"""
    async def on_reaction_add(self, reaction, user):
        await reaction_hook(self, reaction, user)

    async def on_member_join(self, member):
        for cmd in self.cmd_instances:
            await cmd.on_member_join(member)

    def load_config(self):
        try:
            with open('config.yml', 'r') as file:
                config = yaml.safe_load(file)

            # Completar info con defaults
            if 'owners' not in config:
                config['owners'] = []
            if 'starboard_reactions' not in config or not isinstance(config['starboard_reactions'], int):
                config['starboard_reactions'] = 5
            if 'command_prefix' not in config or not isinstance(config['command_prefix'], str):
                config['command_prefix'] = '!'

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
        svid = destination.server.id if isinstance(destination, discord.Channel) else 'PM?'
        msg = 'Sending message "{}" to {}#{}'.format(content, svid, destination)
        if isinstance(kwargs.get('embed'), discord.Embed):
            msg += ' (with embed: {})'.format(kwargs.get('embed').to_dict())

        self.log.debug(msg)
        await super(Alexis, self).send_message(destination, content, **kwargs)


if __name__ == '__main__':
    ale = Alexis()
    ale.init()
    ale.http_session.close()
