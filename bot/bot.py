import asyncio
import platform
import sys
from datetime import datetime

import discord
from discord import Embed, Server
from discord.http import Route

from bot import Language, StaticConfig, Configuration, Manager
from bot import defaults, init_db, log
from bot.utils import destination_repr, get_bot_root


class AlexisBot(discord.Client):
    __author__ = 'makzk (github.com/jkcgs)'
    __license__ = 'MIT'
    __version__ = '1.0.0-dev.70'
    name = 'AlexisBot'

    def __init__(self, **options):
        """
        Initializes configuration, logging, an aiohttp session and class attributes.
        :param options: The discord.Client options
        """
        super().__init__(**options)

        self.db = None
        self.sv_config = None
        self.last_author = None
        self.initialized = False
        self.start_time = datetime.now()

        self.lang = {}
        self.deleted_messages = []
        self.deleted_messages_nolog = []

        self.manager = Manager(self)
        self.config = StaticConfig()

    def init(self):
        """
        Loads configuration, connects to database, and then connects to Discord.
        """
        log.info('%s v%s, discord.py v%s', AlexisBot.name, AlexisBot.__version__, discord.__version__)
        log.info('Python %s in %s.', sys.version.replace('\n', ''), sys.platform)
        log.info('Bot root path: %s', get_bot_root())
        log.info(platform.uname())
        log.info('------')

        # Load configuration
        self.load_config()
        if self.config.get('token', '') == '':
            raise RuntimeError('Discord bot token not defined. It should be in config.yml file.')

        # Load database
        log.info('Connecting to the database...')
        self.db = init_db()
        log.info('Successfully conected to database using %s', self.db.__class__.__name__)
        self.sv_config = Configuration()

        # Load command classes and instances from bots.modules
        log.info('Loading commands...')
        self.manager.load_instances()
        self.manager.dispatch_sync('on_loaded', force=True)

        # Connect to Discord
        try:
            self.start_time = datetime.now()
            log.info('Connecting to Discord...')
            self.run(self.config['token'])
        except discord.errors.LoginFailure:
            log.error('Invalid Discord token!')
            raise
        except KeyboardInterrupt:
            log.error('Keyboard interrupt!')
        except Exception as ex:
            # I don't know how to fix this, but it's raised when closing the bot.
            # if str(ex) != '\'NoneType\' object is not iterable':
            raise ex

    def load_config(self):
        """
        Loads static and language configuration
        :return: A boolean depending on the operation's result.
        """
        try:
            log.info('Loading configuration...')
            self.config.load(defaults.config)
            self.lang = Language('lang', default=self.config['default_lang'], autoload=True)
            log.info('Default language: %s', self.config['default_lang'])
            log.info('Configuration loaded')
            return True
        except Exception as ex:
            log.exception(ex)
            return False

    def logout(self):
        """
        Stops tasks, close connections and logout from Discord.
        :return:
        """
        log.debug('Closing stuff...')
        yield from super().logout()

        # Close everything http related
        loop = asyncio.get_event_loop()
        loop.create_task(self.http.close())
        self.manager.close_http()

        # Stop tasks
        self.manager.cancel_tasks()

        # And that's it!
        log.debug('Goodbye!')

    async def send_modlog(self, server, message=None, embed=None, locales=None):
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

        await self.send_message(chan, message, embed=embed, locales=locales)

    def schedule(self, task, time=0, force=False):
        """
        Shorthand method: adds a task to the loop to be run every *time* seconds.
        :param task: The task function
        :param time: The time in seconds to repeat the task. If zero, the task will be called just once.
        :param force: What to do if the task was already created. If True, the task is cancelled and created again.
        """

        return self.manager.schedule(task, time, force)

    async def channel_is_nsfw(self, channel):
        """
        Checks if a given channel is marked as NSFW or not.
        :param channel: The channel, as a discord.Channel instance, or the channel ID.
        :return: A boolean value given the operation result.
        """
        if isinstance(discord, discord.Channel) and channel.name.lower().startswith('nsfw'):
            return True

        channel_id = channel.id if isinstance(discord, discord.Channel) else str(channel)
        route = Route('GET', '/channels/{channel_id}', channel_id=channel_id)
        log.debug('Loading %s...', route.url)

        req = await self.http.request(route)
        log.debug(req)

        return req['name'].lower().startswith('nsfw') or req.get('nsfw', False)

    """
    ===== METHOD OVERRIDES =====
    """

    async def send_message(self, destination, content=None, *, tts=False, embed=None, locales=None, event=None):
        """
        Override original discord.Client method to send messages, to fire other calls
        like event handlers, message filters and bot logging. Allows original method's parameters.
        :param destination: Where to send the message, e.g. discord.Channel, discord.User, discord.Object.
        :param content: Textual content to send
        :param tts: Enable TTS (text to speech).
        :param embed: Send an embed with the message.
        :param locales: Strings to replace on the message and embed.
        :param event: Original event that triggers the message. Used to deliver it to handlers.
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
        return await super().send_message(**kwargs)

    async def delete_message(self, message):
        """
        Deletes a message and registers the last 20 messages' IDs.
        :param message: The message to delete
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
        Deletes a message and registers the last 20 messages' IDs.
        It also adds the message to a no-track list, for the corresponding modules (i.e. Modlog).
        :param message: The message to delete
        """

        try:
            self.deleted_messages_nolog.append(message.id)
            await self.delete_message(message)
        except discord.Forbidden as e:
            del self.deleted_messages_nolog[-1]
            raise e

        if len(self.deleted_messages_nolog) > 20:
            del self.deleted_messages_nolog[0]

    """
    ===== EVENT HANDLERS =====
    """

    async def on_ready(self):
        """ This is executed when the bot has successfully connected to Discord. """

        log.info('Connected as "%s" (%s)', self.user.name, self.user.id)
        log.info('It took %.3f seconds to connect.', (datetime.now() - self.start_time).total_seconds())
        log.info('------')
        await self.change_presence(game=discord.Game(name=self.config['playing']))

        self.initialized = True
        self.manager.create_tasks()
        await self.manager.dispatch('on_ready')

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
