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

        if self.is_locked(message.server.id, message.channel.id):
            return False

    async def handle(self, message, cmd):
        channel = None
        if cmd.argc == 0:
            channel = message.channel
        elif cmd.argc == 1:
            if len(message.channel_mentions) > 0:
                channel = message.channel_mentions[0]
            else:
                channel = cmd.find_channel(cmd.args[0])

        if channel is None:
            await cmd.answer('canal no encontrado')
            return

        config, _ = ServerConfig.get_or_create(serverid=message.server.id, name='locked_bot_channels')
        chans = config.value.split(',')

        if cmd.cmdname == 'islocked':
            await cmd.answer('si' if channel.id in chans else 'no')
            return

        lock = cmd.cmdname == 'lockbot'

        process = True
        if channel.id in chans:
            if lock:
                msg = 'el canal ya está bloqueado, usa !unlockbot para desbloquear.'
                process = False
            else:
                chans.remove(channel.id)
                msg = 'canal desbloqueado! :smile:'
        else:
            if not lock:
                msg = 'el canal no está bloqueado, usa !lockbot para bloquear.'
                process = False
            else:
                if config.value == '':
                    chans = [channel.id]
                else:
                    chans.append(channel.id)
                msg = 'canal bloqueado jajaj ewe'

        if process:
            config.value = ','.join(chans)
            config.save()

        await cmd.answer(msg)

    def is_locked(self, serverid, channelid):
        config, _ = ServerConfig.get_or_create(serverid=serverid, name='locked_bot_channels')
        return channelid in config.value.split(',')
