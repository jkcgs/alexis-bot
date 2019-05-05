from discord import Embed

from bot import Command, categories
from bot.libs.configuration import ServerConfig


cfg_locked = 'locked_bot_channels'


class LockBot(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'lockbot'
        self.aliases = ['unlockbot', 'islocked']
        self.help = '$[lockbot-help]'
        self.format = '$CMD [all]'
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.STAFF

    async def pre_on_message(self, message, event):
        if event.is_pm or event.owner:
            return

        if is_locked(message.guild.id, message.channel.id):
            return False

    async def handle(self, cmd):
        channel = None
        chall = False
        if cmd.argc == 0:
            channel = cmd.message.channel
        elif cmd.argc >= 1:
            if len(cmd.message.channel_mentions) > 0:
                channel = cmd.message.channel_mentions[0]
            elif cmd.args[0] != 'all':
                channel = cmd.find_channel(cmd.args[0])
            else:
                chall = True

        if not chall and channel is None:
            await cmd.answer('$[lockbot-channel-not-found]')
            return

        chans = cmd.config.get_list(cfg_locked)
        chanid = 'all' if chall else channel.id

        if cmd.cmdname == 'islocked':
            locked = is_locked(cmd.message.server.id, chanid)
            msg = ['$[lockbot-no]', '$[lockbot-yes]'][locked]

            if 'all' in chans:
                msg += '$[lockbot-also]'
            await cmd.answer(msg)
            return

        if chanid == 'all':
            if cmd.cmdname == 'lockbot':
                if 'all' in chans:
                    await cmd.answer('$[lockbot-all-already]')
                    return
                else:
                    cmd.config.add(cfg_locked, 'all')
                    await cmd.answer('$[lockbot-all-locked]')
                    return
            else:
                if 'all' not in chans:
                    await cmd.answer('$[lockbot-all-not-locked]')
                    return
                else:
                    if cmd.argc > 1 and cmd.args[1] == 'keep':
                        cmd.config.remove(cfg_locked, 'all')
                        await cmd.answer('$[lockbot-all-removed-but]')
                        return
                    else:
                        cmd.config.set(cfg_locked, '')
                        await cmd.answer('$[lockbot-all-removed]')
                        return

        if chanid in chans:
            if cmd.cmdname == 'lockbot':
                await cmd.answer('$[lockbot-already]')
                return

            cmd.config.remove(cfg_locked, chanid)
            await cmd.answer('$[lockbot-unlocked]')
        else:
            if cmd.cmdname != 'lockbot':
                await cmd.answer('$[lockbot-not-locked]')
                return

            cmd.config.add(cfg_locked, chanid)
            await cmd.answer('$[lockbot-locked]')


class LockedChans(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'lockedlist'
        self.help = '$[lockbot-list-help]'
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.MODERATION

    async def handle(self, cmd):
        chans = cmd.config.get_list(cfg_locked)
        is_all = 'all' in chans
        others = [f for f in chans if f != 'all']
        chan_list = []
        for chanid in others:
            chan = cmd.message.server.get_channel(chanid)
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


def is_locked(serverid, channelid):
    config, _ = ServerConfig.get_or_create(serverid=serverid, name=cfg_locked)
    val = [] if config.value == '' else config.value.split(',')
    return 'all' in val or channelid in val
