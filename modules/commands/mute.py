import asyncio
from datetime import datetime

import peewee

from modules.base.command import Command
from modules.base.database import BaseModel


class Mute(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'mute'
        self.help = 'Mutea usuarios'
        self.owner_only = True
        self.db_models = [MutedUser]
        self.run_task = True

        self.muted_role = 'Muted'

    async def handle(self, message, cmd):
        if len(cmd.args) < 1 or len(message.mentions) != 1:
            await cmd.answer('Formato: !mute <@mención> [duración] [razón]')
            return

        # TODO: Buscar forma de interpretar duración
        # TODO: Agregar rol
        # TODO: Avisar mediante PM
        await cmd.answer('Este comando aún no está listo')

    # Restaurar el rol de muteado una vez que el usuario ha reingresado
    async def on_member_join(self, member):
        server = member.server
        self_member = server.get_member(self.bot.id)
        if not self_member.server_permissions.manage_roles():
            self.log.warning('No se puede agregar el rol de muteado a un usuario porque '
                             'no se dispone del permiso necesario')
            return

        role = Command.get_server_role(server, self.muted_role)
        if role is None:
            self.log.warning('El rol "%s" no existe (server: %s)', self.muted_role, server)
            return

        try:
            muted = MutedUser.get(MutedUser.until > datetime.now(), MutedUser.userid == member.id)
            self.bot.add_role(member, role)
            return
        except MutedUser.DoesNotExist:
            pass

    # Elimina los roles de muteado una vez que ha terminado
    async def task(self):
        muted = MutedUser.select().where(MutedUser.until <= datetime.now())
        for muteduser in muted:
            server = self.bot.get_server(muteduser.serverid)
            if server is None:
                continue

            self_member = server.get_member(self.bot.id)
            if not self_member.server_permissions.manage_roles():
                self.log.warning('No se puede eliminar el rol de muteado a un usuario porque '
                                 'no se dispone del permiso necesario (server: %s)', server)
                continue

            member = server.get_member(muteduser.userid)
            role = Command.get_server_role(server, self.muted_role)
            if role is None:
                self.log.warning('El rol "%s" no existe (server: %s)', self.muted_role, server)
                continue
            else:
                self.bot.remove_role(member, role)

        await asyncio.sleep(5)
        if not self.bot.is_closed:
            self.bot.loop.create_task(self.task())


class Unmute(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'unmute'
        self.help = 'Quita el mute de usuarios'
        self.owner_only = True

    async def handle(self, message, cmd):
        if len(cmd.args) != 1 or len(message.mentions) != 1:
            await cmd.answer('Formato: !unmute <@mención>')
            return

        # TODO: Quitar rol
        await cmd.answer('Este comando aún no está listo')


class MutedUser(BaseModel):
    userid = peewee.TextField(null=False)
    serverid = peewee.TextField(null=False)
    until = peewee.DateTimeField(default=datetime.now)
    reason = peewee.TextField(default='')
    author = peewee.TextField(null=False)
