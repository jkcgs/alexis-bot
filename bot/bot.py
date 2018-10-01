import asyncio
import platform
import sys
from datetime import datetime

import discord
from discord import Embed, Server

from bot import Language, StaticConfig, Configuration, Manager
from bot import defaults, init_db, log
from bot.utils import destination_repr, get_bot_root, replace_everywhere


class AlexisBot(discord.Client):
    __author__ = 'ibk (github.com/santisteban), makzk (github.com/jkcgs)'
    __license__ = 'MIT'
    __version__ = '1.0.0-dev.66'
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
        self.start_time = None

        self.lang = {}
        self.deleted_messages = []
        self.deleted_messages_nolog = []

        self.manager = Manager(self)
        self.config = StaticConfig()

    def init(self):
        """
        Carga la configuración, se conecta a la base de datos, y luego se conecta con Discord.
        :return:
        """
        log.info('%s v%s, discord.py v%s', AlexisBot.name, AlexisBot.__version__, discord.__version__)
        log.info('Python %s in %s.', sys.version.replace('\n', ''), sys.platform)
        log.info('Bot root path: %s', get_bot_root())
        log.info(platform.uname())
        log.info('------')

        self.start_time = datetime.now()

        # Cargar configuración
        self.load_config()
        if self.config.get('token', '') == '':
            raise RuntimeError('Discord bot token not defined. It should be in config.yml file.')

        # Cargar base de datos
        log.info('Connecting to the database...')
        self.connect_db()
        self.sv_config = Configuration()

        # Cargar instancias de las clases de comandos cargadas en bots.modules
        log.info('Loading commands...')
        self.manager.load_instances()
        self.manager.dispatch_sync('on_loaded', force=True)

        # Conectar con Discord
        try:
            log.info('Connecting to Discord...')
            self.run(self.config['token'])
        except discord.errors.LoginFailure:
            log.error('Invalid Discord token!')
            raise
        except Exception as ex:
            log.exception(ex)
            raise

    async def on_ready(self):
        """Esto se ejecuta cuando el bot está conectado y listo"""

        log.info('Connected as "%s" (%s)', self.user.name, self.user.id)
        log.info('------')
        await self.change_presence(game=discord.Game(name=self.config['playing']))

        self.initialized = True
        await self.manager.dispatch('on_ready')

    async def send_message(self, destination, content=None, *, tts=False, embed=None, locales=None, event=None):
        """
        Sobrecarga la llamada original de discord.Client para enviar mensajes para accionar otras llamadas
        como handlers de modificación de mensajes y registros del bot. Soporta los mismos parámetros del
        método original.
        :param destination: Dónde enviar un mensaje, como discord.Channel, discord.User, discord.Object, entre otros.
        :param content: El contenido textual a enviar
        :param tts: El mensaje es TTS (text to speech).
        :param embed: Enviar un embed con el mensaje.
        :param locales: Mensajes a reemplazar en el contenido y embed.
        :param event: El evento que origina el mensaje. Se usa para entregárselo a los respectivos handlers.
        :return:
        """

        # Call pre_send_message handlers, append destination
        if locales is None:
            locales = {}

        kwargs = {'destination': destination, 'content': content, 'tts': tts,
                  'embed': embed, 'locales': locales, 'event': event}
        self.manager.dispatch_ref('pre_send_message', kwargs)

        # Log the message
        dest = destination_repr(kwargs['destination'])
        msg = 'Sending message "{}" to {} '.format(kwargs['content'], dest)
        if isinstance(embed, discord.Embed):
            msg += ' (with embed: {})'.format(embed.to_dict())
        log.debug(msg)

        # Send the actual message
        del kwargs['locales'], kwargs['event']
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

    async def delete_message_silent(self, message):
        """
        Elimina un mensaje, y además registra los IDs de los últimos 20 mensajes guardados.
        Adicionalmente, agregará el mensaje a una lista de mensajes que no deben ser logueados, para el correspondiente
        módulo.
        :param message: El mensaje a eliminar
        """

        try:
            self.deleted_messages_nolog.append(message.id)
            await self.delete_message(message)
        except discord.Forbidden as e:
            del self.deleted_messages_nolog[-1]
            raise e

        if len(self.deleted_messages_nolog) > 20:
            del self.deleted_messages_nolog[0]

    async def send_modlog(self, server, message=None, embed=None):
        if not isinstance(server, Server):
            raise RuntimeError('server must be a discord.Server instance')

        if (message is None or message == '') and embed is None:
            raise RuntimeError('message or embed arguments are required')

        if embed is not None and not isinstance(embed, Embed):
            raise RuntimeError('embed must be a discord.Embed instance')

        chanid = self.sv_config.get(server.id, 'join_send_channel')
        if chanid == '':
            return

        chan = self.get_channel(chanid)
        if chan is None:
            log.debug('[modlog] Channel not found (svid %s chanid %s)', server.id, chanid)
            return

        await self.send_message(chan, message, embed=embed)

    def connect_db(self):
        """
        Ejecuta la conexión a la base de datos
        """
        self.db = init_db()
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
            log.exception(ex)
            return False

    def close(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()

        super().close()
        loop.run_until_complete(self.http.close())
        self.manager.cancel_tasks()
        self.manager.close_http()

    async def run_task(self, task, time=0):
        """
        Runs a task on a given interval
        :param task: The task function
        :param time: The time in seconds to repeat the task
        """
        try:
            await task()
        except Exception as e:
            if not isinstance(e, RuntimeError):
                log.exception(e)
        finally:
            await asyncio.sleep(time)

        if not self.is_closed:
            self.schedule(task, time)

    def schedule(self, task, time=0):
        """
        Adds a task to the loop to be run every *time* seconds.
        :param task: The task function
        :param time: The time in seconds to repeat the task
        """
        if time <= 0:
            raise RuntimeError('Task interval time must be positive')

        if not self.is_closed:
            self.loop.create_task(self.run_task(task, time))

    """
    ===== EVENT HANDLERS =====
    """

    async def on_message(self, message):
        await self.manager.dispatch('on_message', message=message)

    async def on_reaction_add(self, reaction, user):
        await self.manager.dispatch('on_reaction_add', reaction=reaction, user=user)

    async def on_reaction_remove(self, reaction, user):
        await self.manager.dispatch('on_reaction_remove', reaction=reaction, user=user)

    async def on_reaction_clear(self, message, reactions):
        await self.manager.dispatch('on_reaction_clear', message=message, reactions=reactions)

    async def on_member_join(self, member):
        await self.manager.dispatch('on_member_join', member=member)

    async def on_member_remove(self, member):
        await self.manager.dispatch('on_member_remove', member=member)

    async def on_member_update(self, before, after):
        await self.manager.dispatch('on_member_update', before=before, after=after)

    async def on_message_delete(self, message):
        await self.manager.dispatch('on_message_delete', message=message)

    async def on_message_edit(self, before, after):
        await self.manager.dispatch('on_message_edit', before=before, after=after)

    async def on_server_join(self, server):
        await self.manager.dispatch('on_server_join', server=server)

    async def on_server_remove(self, server):
        await self.manager.dispatch('on_server_remove', server=server)

    async def on_member_ban(self, member):
        await self.manager.dispatch('on_member_ban', member=member)

    async def on_member_unban(self, member):
        await self.manager.dispatch('on_member_unban', member=member)

    async def on_typing(self, channel, user, when):
        await self.manager.dispatch('on_server_remove', channel=channel, user=user, when=when)
