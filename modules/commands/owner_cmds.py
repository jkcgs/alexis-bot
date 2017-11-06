import re

import discord

from modules.base.command import Command
from discord import Game
import sys
import alexis
from modules.base.database import ServerConfig

rx_snowflake = re.compile('^\d{10,19}$')
rx_channel = re.compile('^<#\d{10,19}>$')


class ReloadCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reload'
        self.help = 'Recarga la configuración'
        self.owner_only = True

    async def handle(self, message, cmd):
        if not self.bot.load_config():
            msg = 'No se pudo recargar la configuración'
        else:
            msg = 'Configuración recargada correctamente'

        await cmd.answer(msg)


class ShutdownCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'shutdown'
        self.help = 'Detiene el proceso del bot'
        self.owner_only = True

    async def handle(self, message, cmd):
        await cmd.answer('chao loh vimo')
        await self.bot.logout()
        sys.exit(0)


class InfoCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['version', 'info']
        self.help = 'Muestra la información del bot'

    async def handle(self, message, cmd):
        info_msg = "```\nAutores: {}\nVersión: {}\nEstado: {}```"
        info_msg = info_msg.format(alexis.__author__, alexis.__version__, alexis.__status__)
        await cmd.answer(info_msg)


class SetStatus(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'status'
        self.help = 'Determina el status del bot'
        self.owner_only = True

    async def handle(self, message, cmd):
        status = '' if len(cmd.args) < 1 else cmd.text
        await self.bot.change_presence(game=Game(name=status))
        await cmd.answer('k')


class ClearReactions(Command):

    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['clearreactions', 'clr']
        self.help = 'Elimina las reacciones de uno o más mensajes'
        self.owner_only = True

    async def handle(self, message, cmd):
        if cmd.argc < 1:
            prefix = self.bot.config['command_prefix']
            await cmd.answer('Formato: {}{} [#canal=actual] <id_mensaje1> ... <id_mensajeN>'.format(prefix, cmd.cmdname))
            return

        await cmd.typing()

        channel = message.channel
        if rx_channel.match(cmd.args[0]):
            channel = message.channel_mentions[0]
            cmd.args = cmd.args[1:]
            cmd.argc -= 1

        filtered_len = len([f for f in cmd.args if rx_snowflake.match(f)])
        if cmd.argc != filtered_len:
            await cmd.answer('Por favor ingresa formatos de IDs compatibles')
            return

        success_count = 0
        for arg in cmd.args:
            try:
                msg = await self.bot.get_message(channel, arg)
                await self.bot.clear_reactions(msg)
                success_count += 1
            except discord.Forbidden:
                pass

        if success_count == 0:
            msg_suffix = 'del mensaje' if cmd.argc == 1 else 'de ningún mensaje'
            await cmd.answer('No se pudo limpiar las reacciones ' + msg_suffix)
        elif success_count < cmd.argc:
            await cmd.answer('Se eliminaron las reacciones de algunos mensajes')
        else:
            await cmd.answer('Reacciones eliminadas correctamente')


class LockBot(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['lockbot', 'lock', 'unlockbot', 'unlock']
        self.help = 'Bloquea o desbloquea al bot para que no lo puedan usar los sucios mortales'
        self.owner_only = True
        self.allow_pm = False

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
            await cmd.answer('Canal no encontrado')
            return

        lock = cmd.cmdname in ['lock', 'lockbot']

        config, _ = ServerConfig.get_or_create(serverid=message.server.id, name='locked_bot_channels')
        chans = config.value.split(',')

        process = True
        if channel.id in chans:
            if lock:
                msg = 'El canal ya está bloqueado, usa !unlockbot para desbloquear.'
                process = False
            else:
                chans.remove(channel.id)
                msg = 'Canal desbloqueado! :D'
        else:
            if not lock:
                msg = 'El canal no está bloqueado, usa !lockbot para bloquear.'
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
