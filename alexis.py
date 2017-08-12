#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Este módulo contiene al bot y lo ejecuta si se corre el script."""

import platform
import sqlite3
import sys
import random
import re
import yaml
import logger
import discord
import commands
from cleverwrap import CleverWrap
from models import db, Post, Ban, Redditor, Meme
from tasks import posts_loop

__author__ = 'Nicolás Santisteban, Jonathan Gutiérrez'
__license__ = 'MIT'
__version__ = '0.3.0-dev.0+refractor'
__status__ = "Desarrollo"


class Alexis(discord.Client):
    """Contiene al bot e inicializa su funcionamiento."""
    def __init__(self, **options):
        super().__init__(**options)

        self.log = logger.get_logger('Alexis')
        self.initialized = False
        self.config = {}
        self.cmds = {}

        db.connect()
        db.create_tables([Post, Ban, Redditor, Meme], True)

        self.load_config()

        self.cbot = CleverWrap(self.config['cleverbot_key'])
        self.cbotcheck = False
        self.conversation = True

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

        # Cargar comandos
        self.log.debug('Cargando comandos...')
        cmd_instances = []
        for cmd in commands.classes:
            cmd_instances.append(cmd(self))

        for i in cmd_instances:
            if isinstance(i.name, list):
                for name in i.name:
                    if name not in self.cmds:
                        self.cmds[name] = []
                    self.cmds[name].append(i)
            elif isinstance(i.name, str):
                if i.name not in self.cmds:
                    self.cmds[i.name] = []
                self.cmds[i.name].append(i)

        self.log.debug('Comandos cargados: ' + ', '.join(self.cmds.keys()))

        # Cleverbot
        self.log.info('Conectando con Cleverbot API...')
        self.cbotcheck = self.cbot.say('test') is not None
        if self.cbotcheck:
            self.log.info('CleverWrap iniciado correctamente.')
        else:
            self.log.warning('El valor "cleverbot_key" ("%s") es inválido.', self.config['cleverbot_key'])

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
        author = self.final_name(message.author)
        chan = message.channel
        is_pm = message.server is None
        is_owner = self.is_owner(message.author, message.server)
        frase = random.choice(self.config['frases'])
        own_message = message.author.id == self.user.id

        # Mandar PMs al log
        if is_pm:
            if own_message:
                self.log.info('[PM] (-> %s): %s', message.channel.user, text)
            else:
                self.log.info('[PM] %s: %s', author, text)

        if text.startswith('!') and len(text) > 1:
            cmd = text.split(' ')[0][1:]
            if cmd in self.cmds:
                self.log.debug('[command] message: "%s" command %s', text, cmd)
                for i in self.cmds[cmd]:
                    if i.owner_only and not is_owner:
                        await self.send_message(chan, i.owner_error)
                    elif not i.allow_pm and is_pm:
                        await self.send_message(chan, i.pm_error)
                    else:
                        await i.handle(message, i.parse(message))
                return

        # !version
        if text == '!version' or text == '!info':
            info_msg = "```\nAutores: {}\nVersión: {}\nEstado: {}```"
            info_msg = info_msg.format(__author__, __version__, __status__)
            await self.send_message(chan, info_msg)

        # ! <meme> | ¡<meme>
        elif text.startswith('! ') or text.startswith('¡'):
            # Actualizar el id de la última persona que usó el comando, omitiendo al mismo bot
            if self.last_author is None or not own_message:
                self.last_author = message.author.id

            meme_query = text[2:] if text.startswith('! ') else text[1:]

            try:
                meme = Meme.get(Meme.name == meme_query)
                await self.send_message(chan, meme.content)
            except Meme.DoesNotExist:
                pass

        # Cleverbot (@bot <mensaje>)
        elif self.rx_mention.match(text) and self.conversation and self.cbotcheck is not None:
            if is_pm:
                return

            msg = self.rx_mention.sub('', text).strip()
            if msg == '':
                reply = '{}\n\n*Si querías decirme algo, dílo de la siguiente forma: <@bot> <texto>*'.format(frase)
            else:
                reply = self.cbot.say(msg)

            await self.send_message(chan, reply)

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

    def final_name(self, user):
        return user.nick if hasattr(user, 'nick') else user.name


if __name__ == '__main__':
    Alexis().init()
