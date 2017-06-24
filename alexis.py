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
from models import db, Post, Ban, Redditor
from tasks import posts_loop

__author__ = 'Nicolás Santisteban, Jonathan Gutiérrez'
__license__ = 'MIT'
__version__ = '0.1.2-4'
__status__ = "Desarrollo"


class Alexis(discord.Client):
    """Contiene al bot e inicializa su funcionamiento."""
    def __init__(self, **options):
        super().__init__(**options)

        self.log = logger.get_logger('Alexis')

        db.connect()
        db.create_tables([Post, Ban, Redditor], True)

        try:
            with open('config.yml', 'r') as file:
                self.config = yaml.safe_load(file)
        except Exception as ex:
            self.log.exception(ex)
            raise

    def init(self):
        """Inicializa al bot"""
        self.log.info('"Alexis Bot" versión %s de %s.', __version__, __status__)
        self.log.info('Python %s en %s.', sys.version, sys.platform)
        self.log.info(platform.uname())
        self.log.info('Soporte SQLite3 para versión %s.', sqlite3.sqlite_version)
        self.log.info('------')
        self.log.info('Conectando...')

        try:
            self.loop.create_task(posts_loop(self))
            self.run(self.config['token'])
        except Exception as ex:
            self.log.exception(ex)
            raise

    async def on_ready(self):
        """Esto se ejecuta cuando el bot está conectado y listo"""
        self.log.info('Conectado como:')
        self.log.info(self.user.name)
        self.log.info(self.user.id)
        self.log.info('------')
        await self.change_presence(game=discord.Game(name=self.config['playing']))

    async def on_message(self, message):
        """Método ejecutado cada vez que se recibe un mensaje"""
        text = message.content
        author = message.author.name
        chan = message.channel
        is_pm = message.server is None

        # !ping
        #if text == '!ping':
        #    await self.send_message(chan, 'pong!')

        # !version
        if text == '!version' or text == '!info':
            info_msg = "```\nAutores: {}\n\nVersión: {}\n\nEstado: {}```"
            await self.send_message(chan, info_msg.format(__author__, __version__, __status__))

        # !callate
        elif text == '!callate':
            await self.send_message(chan, 'http://i.imgur.com/nZ72crJ.jpg')

        # !choose
        elif text.startswith('!choose '):
            options = text[8:].split("|")
            if len(options) < 2:
                return

            # Validar que no hayan opciones vacías
            for option in options:
                if option.strip() == '':
                    return

            answer = random.choice(options).strip()
            text = 'Yo elijo **{}**'.format(answer)
            await self.send_message(chan, text)

        # !f
        elif text.startswith('!f'):
            if text.strip() == '!f':
                text = "**{}** ha pedido respetos :hearts:".format(author)
                await self.send_message(chan, text)
            elif text.startswith('!f ') and len(text) >= 4:
                respects = text[3:]
                text = "**{}** ha pedido respetos por **{}** :hearts:".format(author, respects)
                await self.send_message(chan, text)

        # !ban (no PM)
        elif text.startswith('!ban '):
            if is_pm:
                await self.send_message(chan, 'me estai weando?')
                return

            for mention in message.mentions:
                if mention.id == "130324995984326656":
                    text = 'nopo wn no hagai esa wea'
                    await self.send_message(chan, text)
                elif random.randint(0, 1):
                    user, _ = Ban.get_or_create(user=mention, server=message.server)
                    update = Ban.update(bans=Ban.bans + 1)
                    update = update.where(Ban.user == mention, Ban.server == message.server)
                    update.execute()

                    if user.bans + 1 == 1:
                        text = 'Uff, ¡**{}** se fue baneado por primera vez!'.format(mention.name)
                    else:
                        text = '¡**{}** se fue baneado otra vez y registra **{} baneos**!'
                        text = text.format(mention.name, user.bans + 1)
                    await self.send_message(chan, text)
                else:
                    text = '¡**{}** se salvo del ban de milagro!'.format(mention.name)
                    await self.send_message(chan, text)

        # !redditor
        elif text.startswith('!redditor '):
            user = text[10:].split(' ')[0].lower().strip()

            if user.startswith('/u/'):
                user = user[3:]
            if not re.match('^[a-zA-Z0-9_]*$', user):
                return

            redditor, _ = Redditor.get_or_create(name=user)

            if redditor.posts > 0:
                suffix = 'post' if redditor.posts == 1 else 'posts'
                text = '**/u/{name}** ha creado **{num}** {suffix}.'
                text = text.format(name=user, num=redditor.posts, suffix=suffix)
                await self.send_message(chan, text)
            else:
                text = '**/u/{name}** no ha creado ningún post.'
                text = text.format(name=user)
                await self.send_message(chan, text)


if __name__ == '__main__':
    Alexis().init()
