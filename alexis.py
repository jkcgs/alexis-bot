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
from models import db, Post, Ban, Redditor, Meme
from tasks import posts_loop

__author__ = 'Nicolás Santisteban, Jonathan Gutiérrez'
__license__ = 'MIT'
__version__ = '0.1.4-dev'
__status__ = "Desarrollo"


class Alexis(discord.Client):
    """Contiene al bot e inicializa su funcionamiento."""
    def __init__(self, **options):
        super().__init__(**options)

        self.log = logger.get_logger('Alexis')

        db.connect()
        db.create_tables([Post, Ban, Redditor, Meme], True)

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

        if 'default_memes' in self.config and len(self.config['default_memes']) > 0:
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
        is_owner = 'owners' in self.config and message.author.id in self.config['owners']

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
                if 'owners' in self.config and mention.id in self.config['owners']:
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

        # !resetban
        elif text.startswith("!resetban "):
            if not is_owner:
                await self.send_message(chan, 'USUARIO NO AUTORIZADO, ACCESO DENEGADO')
                return

            if len(text.split(' ')) > 2 or len(message.mentions) < 1:
                await self.send_message(chan, 'Formato: !resetban <mención>')
                return

            mention = message.mentions[0]
            user, _ = Ban.get_or_create(user=mention, server=message.server)
            user.bans = 0
            user.save()

            await self.send_message(chan, 'Bans reiniciados xd')

        # !redditor
        elif text.startswith('!redditor '):
            user = text[10:].split(' ')[0].lower().strip()

            if user.startswith('/u/'):
                user = user[3:]
            if not re.match('^[a-zA-Z0-9_-]*$', user):
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

        # ! <meme> | ¡<meme>
        elif text.startswith('! ') or text.startswith('¡'):
            meme_query = ''
            if text.startswith('! '):
                meme_query = text[2:]
            else:
                meme_query = text[1:]

            try:
                meme = Meme.get(Meme.name == meme_query)
                await self.send_message(chan, meme.content)
            except Meme.DoesNotExist:
                pass

        elif text.startswith('!set '):
            meme_query = text[5:].strip().split(' ')

            if not is_owner:
                await self.send_message(chan, 'USUARIO NO AUTORIZADO, ACCESO DENEGADO')
                return

            if len(meme_query) < 2:
                await self.send_message(chan, 'Formato: !set <nombre> <contenido>')
                return

            meme_name = meme_query[0].strip()
            meme_cont = ' '.join(meme_query[1:]).strip()
            meme, created = Meme.get_or_create(name=meme_name)
            meme.content = meme_cont
            meme.save()

            if created:
                msg = 'Valor **{name}** creado'.format(name=meme_name)
                self.log.info('Meme %s creado con valor: "%s"', meme_name, meme_cont)
            else:
                msg = 'Valor **{name}** actualizado'.format(name=meme_name)
                self.log.info('Meme %s actualizado a: "%s"', meme_name, meme_cont)

            await self.send_message(chan, msg)

        elif text.startswith('!unset '):
            meme_name = text[7:].strip()

            if not is_owner:
                await self.send_message(chan, 'USUARIO NO AUTORIZADO, ACCESO DENEGADO')
                return

            if meme_name == "":
                await self.send_message(chan, 'Formato: !unset <nombre>')
                return

            try:
                meme = Meme.get(name=meme_name)
                meme.delete_instance()
                msg = 'Valor **{name}** eliminado'.format(name=meme_name)
                await self.send_message(chan, msg)
                self.log.info('Meme %s eliminado', meme_name)
            except Meme.DoesNotExist:
                msg = 'El valor con nombre {name} no existe'.format(name=meme_name)
                await self.send_message(chan, msg)
        
        elif text == '!list':
            if not is_owner:
                await self.send_message(chan, 'USUARIO NO AUTORIZADO, ACCESO DENEGADO')
                return
            
            namelist = []
            for item in Meme.select().iterator():
                namelist.append(item.name)

            word = 'valor' if len(namelist) == 1 else 'valores'
            resp = 'Hay {} {}: {}'.format(len(namelist), word, ', '.join(namelist))
            await self.send_message(chan, resp)

if __name__ == '__main__':
    Alexis().init()
