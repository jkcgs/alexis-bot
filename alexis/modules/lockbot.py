from alexis import Command
from alexis.base.database import ServerConfig


class LockBot(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'lockbot'
        self.aliases = ['unlockbot', 'islocked']
        self.help = 'Bloquea o desbloquea al bot para que no lo puedan usar los sucios mortales'
        self.owner_only = True
        self.allow_pm = False

    async def pre_on_message(self, message, cmd):
        if cmd.is_pm or cmd.owner:
            return

        if is_locked(message.server.id, message.channel.id):
            return False

    async def handle(self, message, cmd):
        channel = None
        chall = False
        if cmd.argc == 0:
            channel = message.channel
        elif cmd.argc >= 1:
            if len(message.channel_mentions) > 0:
                channel = message.channel_mentions[0]
            elif cmd.args[0] != 'all':
                channel = cmd.find_channel(cmd.args[0])
            else:
                chall = True

        if not chall and channel is None:
            await cmd.answer('canal no encontrado')
            return

        chans = cmd.config.get_list('locked_bot_channels',)
        chanid = 'all' if chall else channel.id

        if cmd.cmdname == 'islocked':
            locked = is_locked(message.server.id, chanid)
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
                    cmd.config.add('locked_bot_channels', 'all')
                    await cmd.answer('ahora todo está bloqueado ewe')
                    return
            else:
                if 'all' not in chans:
                    await cmd.answer('no está todo bloqueado XD')
                    return
                else:
                    if cmd.argc > 1 and cmd.args[1] == 'keep':
                        cmd.config.remove('locked_bot_channels', 'all')
                        await cmd.answer('desbloqueado todo (excepto lo que estaba bloqueado antes del bloqueo total)')
                        return
                    else:
                        cmd.config.set('locked_bot_channels', '')
                        await cmd.answer('desbloqueado todo')
                        return

        if chanid in chans:
            if lock:
                await cmd.answer('el canal ya está bloqueado, usa $PXunlockbot para desbloquear.')
                return

            cmd.config.remove('locked_bot_channels', chanid)
            await cmd.answer('canal desbloqueado! :smile:')
        else:
            if not lock:
                await cmd.answer('el canal no está bloqueado, usa $PXlockbot para bloquear.')
                return

            cmd.config.add('locked_bot_channels', chanid)
            await cmd.answer('canal bloqueado jajaj ewe')


def is_locked(serverid, channelid):
    config, _ = ServerConfig.get_or_create(serverid=serverid, name='locked_bot_channels')
    val = [] if config.value == '' else config.value.split(',')
    return 'all' in val or channelid in val
