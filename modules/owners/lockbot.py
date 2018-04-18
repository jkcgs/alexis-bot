from discord import Embed

from bot import Command
from bot.libs.configuration import ServerConfig


cfg_locked = 'locked_bot_channels'


class LockBot(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'lockbot'
        self.aliases = ['unlockbot', 'islocked']
        self.help = 'Bloquea o desbloquea al bot para que no lo puedan usar los sucios mortales'
        self.owner_only = True
        self.allow_pm = False

    async def pre_on_message(self, message, event):
        if event.is_pm or event.owner:
            return

        if is_locked(message.server.id, message.channel.id):
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
            await cmd.answer('canal no encontrado')
            return

        chans = cmd.config.get_list(cfg_locked)
        chanid = 'all' if chall else channel.id

        if cmd.cmdname == 'islocked':
            locked = is_locked(cmd.message.server.id, chanid)
            msg = 'si' if locked else 'no'

            if 'all' in chans:
                msg += ' pero también está todo bloqueado c:'
            await cmd.answer(msg)
            return

        lock = cmd.cmdname == 'lockbot'
        if chanid == 'all':
            if lock:
                if 'all' in chans:
                    await cmd.answer('ya está todo bloqueado')
                    return
                else:
                    cmd.config.add(cfg_locked, 'all')
                    await cmd.answer('ahora todo está bloqueado ewe')
                    return
            else:
                if 'all' not in chans:
                    await cmd.answer('no está todo bloqueado XD')
                    return
                else:
                    if cmd.argc > 1 and cmd.args[1] == 'keep':
                        cmd.config.remove(cfg_locked, 'all')
                        await cmd.answer('desbloqueado todo (excepto lo que estaba bloqueado antes del bloqueo total)')
                        return
                    else:
                        cmd.config.set(cfg_locked, '')
                        await cmd.answer('desbloqueado todo')
                        return

        if chanid in chans:
            if lock:
                await cmd.answer('el canal ya está bloqueado, usa $PXunlockbot para desbloquear.')
                return

            cmd.config.remove(cfg_locked, chanid)
            await cmd.answer('canal desbloqueado! :smile:')
        else:
            if not lock:
                await cmd.answer('el canal no está bloqueado, usa $PXlockbot para bloquear.')
                return

            cmd.config.add(cfg_locked, chanid)
            await cmd.answer('canal bloqueado jajaj ewe')


class LockedChans(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'lockedlist'
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, cmd):
        chans = cmd.config.get_list(cfg_locked)
        is_all = 'all' in chans
        others = [f for f in chans if f != 'all']
        chan_list = []
        for chanid in others:
            chan = cmd.message.server.get_channel(chanid)
            if chan is None:
                chan_list.append('- {} (no encontrado)'.format(chanid))
            else:
                chan_list.append('- {} (ID: {})'.format(chan.mention, chanid))

        msg = ''
        if is_all:
            msg = 'todos los canales están bloqueados.'
            if len(others) > 0:
                msg += ' Además, los siguientes canales han sido marcados como bloqueados.'
        else:
            if len(others) > 0:
                msg += 'los siguientes canales están bloqueados'
            else:
                msg = 'no hay canales bloqueados.'

        embed = None
        if len(others) > 0:
            embed = Embed(description='\n'.join(chan_list))

        await cmd.answer(msg, embed=embed)


def is_locked(serverid, channelid):
    config, _ = ServerConfig.get_or_create(serverid=serverid, name=cfg_locked)
    val = [] if config.value == '' else config.value.split(',')
    return 'all' in val or channelid in val
