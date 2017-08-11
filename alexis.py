#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Este módulo contiene al bot y lo ejecuta si se corre el script."""

import platform
import sqlite3
import sys
import random
import re
import yaml
import urllib.parse as urlparse
import logger
import discord
import commands
from cleverwrap import CleverWrap
from models import db, Post, Ban, Redditor, Meme
from tasks import posts_loop

__author__ = 'Nicolás Santisteban, Jonathan Gutiérrez'
__license__ = 'MIT'
__version__ = '0.2.0-dev.2'
__status__ = "Desarrollo"


class Alexis(discord.Client):
    """Contiene al bot e inicializa su funcionamiento."""
    def __init__(self, **options):
        super().__init__(**options)

        self.log = logger.get_logger('Alexis')
        self.initialized = False
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

        # Cargar comandos
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
                if name not in self.cmds:
                    self.cmds[name] = []
                self.cmds[name].append(i)

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
            self.log.info('[PM] %s: %s', author, text)

        if text.startswith('!') and len(text) > 1:
            cmd = text.split(' ')[0][1:]
            if cmd in self.cmds:
                for i in self.cmds[cmd]:
                    i.handle(message)
                return

        # !version
        if text == '!version' or text == '!info':
            info_msg = "```\nAutores: {}\nVersión: {}\nEstado: {}```"
            info_msg = info_msg.format(__author__, __version__, __status__)
            await self.send_message(chan, info_msg)

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
            hearts = ['heart', 'hearts', 'yellow_heart', 'green_heart', 'blue_heart', 'purple_heart']
            if text.strip() == '!f':
                text = "**{}** ha pedido respetos :{}:".format(author, random.choice(hearts))
                await self.send_message(chan, text)
            elif text.startswith('!f ') and len(text) >= 4:
                respects = text[3:]
                text = "**{}** ha pedido respetos por **{}** :{}:".format(author, respects, random.choice(hearts))
                await self.send_message(chan, text)

        # !redditor
        elif text.startswith('!redditor '):
            user = text[10:].split(' ')[0].strip()

            if user.startswith('/u/'):
                user = user[3:]
            if not re.match('^[a-zA-Z0-9_-]*$', user):
                return

            redditor, _ = Redditor.get_or_create(name=user.lower())

            if redditor.posts > 0:
                suffix = 'post' if redditor.posts == 1 else 'posts'
                text = '**/u/{name}** ha creado **{num}** {suffix}.'
                text = text.format(name=user, num=redditor.posts, suffix=suffix)
                await self.send_message(chan, text)
            else:
                text = '**/u/{name}** no ha creado ningún post.'
                text = text.format(name=user)
                await self.send_message(chan, text)

        # !ban (no PM)
        elif text.startswith('!ban '):
            if is_pm:
                await self.send_message(chan, 'banéame esta xd')
                return

            if len(text.split(' ')) > 2 or len(message.mentions) != 1:
                await self.send_message(chan, 'Formato: !ban <mención>')
                return

            mention = message.mentions[0]
            name = self.final_name(mention)

            if not is_owner and self.is_owner(mention, message.server):
                await self.send_message(chan, 'nopo wn no hagai esa wea')
            else:
                # Actualizar id del último que usó un comando (omitir al mismo bot)
                if self.last_author is None or not own_message:
                    self.last_author = message.author.id

                # Evitar que alguien se banee a si mismo
                if self.last_author == mention.id:
                    await self.send_message(chan, 'no hagai trampa po wn xd')
                    return

                if not random.randint(0, 1):
                    text = '¡**{}** se salvo del ban de milagro!'.format(name)
                    await self.send_message(chan, text)
                    return

                user, _ = Ban.get_or_create(user=mention, server=message.server.id)
                update = Ban.update(bans=Ban.bans + 1)
                update = update.where(Ban.user == mention, Ban.server == message.server.id)
                update.execute()

                if user.bans + 1 == 1:
                    text = 'Uff, ¡**{}** se fue baneado por primera vez!'.format(name)
                else:
                    text = '¡**{}** se fue baneado otra vez y registra **{} baneos**!'
                    text = text.format(name, user.bans + 1)
                await self.send_message(chan, text)

        # !bans
        elif text.startswith('!bans '):
            if len(text.split(' ')) > 3 or len(message.mentions) < 1:
                await self.send_message(chan, 'Formato: !bans <mención>')
                return

            if message.mentions:
                mention = message.mentions[0]
                if self.is_owner(mention, message.server):
                    mesg = 'Te voy a decir la cifra exacta: Cuatro mil trescientos cuarenta y '
                    mesg += 'cuatro mil quinientos millones coma cinco bans, ese es el valor.'
                    await self.send_message(chan, mesg)
                    return

                name = mention.nick if mention.nick is not None else mention.name
                user, _ = Ban.get_or_create(user=mention, server=message.server.id)

                mesg = ''
                if user.bans == 0:
                    mesg = "```\nException in thread \"main\" java.lang.NullPointerException\n"
                    mesg += "    at AlexisBot.main(AlexisBot.java:34)\n```"
                else:
                    word = 'ban' if user.bans == 1 else 'bans'
                    if user.bans == 2:
                        word = '~~papás~~ bans'

                    mesg = '**{}** tiene {} {}'.format(name, user.bans, word)

                await self.send_message(chan, mesg)

        # !setbans
        elif text.startswith('!setbans '):
            if not is_owner:
                await self.send_message(chan, 'USUARIO NO AUTORIZADO, ACCESO DENEGADO')
                return

            args = text.split(' ')
            is_valid = not (len(args) < 3 or len(message.mentions) < 1)
            num_bans = 0

            try:
                num_bans = int(args[2])
            except (IndexError, ValueError):
                is_valid = False

            if not is_valid:
                await self.send_message(chan, 'Formato: !setbans <mención> <cantidad>')
                return

            mention = message.mentions[0]
            user, _ = Ban.get_or_create(user=mention, server=message.server.id)
            user.bans = num_bans
            user.save()

            name = self.final_name(mention)
            if user.bans == 0:
                mesg = 'Bans de **{}** reiniciados xd'.format(name)
                await self.send_message(chan, mesg)
            else:
                word = 'ban' if user.bans == 1 else 'bans'
                mesg = '**{}** ahora tiene {} {}'.format(name, user.bans, word)
                await self.send_message(chan, mesg)

        # !banrank
        elif text == '!banrank' or text == '!!banrank':
            bans = Ban.select().where(Ban.server == chan.server.id).order_by(Ban.bans.desc())
            banlist = []
            limit = 10 if text == '!!banrank' else 5

            i = 1
            for item in bans.iterator():
                banlist.append('{}. {}: {}'.format(i, item.user, item.bans))

                i += 1
                if i > limit:
                    break

            if len(banlist) == 0:
                await self.send_message(chan, 'No hay bans registrados')
                return

            mesg = 'Ranking de bans:\n```\n{}\n```'.format('\n'.join(banlist))
            await self.send_message(chan, mesg)

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

        # !set
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

        # !unset
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

        # !list (lista los memes)
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

        # !!list (lista completa de memes)
        elif text == '!!list':
            if not is_owner:
                await self.send_message(chan, 'USUARIO NO AUTORIZADO, ACCESO DENEGADO')
                return

            memelist = []
            for item in Meme.select().iterator():
                memelist.append("- {}: {}".format(item.name, item.content))

            num_memes = len(memelist)
            if num_memes == 0:
                await self.send_message(chan, 'No hay valores disponibles')
                return

            word = 'valor' if num_memes == 1 else 'valores'
            resp = 'Hay {} {}:'.format(num_memes, word)
            await self.send_message(chan, resp)

            # Separar lista de memes en mensajes con menos de 2000 carácteres
            resp_list = ''
            for meme in memelist:
                if len('```{}\n{}```'.format(resp_list, meme)) > 2000:
                    await self.send_message(chan, '```{}```'.format(resp_list))
                    resp_list = ''
                else:
                    resp_list = '{}\n{}'.format(resp_list, meme)

            # Enviar lista restante
            if resp_list != '':
                await self.send_message(chan, '```{}```'.format(resp_list))

        elif text.startswith('!altoen '):
            altotext = text[8:].strip()
            if len(altotext) > 25:
                await self.send_message(chan, 'mucho texto, máximo 25 carácteres plix ty')
                return

            altourl = "https://desu.cl/alto.php?size=1000&text=" + urlparse.quote(altotext)
            emb = discord.Embed()
            emb.set_image(url=altourl)
            await self.send_message(chan, embed=emb)

        # !toggleconversation
        elif text == '!toggleconversation':
            if not is_owner:
                await self.send_message(chan, 'USUARIO NO AUTORIZADO, ACCESO DENEGADO')
                return

            self.conversation = not self.conversation
            resp = 'activada' if self.conversation else 'desactivada'
            await self.send_message(chan, 'Conversación {}'.format(resp))

        elif text == '!reload':
            if not is_owner:
                await self.send_message(chan, 'USUARIO NO AUTORIZADO, ACCESO DENEGADO')
                return

            if not self.load_config():
                msg = 'No se pudo recargar la configuración'
            else:
                msg = 'Configuración recargada correctamente'

            await self.send_message(chan, msg)

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
        nick = user.nick
        return nick if nick else user.name


if __name__ == '__main__':
    Alexis().init()
