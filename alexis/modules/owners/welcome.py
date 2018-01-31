import random

from discord import Embed

from alexis import Command
from alexis.database import ServerConfigMgrSingle
from alexis.utils import is_int


class Welcome(Command):
    cfg_channel = 'welcome_channel'
    cfg_messages = 'welcome_messages'
    separator = '|'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'welcome'
        self.aliases = ['bienvenida']
        self.help = 'Determina un canal para dar la bienvenida a nuevos usuarios, con mensajes personalizados.'
        self.owner_only = True
        self.default_config = {
            'welcome_max_messages': 10
        }

    async def handle(self, cmd):
        max_msgs = self.bot.config.get('welcome_max_msgs', 10)
        if not is_int(max_msgs):
            max_msgs = 10

        if cmd.argc == 0 or cmd.args[0] not in ['set', 'message', 'channel', 'disable']:
            if cmd.argc > 0 and cmd.find_channel(cmd.args[0]) is not None:
                subcmd = 'channel' if cmd.argc == 1 else 'set'
                cmd.args.insert(0, subcmd)
                cmd.argc += 1
            else:
                await cmd.answer('formato: $PX$NM <set|message|channel|disable> <opciones...> (si omites las opciones, '
                                 'verás la ayuda de cada sub-comando)')
                return

        if cmd.args[0] == 'set':
            if cmd.argc < 2:
                await cmd.answer('formato: $PX$NM set <canal> <mensaje1>|<mensaje2>|...|<mensaje{}>\n'
                                 'Si se agrega más de un mensaje, uno de ellos será elegido de forma aleatoria para '
                                 'recibir a un usuario. '
                                 'Cada mensaje debe ser separado por `{}` y puede contener hasta 100 '
                                 'carácteres. Puedes insertar los siguientes placeholders para que sean reemplazados '
                                 'en tu mensaje: \n'
                                 '$name: nombre del usuario\n'
                                 '$mention: mención al nombre del usuario\n'
                                 '$server: nombre del servidor'.format(max_msgs, Welcome.separator))
                return

            chan = cmd.find_channel(cmd.args[1])
            if chan is None:
                await cmd.answer('canal no encontrado')
                return

            msgs = [f.strip() for f in ' '.join(cmd.args[2:]).split(Welcome.separator)]
            for i, m in enumerate(msgs):
                if len(m) > 100:
                    await cmd.answer('Los mensajes sólo pueden tener hasta 100 carácteres. El mensaje no. {} tiene '
                                     '{} carácteres.'.format(i+1, len(m)))
                    return

            cmd.config.set(Welcome.cfg_channel, chan.id)
            cmd.config.set_list(Welcome.cfg_messages, msgs, Welcome.separator)
            await cmd.answer('configuración de bienvenida guardada!')

        elif cmd.args[0] == 'message':
            if (cmd.argc < 3 and cmd.args[1] != 'list') or cmd.argc < 2 \
                    or cmd.args[1] not in ['list', 'show', 'add', 'remove', 'set']:
                await cmd.answer('formato: $PX$NM message <list|add|remove|set> <opciones...> (si omites las opciones,'
                                 'verás las opciones de cada sub-sub-comando')
                return

            if cmd.config.get(Welcome.cfg_channel) == '':
                await cmd.answer('los mensajes de bienvenida están desactivados. Define el canal de bienvenida, o bien '
                                 'usa $PX$NM set <opciones...>')
                return
            msgs = cmd.config.get_list(Welcome.cfg_messages, Welcome.separator)

            if cmd.args[1] in ['list', 'show']:
                if len(msgs) == 0:
                    await cmd.answer('no hay mensajes')
                    return

                x = '\n'.join(['{}.- {}'.format(i+1, f) for i, f in enumerate(msgs)])
                x += '\n\n**Canal actual**: <#{}>'.format(cmd.config.get(Welcome.cfg_channel))
                embed = Embed(title='Mensajes de bienvenida', description=x)
                await cmd.answer(embed)

            elif cmd.args[1] == 'add':
                if len(msgs) >= max_msgs:
                    await cmd.answer('no es posible agregar más mensajes, el máximo es {}'.format(max_msgs))
                    return

                msg = ' '.join(cmd.args[2:])
                if Welcome.separator in msg:
                    await cmd.answer('el mensaje no puede contener `{}`'.format(Welcome.separator))
                    return

                cmd.config.add(Welcome.cfg_messages, msg, Welcome.separator)
                await cmd.answer('mensaje agregado!')

            elif cmd.args[1] == 'remove':
                if not is_int(cmd.args[2]):
                    await cmd.answer('ingresa un número por favor. Puedes obtener los números con el comando $PX$NM'
                                     'message list')
                    return

                if len(msgs) == 0:
                    await cmd.answer('no hay mensajes!')
                    return

                idx = int(cmd.args[2]) - 1
                if idx+1 > len(msgs):
                    await cmd.answer('número fuera de rango! Puedes obtener los números con el comando $PX$NM'
                                     'message list')
                    return

                cmd.config.remove_index(Welcome.cfg_messages, idx, Welcome.separator)

                await cmd.answer('mensaje eliminado!')
            elif cmd.args[1] == 'set':
                msgs = ' '.join(cmd.args[2:]).split(Welcome.separator)
                for m in msgs:
                    if Welcome.separator in m:
                        await cmd.answer('los mensajes no puede contener `{}`'.format(Welcome.separator))
                        return

                cmd.config.set_list(Welcome.cfg_messages, msgs, Welcome.separator)
                msg = ['mensajes guardados', 'mensaje guardado'][int(len(msgs) == 1)]
                await cmd.answer(msg)

        elif cmd.args[0] == 'channel':
            chan = cmd.find_channel(cmd.args[1])
            if chan is None:
                await cmd.answer('canal no encontrado')
                return

            cmd.config.set(Welcome.cfg_channel, chan.id)
            await cmd.answer('canal guardado')

        elif cmd.args[0] == 'disable':
            cmd.config.set(Welcome.cfg_channel, '')
            await cmd.answer('mensajes de bienvenida desactivados (los mensajes actuales no fueron eliminados)')

    async def on_member_join(self, member):
        cfg = ServerConfigMgrSingle(self.bot.sv_config, member.server)
        chanid = cfg.get(Welcome.cfg_channel)
        msgs = cfg.get_list(Welcome.cfg_messages, Welcome.separator)
        if chanid == '' or len(msgs) == 0:
            return

        chan = member.server.get_channel(chanid)
        if chan is None:
            return

        msg = random.choice(msgs)
        msg = msg.replace('$name', member.display_name)
        msg = msg.replace('$mention', member.mention)
        msg = msg.replace('$server', member.server.name)

        await self.bot.send_message(chan, msg)

