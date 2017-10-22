import asyncio
import re
import datetime
from datetime import datetime as dt

import discord
import peewee

from modules.base.command import Command
from modules.base.database import BaseModel


class Mute(Command):
    muted_role = 'Muted'
    rx_timediff_all = re.compile('^([0-9]+[smhdSMDH]?)+$')
    rx_timediff = re.compile('([0-9]+[smhdSMDH]?)')

    cant_manage_msg = 'no tengo permiso pa manejar roles D:'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'mute'
        self.help = 'Mutea usuarios'
        self.owner_only = True
        self.db_models = [MutedUser]
        self.run_task = True
        self.allow_pm = False

    async def handle(self, message, cmd):
        if len(cmd.args) < 1 or len(message.mentions) != 1:
            await cmd.answer('Formato: !mute <@mención> [duración]|[razón]')
            return

        member = message.mentions[0]
        server = message.server

        if member.id == self.bot.user.id:
            await cmd.answer('como me vas a mutear a mi! owo')
            return

        if member.id == cmd.author.id:
            await cmd.answer('no podi mutearte a ti mismo jaj')
            return

        # Verificar si se pueden manejar roles
        if not self.can_manage_roles(server):
            self.log.warning(Mute.cant_manage_msg + ' (server: %s)', str(server))
            await cmd.answer(Mute.cant_manage_msg)
            return

        # Obtener argumentos del mute
        mute_args = []
        if len(cmd.args) > 1:
            mute_args = ' '.join(cmd.args[1:]).split('|')

        # Obtener tiempo del mute
        until = None
        deltatime = None
        if len(mute_args) > 0:
            if Mute.rx_timediff_all.match(mute_args[0]) is None:
                cmd.answer('Tiempo de mute no válido')
                return

            deltatime = Mute.timediff_parse(mute_args[0])
            until = dt.now() + deltatime

        # Quitar mute de la db si ya está muteado
        MutedUser.delete().where(MutedUser.userid == member.id).execute()

        # Revisar si el usuario ya tiene el rol
        mutedrole = None
        for role in member.roles:
            if role.name == Mute.muted_role:
                mutedrole = role
                break

        # Si el usuario ya tiene el rol, no es necesario agregarlo
        if mutedrole is None:
            mutedrole = Command.get_server_role(server, Mute.muted_role)
            # if mutedrole is still None
            if mutedrole is None:
                self.log.warning('El rol "%s" no existe (server: %s)', Mute.muted_role, server)
                cmd.answer('El rol "{}" no existe!'.format(Mute.muted_role))
                return

            await self.bot.add_roles(member, mutedrole)

        reason = ''
        if len(mute_args) > 1:
            reason = ' '.join(cmd.args[2:])

        MutedUser.insert(userid=member.id, serverid=server.id, until=until, reason=reason,
                         author_name=str(cmd.author), author_id=cmd.author.id).execute()

        str_deltatime = ' por **{}**'.format(Mute.deltatime_to_str(deltatime)) if deltatime is not None else ''

        # Enviar PM con el aviso del mute
        try:
            await self.bot.send_message(member, 'Hola! Lamentablemente has sido muteado en el servidor **{}**{}.'
                                        .format(server.name, str_deltatime))
        except discord.errors.Forbidden as e:
            self.log.exception(e)

        # Avisar por el canal donde se envió el comando
        await cmd.answer('Usuario **{}** muteado{}!'.format(member.display_name, str_deltatime))

    # Restaurar el rol de muteado una vez que el usuario ha reingresado
    async def on_member_join(self, member):
        server = member.server
        if not self.can_manage_roles(member):
            self.log.warning(Mute.cant_manage_msg)
            return

        role = Command.get_server_role(server, Mute.muted_role)
        if role is None:
            self.log.warning('El rol "%s" no existe (server: %s)', Mute.muted_role, server)
            return

        try:
            muted = MutedUser.get((MutedUser.until > dt.now()) | MutedUser.until.is_null(),
                                  MutedUser.userid == member.id)
            self.bot.add_role(member, role)
            self.log.info('Rol de muteado agregado a %s server %s', member.display_name, server)
            return
        except MutedUser.DoesNotExist:
            pass

    # Elimina los roles de muteado una vez que ha terminado
    async def task(self):
        muted = MutedUser.select().where((MutedUser.until <= dt.now()) & MutedUser.until.is_null(False))
        for muteduser in muted:
            server = self.bot.get_server(muteduser.serverid)
            if server is None:
                continue

            self_member = server.get_member(self.bot.user.id)
            if not self_member.server_permissions.manage_roles:
                self.log.warning(Mute.cant_manage_msg + ' (server: %s)', server)
                continue

            member = server.get_member(muteduser.userid)
            role = Command.get_server_role(server, Mute.muted_role)
            if role is None:
                self.log.warning('El rol "%s" no existe (server: %s)', Mute.muted_role, server)
                continue
            else:
                await self.bot.remove_roles(member, role)
                MutedUser.delete_instance(muteduser)
                self.log.info('Rol de muteado eliminado a "%s", server "%s"', member.display_name, server)

        await asyncio.sleep(5)
        if not self.bot.is_closed:
            self.bot.loop.create_task(self.task())

    @staticmethod
    def timediff_parse(timediff):
        timediff = timediff.lower()
        result = datetime.timedelta(minutes=0)
        if Mute.rx_timediff_all.match(timediff) is None:
            return result

        times = Mute.rx_timediff.findall(timediff)
        ds = {'s': 0, 'm': 0, 'h': 0, 'd': 0}

        for t in times:
            mult = 's' if t[-1] not in 'smhd' else t[-1]
            ds[mult] += int(0 if t[:-1] == '' else t[:-1])

        return datetime.timedelta(seconds=ds['s'], minutes=ds['m'], hours=ds['h'], days=ds['d'])

    @staticmethod
    def deltatime_to_str(deltatime):
        result = []
        if deltatime.days > 0:
            result.append(deltatime.days + ' día{}'.format('' if deltatime.days == 1 else 's'))
        m, s = divmod(deltatime.seconds, 60)
        h, m = divmod(m, 60)

        if h > 0:
            result.append(str(h) + ' hora{}'.format('' if h == 1 else 's'))
        if m > 0:
            result.append(str(m) + ' minuto{}'.format('' if m == 1 else 's'))
        if s > 0:
            result.append(str(s) + ' segundo{}'.format('' if s == 1 else 's'))

        return ', '.join(result)


class Unmute(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'unmute'
        self.help = 'Quita el mute de usuarios'
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, message, cmd):
        if len(cmd.args) != 1 or len(message.mentions) != 1:
            await cmd.answer('Formato: !unmute <@mención>')
            return

        member = message.mentions[0]
        mutedrole = Command.get_server_role(message.server, Mute.muted_role)

        if mutedrole is None:
            await cmd.answer('El usuario no tiene el rol de muteado ({})'.format(Mute.muted_role))
            return

        try:
            muteduser = MutedUser.get(MutedUser.userid == member.id)
            muteduser.delete()
        except MutedUser.DoesNotExist:
            pass

        await self.bot.remove_roles(member, mutedrole)
        await cmd.answer('Usuario desmuteado!')


class MuteTimeLeft(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['muteleft', 'mutetime']
        self.help = 'Muestra cuanto tiempo queda de mute'
        self.user_delay = 10

    async def handle(self, message, cmd):
        # TODO: Implementar este comando
        await cmd.answer('Este comando aún no está disponible!')


class MutedUser(BaseModel):
    userid = peewee.TextField(null=False)
    serverid = peewee.TextField(null=False)
    until = peewee.DateTimeField(null=True)
    reason = peewee.TextField(default='')
    author_name = peewee.TextField(null=False)
    author_id = peewee.TextField(null=False)
