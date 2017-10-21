import asyncio
import re
import datetime
from datetime import datetime as dt

import peewee

from modules.base.command import Command
from modules.base.database import BaseModel


class Mute(Command):
    muted_role = 'Muted'
    rx_timediff_all = re.compile('([0-9]+[smhdSMDH]?)+')
    rx_timediff = re.compile('([0-9]+[smhdSMDH]?)')

    cant_manage_msg = 'No se puede agregar el rol de muteado a un usuario porque no se dispone del permiso necesario'

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

        # Verificar si se pueden manejar roles
        if not self.can_manage_roles(server):
            self.log.warning(Mute.cant_manage_msg + ' (server: %s)', str(server))
            cmd.answer(Mute.cant_manage_msg)
            return

        # Obtener argumentos del mute
        mute_args = []
        if len(cmd.args) > 1:
            cmd.args[1:].split('|')

        # Obtener tiempo del mute
        until = None
        deltatime = None
        if len(mute_args) > 0:
            if not re.match(Mute.rx_timediff_all, mute_args[0]):
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
                return
            pass

        reason = ''
        if len(mute_args) > 1:
            reason = ' '.join(cmd.args[2:])

        MutedUser.insert(userid=member.id, serverid=server.id, until=until, reason=reason,
                         author_name=str(cmd.author), author_id=cmd.author.id).execute()

        str_deltatime = ' por **{}**'.format(Mute.timediff_parse(deltatime)) if deltatime is not None else ''

        # Enviar PM con el aviso del mute
        self.bot.send_message(member, 'Hola! Lamentablemente has sido muteado en el servidor **{}**{}.'.format(
            server.name, str_deltatime))

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
            # TODO: Manejar until correctamente
            muted = MutedUser.get(MutedUser.until > dt.now(), MutedUser.userid == member.id)
            self.bot.add_role(member, role)
            return
        except MutedUser.DoesNotExist:
            pass

    # Elimina los roles de muteado una vez que ha terminado
    async def task(self):
        # TODO: Manejar until correctamente
        muted = MutedUser.select().where(MutedUser.until <= dt.now())
        for muteduser in muted:
            server = self.bot.get_server(muteduser.serverid)
            if server is None:
                continue

            self_member = server.get_member(self.bot.id)
            if not self_member.server_permissions.manage_roles():
                self.log.warning(Mute.cant_manage_msg + ' (server: %s)', server)
                continue

            member = server.get_member(muteduser.userid)
            role = Command.get_server_role(server, Mute.muted_role)
            if role is None:
                self.log.warning('El rol "%s" no existe (server: %s)', Mute.muted_role, server)
                continue
            else:
                self.bot.remove_role(member, role)

        await asyncio.sleep(5)
        if not self.bot.is_closed:
            self.bot.loop.create_task(self.task())

    @staticmethod
    def timediff_parse(timediff):
        # TODO: Buscar forma de interpretar duración
        result = datetime.timedelta(minutes=15)
        return result

    @staticmethod
    def deltatime_to_str(deltatime):
        # TODO: timediff a string
        return 'x tiempo'


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
        mutedrole = None
        for role in member.roles:
            if role.name == Mute.muted_role:
                mutedrole = role
                break

        if mutedrole is None:
            await cmd.answer('El usuario no tiene el rol de muteado ({})'.format(Mute.muted_role))
            return

        try:
            muteduser = MutedUser.get(MutedUser.userid == member.id)
            muteduser.delete()
        except MutedUser.DoesNotExist:
            pass

        self.bot.remove_role(member, mutedrole)
        await cmd.answer('Usuario desmuteado!')


class MutedUser(BaseModel):
    userid = peewee.TextField(null=False)
    serverid = peewee.TextField(null=False)
    until = peewee.DateTimeField()
    reason = peewee.TextField(default='')
    author_name = peewee.TextField(null=False)
    author_id = peewee.TextField(null=False)
