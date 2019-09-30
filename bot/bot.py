import asyncio
import platform
import sys
from datetime import datetime

import discord

from bot import Language, StaticConfig, Configuration, Manager
from bot import defaults, init_db, log
from bot.libs.configuration import GuildConfiguration


class AlexisBot(discord.Client):
    __author__ = 'makzk (github.com/jkcgs)'
    __license__ = 'MIT'
    __version__ = '1.0.0-dev2.1'
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
        self.loop = asyncio.get_event_loop()

    def init(self):
        """
        Loads configuration, connects to database, and then connects to Discord.
        """
        log.info('%s v%s, discord.py v%s', AlexisBot.name, AlexisBot.__version__, discord.__version__)
        log.info('Python %s in %s.', sys.version.replace('\n', ''), sys.platform)
        log.info('Bot root path: %s', self.manager.get_bot_root())
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
            self.loop.run_until_complete(self.start(self.config['token']))
        except discord.errors.LoginFailure:
            log.error('Invalid Discord token!')
            raise
        except KeyboardInterrupt:
            self.loop.run_until_complete(self.close())
            log.error('Keyboard interrupt!')
        finally:
            self.loop.close()

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

    async def send_modlog(self, guild: discord.Guild, message=None, embed: discord.Embed=None,
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
        chanid = self.sv_config.get(guild.id, 'join_send_channel')
        if chanid == '':
            return

        if logtype and logtype in self.sv_config.get_list(guild.id, 'logtype_disabled'):
            return

        chan = self.get_channel(chanid)
        if chan is None:
            log.debug('[modlog] Channel not found (svid %s chanid %s)', guild.id, chanid)
            return

        await self.send_message(chan, content=message, embed=embed, locales=locales)

    def schedule(self, task, time=0, force=False):
        """
        Shorthand method: adds a task to the loop to be run every *time* seconds.
        :param task: The task function
        :param time: The time in seconds to repeat the task. If zero, the task will be called just once.
        :param force: What to do if the task was already created. If True, the task is cancelled and created again.
        """

        return self.manager.schedule(task, time, force)

    async def send_message(self, destination, content, **kwargs):
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
            destination_repr = '{} (ID: {})'.format(str(destination), destination.id)

        msg = 'Sending message "{}" to {} '.format(kwargs['content'], destination_repr)
        if isinstance(kwargs.get('embed', None), discord.Embed):
            msg += ' (with embed: {})'.format(kwargs.get('embed').to_dict())
        log.debug(msg)

        # Send the actual message
        del kwargs['locales'], kwargs['event']
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

    # ------------------------
    # | GUILD HELPER METHODS |
    # ------------------------

    def get_guild_config(self, guild: discord.Guild):
        """
        Creates a GuildConfiguration instance for a specific discord.Guild
        :param guild: The guild that "owns" the GuildConfiguration instance
        :return: The GuildConfiguration instance for that guild.
        """
        return GuildConfiguration(self.sv_config, guild)

    def is_guild_owner(self, member: discord.Member):
        """
        Check if a guild member is an "owner" for the bot
        :param member: The discord.Guild member.
        :return: A boolean value depending if the member is an owner or not.
        """
        # The server owner or a user with the Administrator permission is an owner to the bot.
        if member.guild.owner == member or member.guild_permissions.administrator:
            return True

        # Check if the user has the owner role
        cfg = self.get_guild_config(member.guild)
        owner_roles = cfg.get_list('owner_roles', '\n', [self.config['owner_role']])
        for role in member.roles:
            if role.id in owner_roles \
                    or role.name in owner_roles \
                    or member.id in owner_roles:
                return True

        return False

    def get_prefix(self, destination=None):
        """
        Gets the prefix for a channel of destination. It would normally return a prefix for a guild
        TextChannel, and return the default one for all the other destinations.
        :param destination: The Guild or TextChannel of destination. Any other of these will return
        the default prefix.
        :return: The prefix for the destination.
        """
        if isinstance(destination, discord.TextChannel):
            # If the destination is a TextChannel, use its Guild
            destination = destination.guild
        elif not isinstance(destination, discord.Guild):
            # Anything not a TextChannel or Guild, sets the destination to None to get the default prefix.
            destination = None

        # Retrieve and return the prefix
        cfg = self.get_guild_config(destination)
        return cfg.get('command_prefix', self.config['command_prefix'])

    @property
    def uptime(self):
        return datetime.now() - self.start_time

    # ------------------
    # | EVENT HANDLERS |
    # ------------------

    async def on_ready(self):
        """ This is executed once the bot has successfully connected to Discord. """

        log.info('Connected as "%s" (%s)', self.user.name, self.user.id)
        log.info('It took %.3f seconds to connect.', (datetime.now() - self.start_time).total_seconds())
        log.info('------')
        await self.change_presence(activity=discord.Game(self.config['playing']))

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

    async def on_guild_join(self, guild):
        await self.manager.dispatch('on_guild_join', guild=guild)

    async def on_guild_remove(self, guild):
        await self.manager.dispatch('on_guild_remove', guild=guild)

    async def on_member_ban(self, member):
        await self.manager.dispatch('on_member_ban', member=member)

    async def on_member_unban(self, member):
        await self.manager.dispatch('on_member_unban', member=member)

    async def on_typing(self, channel, user, when):
        await self.manager.dispatch('on_typing', channel=channel, user=user, when=when)
