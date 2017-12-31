import re

import discord

from alexis import Command
from alexis import Alexis
from alexis.base.utils import unserialize_avail, get_server_role, serialize_avail

rx_snowflake = re.compile('^\d{10,19}$')
rx_channel = re.compile('^<#\d{10,19}>$')


class InfoCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'info'
        self.aliases = ['version']
        self.help = 'Muestra la información del bot'

    async def handle(self, message, cmd):
        info_msg = "```\nAutores: {}\nVersión: {}```"
        info_msg = info_msg.format(Alexis.__author__, Alexis.__version__)
        await cmd.answer(info_msg)


class ClearReactions(Command):

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'clearreactions'
        self.aliases = ['clr']
        self.help = 'Elimina las reacciones de uno o más mensajes'
        self.owner_only = True

    async def handle(self, message, cmd):
        if cmd.argc < 1:
            await cmd.answer('formato:  $PX$NM [#canal=actual] <id_mensaje1> ... <id_mensajeN>')
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
            await cmd.answer('no se pudo limpiar las reacciones ' + msg_suffix)
        elif success_count < cmd.argc:
            await cmd.answer('se eliminaron las reacciones de algunos mensajes')
        else:
            await cmd.answer('reacciones eliminadas correctamente')


class ChangePrefix(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'prefix'
        self.aliases = ['changeprefix']
        self.help = 'Cambia el prefijo para los comandos'
        self.owner_only = True

    async def handle(self, message, cmd):
        if cmd.argc < 1:
            await cmd.answer('formato: $PX$NM <prefijo>')
            return

        txt = cmd.args[0]
        if len(txt) > 3:
            await cmd.answer('el prefijo sólo puede tener hasta 3 carácteres')
            return

        cmd.config.set('command_prefix', txt)
        await cmd.answer('prefijo configurado como {}'.format(txt))


class CommandConfig(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'cmd'
        self.help = 'Cambia la configuración de algún comando'
        self.owner_only = True

    async def handle(self, message, cmd):
        if cmd.argc < 2:
            await cmd.answer('formato: $PX$NM <enable|disable> <comando>')
            return

        if cmd.args[1] not in self.bot.cmds:
            await cmd.answer('el comando no existe')
            return

        avail = serialize_avail(cmd.config.get('cmd_status', ''))
        cmd_ins = self.bot.cmds[cmd.args[1]]
        current = avail.get(cmd_ins.name, '+' if cmd_ins.default_enabled else '-')

        if cmd.args[0] == 'enable':
            if current == '+':
                await cmd.answer('el comando ya está activado')
                return
            else:
                avail[cmd_ins.name] = '+'
                cmd.config.set('cmd_status', unserialize_avail(avail))
                await cmd.answer('comando activado correctamente')
                return
        elif cmd.args[0] == 'disable':
            if current == '-':
                await cmd.answer('el comando ya está desactivado')
                return
            else:
                avail[cmd_ins.name] = '-'
                cmd.config.set('cmd_status', unserialize_avail(avail))
                await cmd.answer('comando desactivado correctamente')
                return
        else:
            await cmd.answer('este subcomando no existe')


class OwnerRoles(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ownerrole'
        self.help = 'Cambia la configuración de roles de propietario'
        self.owner_only = True

    async def handle(self, message, cmd):
        if cmd.argc < 1:
            await cmd.answer('formato: $PX$NM <comando> [rol/roles...]')
            return

        await cmd.typing()
        owner_roles = cmd.config.get('owner_roles', self.bot.config['owner_role'])
        owner_roles = [owner_roles.split('\n'), []][int(owner_roles == '')]

        if cmd.args[0] in ['set', 'add', 'remove']:
            if cmd.argc < 2:
                await cmd.answer('formato: $PX$NM <comando> [rol/roles...]')
                return

            cmd_role = ' '.join(cmd.args[1:])
            role = get_server_role(message.server, cmd_role)
            if role is None and cmd_role not in owner_roles:
                await cmd.answer('el rol no fue encontrado')
                return

            if cmd.args[0] == 'set':
                if role is None:  # doble check
                    await cmd.answer('el rol no fue encontrado')
                    return

                cmd.config.set('owner_roles', role.id)
                await cmd.answer('el rol de owner ahora es **{}**'.format(role.name))
            elif cmd.args[0] == 'add':
                if role.id in owner_roles:
                    await cmd.answer('El rol ya es de owner')
                    return

                cmd.config.set('owner_roles', '\n'.join(owner_roles + [role.id]))
                await cmd.answer('rol **{}** agregado como de owner'.format(role.name))
            elif cmd.args[0] == 'remove':
                if role.id not in owner_roles:
                    await cmd.answer('Ese rol no es de owner')
                    return

                owner_roles.remove(role.id)
                cmd.config.set('owner_roles', '\n'.join(owner_roles))
                await cmd.answer('el rol **{}** ahora ya no es owner'.format(role.name))
        elif cmd.args[0] == 'adduser':
            await cmd.answer('wip')
        elif cmd.args[0] == 'removeuser':
            await cmd.answer('wip')
        elif cmd.args[0] == 'list':
            msg = 'Roles owner: '
            msg_list = []
            for roleid in owner_roles:
                srole = get_server_role(message.server, roleid)
                if srole is not None:
                    msg_list.append(srole.name)
                else:
                    member = message.server.get_member(roleid)
                    if member is not None:
                        msg_list.append('usuario:' + member.display_name)
                    else:
                        msg_list.append('id:' + roleid)
            await cmd.answer(msg + ', '.join(msg_list))
        else:
            await cmd.answer('no existe este subcomando')
