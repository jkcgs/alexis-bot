from discord import Embed, TextChannel, DMChannel, Message

from bot import Command, categories
from bot.lib.common import is_owner, is_pm
from bot.lib.guild_configuration import GuildConfiguration
from bot.regex import pat_channel
from bot.utils import auto_int

cfg_locked = 'locked_bot_channels'
cfg_all = 'all'


class LockBot(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'lockbot'
        self.aliases = ['lock']
        self.help = '$[lockbot-help]'
        self.format = '$CMD [all]'
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.STAFF

    async def handle(self, cmd):
        chans = cmd.config.get_list(cfg_locked)
        chan = get_chan_cmd(cmd)

        if cmd.argc > 2:
            return await cmd.answer(self.format)

        # 'all' lock
        if chan == cfg_all:
            if cfg_all in chans:
                await cmd.answer('$[lockbot-all-already]')
                return

            cmd.config.add(cfg_locked, cfg_all)
            await cmd.answer('$[lockbot-all-locked]')
            return

        if not isinstance(chan, TextChannel):
            return await cmd.answer(self.format)

        # Channel unlock
        if str(chan.id) in chans:
            await cmd.answer('$[lockbot-already]')
            return

        cmd.config.add(cfg_locked, str(chan.id))
        await cmd.answer('$[lockbot-locked]')

    async def pre_on_message(self, message: Message, **_):
        if is_pm(message.channel) or is_owner(self.bot, message.author):
            return

        config = GuildConfiguration.get_instance(message.guild)
        lockedlist = config.get_list(cfg_locked)
        if cfg_all in lockedlist or str(message.channel.id) in lockedlist:
            return False


class UnlockBot(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'unlockbot'
        self.aliases = ['unlock']
        self.help = '$[lockbot-help]'
        self.format = '$CMD [all]'
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.STAFF

    async def handle(self, cmd):
        chans = cmd.config.get_list(cfg_locked)
        chan = get_chan_cmd(cmd)

        if cmd.argc > 2:
            return await cmd.answer(self.format)

        # Clear all locks
        if cmd.argc > 0 and cmd.args[0] == 'clear':
            cmd.config.unset(cfg_locked)
            return await cmd.answer('$[lockbot-cleared]')

        # Remove 'all' lock
        if chan == cfg_all:
            if cfg_all not in chans:
                await cmd.answer('$[lockbot-all-not-locked]')
                return

            cmd.config.remove(cfg_locked, cfg_all)
            return await cmd.answer('$[lockbot-all-removed]')

        if not isinstance(chan, TextChannel):
            return await cmd.answer(self.format)

        # Channel unlock
        if str(chan.id) not in chans:
            await cmd.answer('$[lockbot-not-locked]')
            return

        cmd.config.remove(cfg_locked, str(chan.id))
        await cmd.answer('$[lockbot-unlocked]')


class IsLockedBot(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'islocked'
        self.help = '$[lockbot-help]'
        self.format = '$CMD [all]'
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.STAFF

    async def handle(self, cmd):
        chans = cmd.config.get_list(cfg_locked)
        chan = get_chan_cmd(cmd)
        total_lock = cfg_all in chans

        if chan == cfg_all:
            msg = ['$[lockbot-all-not-locked]', '$[lockbot-list-all-locked]'][total_lock]
            return await cmd.answer(msg)

        if not isinstance(chan, TextChannel):
            return await cmd.answer(self.format)

        locked = cfg_all in chans or str(chan.id) in chans
        msg = ['$[lockbot-no]', '$[lockbot-yes]'][locked]

        if total_lock:
            msg += '$[lockbot-also]'

        await cmd.answer(msg)


class LockedChans(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'lockedlist'
        self.aliases = ['locklist']
        self.help = '$[lockbot-list-help]'
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.MODERATION

    async def handle(self, cmd):
        chans = cmd.config.get_list(cfg_locked)
        is_all = cfg_all in chans
        others = [f for f in chans if f != cfg_all]
        chan_list = []

        for chanid in others:
            chan = cmd.message.guild.get_channel(auto_int(chanid))
            if chan is None:
                chan_list.append('- {} ($[lockbot-not-found])'.format(chanid))
            else:
                chan_list.append('- {} (ID: {})'.format(chan.mention, chanid))

        msg = ''
        if is_all:
            msg = '$[lockbot-list-all-locked]'
            if len(others) > 0:
                msg += ' $[lockbot-list-also]'
        else:
            if len(others) > 0:
                msg += '$[lockbot-list]'
            else:
                msg = '$[lockbot-list-none]'

        embed = None
        if len(others) > 0:
            embed = Embed(description='\n'.join(chan_list))

        await cmd.answer(msg, embed=embed)


def get_chan_cmd(cmd):
    if cmd.argc == 1 and cmd.args[0] == cfg_all:
        return cfg_all

    if cmd.argc == 0:
        return cmd.channel
    elif pat_channel.match(cmd.args[0]):
        return cmd.message.channel_mentions[0]
    else:
        return None
