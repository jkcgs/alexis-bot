import asyncio
import platform
import sys
from datetime import datetime

import discord

from bot import Language, Manager, constants
from bot.lib.guild_configuration import GuildConfiguration
from bot.database import BotDatabase
from bot.lib.configuration import BotConfiguration
from bot.logger import new_logger
from bot.utils import auto_int

log = new_logger('Core')


class AlexisBot(discord.Client):
    __author__ = 'makzk (github.com/jkcgs)'
    __license__ = 'MIT'
    __version__ = constants.BOT_VERSION
    name = 'AlexisBot'

    def __init__(self, **options):
        """
        Initializes configuration, logging, an aiohttp session and class attributes.
        :param options: The discord.Client options
        """
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(**options, intents=intents)

        self.db = None
        self.initialized = False
        self.start_time = datetime.now()
        self.connect_delta = None

        self.lang = {}
        self.deleted_messages = []
        self.deleted_messages_nolog = []

        self.manager = Manager(self)
        self.config = None
        self.loop = asyncio.get_event_loop()

        # Dinamically create and override event handler methods
        from bot.constants import EVENT_HANDLERS
        for method, margs in EVENT_HANDLERS.items():
            def make_handler(event_name, event_args):
                async def dispatch(*args):
                    kwargs = dict(zip(event_args, args))
                    await self.manager.dispatch(event_name=event_name, **kwargs)

                return dispatch

            event = 'on_' + method
            setattr(self, event, make_handler(event, margs.copy()))

    def init(self):
        """
        Loads configuration, connects to database, and then connects to Discord.
        """
        log.info('%s v%s, discord.py v%s', AlexisBot.name, AlexisBot.__version__, discord.__version__)
        log.info('Python %s in %s.', sys.version.replace('\n', ''), sys.platform)
        log.info(platform.uname())
        log.info('Bot root path: %s', constants.bot_root)
        log.info('------')

        # Load configuration
        self.load_config()
        if self.config.get('token', '') == '':
            raise RuntimeError('Discord bot token not defined. It should be in config.yml file.')

        # Load languages
        self.load_language()

        # Load database
        log.info('Connecting to the database...')
        self.db = BotDatabase.initialize()
        log.info('Successfully conected to database using %s', self.db.__class__.__name__)

        # Load command classes and instances from bots.modules
        log.info('Loading commands...')
        self.manager.load_instances()
        self.manager.dispatch_sync('on_loaded', force=True)

        # Connect to Discord
        try:
            self.start_time = datetime.now()
            log.info('Connecting to Discord...')
            self.loop.run_until_complete(self.start(self.config['token']))
        except discord.errors.LoginFailure:
            log.error('Invalid Discord token!')
            raise
        except KeyboardInterrupt:
            self.loop.run_until_complete(self.close())
            log.warning('Keyboard interrupt!')
        finally:
            self.loop.close()

    async def on_ready(self):
        """ This is executed once the bot has successfully connected to Discord. """
        self.connect_delta = (datetime.now() - self.start_time).total_seconds()
        log.info('Connected as "%s" (%s)', self.user.name, self.user.id)
        log.info('It took %.3f seconds to connect.', self.connect_delta)
        log.info('------')

        self.initialized = True
        self.manager.create_tasks()
        await self.manager.dispatch('on_ready')

    def load_config(self):
        """
        Loads static configuration
        :return: A boolean depending on the operation's result.
        """
        try:
            log.info('Loading configuration...')
            self.config = BotConfiguration.get_instance()
            log.info('Configuration loaded')
            return True
        except Exception as ex:
            log.exception(ex)
            return False

    def load_language(self):
        """
        Loads language content
        :return: A boolean depending on the operation's result.
        """
        try:
            log.info('Loading language stuff...')
            self.lang = Language('lang', default=self.config['default_lang'], autoload=True)
            log.info('Loaded languages: %s, default: %s', list(self.lang.lib.keys()), self.config['default_lang'])
            return True
        except Exception as ex:
            log.exception(ex)
            return False

    async def close(self):
        """
        Stops tasks, close connections and logout from Discord.
        :return:
        """
        log.debug('Closing stuff...')
        await super().close()

        # Close everything http related
        self.manager.close_http()

        # Stop tasks
        self.manager.cancel_tasks()

    async def send_modlog(self, guild: discord.Guild, message=None, embed: discord.Embed = None,
                          locales=None, logtype=None):
        """
        Sends a message to the modlog channel of a guild, if modlog channel is set, and if the
        logtype is enabled.
        :param guild: The guild to send the modlog message.
        :param message: The message content.
        :param embed: An embed for the message.
        :param locales: Locale variables for language messages.
        :param logtype: The modlog type of the message. Guilds can disable individual modlog types.
        """
        config = GuildConfiguration.get_instance(guild)
        chanid = config.get('join_send_channel')
        if chanid == '':
            return

        if logtype and logtype in config.get_list('logtype_disabled'):
            return

        chan = self.get_channel(auto_int(chanid))
        if chan is None:
            return

        await self.send_message(chan, content=message, embed=embed, locales=locales)

    async def send_message(self, destination, content='', **kwargs):
        """
        Method that proxies all messages sent to Discord, to fire other calls
        like event handlers, message filters and bot logging. Allows original method's parameters.
        :param destination: Where to send the message, must be a discord.abc.Messageable compatible instance.
        :param content: The content of the message to send.
        :return: The message sent
        """

        kwargs['content'] = content
        if not isinstance(destination, discord.abc.Messageable):
            raise RuntimeError('destination must be a discord.abc.Messageable compatible instance')

        # Call pre_send_message handlers, append destination
        self.manager.dispatch_ref('pre_send_message', kwargs)

        # Log the message
        if isinstance(destination, discord.TextChannel):
            destination_repr = '{}#{} (IDS {}#{})'.format(
                destination.guild, str(destination), destination.id, destination.guild.id)
        else:
            destination_repr = str(destination)

        msg = 'Sending message "{}" to {} '.format(kwargs['content'], destination_repr)
        if isinstance(kwargs.get('embed', None), discord.Embed):
            msg += ' (with embed: {})'.format(kwargs.get('embed').to_dict())
        log.debug(msg)

        # Send the actual message
        if 'locales' in kwargs:
            del kwargs['locales']
        if 'event' in kwargs:
            del kwargs['event']

        return await destination.send(**kwargs)

    async def delete_message(self, message, silent=False):
        """
        Deletes a message and registers the last 50 messages' IDs.
        :param message: The message to delete
        :param silent: Add the message to the no-log list
        """
        if not isinstance(message, discord.Message):
            raise RuntimeError('message must be a discord.Message instance')

        self.deleted_messages.append(message.id)
        if silent:
            self.deleted_messages_nolog.append(message.id)

        try:
            await message.delete()
        except discord.Forbidden as e:
            del self.deleted_messages[-1]
            if silent:
                del self.deleted_messages_nolog[-1]
            raise e

        if len(self.deleted_messages) > 50:
            del self.deleted_messages[0]
        if len(self.deleted_messages_nolog) > 50:
            del self.deleted_messages_nolog[0]

    @property
    def uptime(self):
        return datetime.now() - self.start_time
