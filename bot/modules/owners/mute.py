import asyncio
import re
import datetime
from datetime import datetime as dt

import discord
import peewee

from bot import Command, utils
from bot.libs.configuration import BaseModel


class Mute(Command):
    default_muted_role = 'Muted'
    cfg_muted_role = 'muted_role'
    rx_timediff_all = re.compile('^([0-9]+[smhdSMDH]?)+$')
    rx_timediff = re.compile('([0-9]+[smhdSMDH]?)')

    cant_manage_msg = 'no tengo permiso pa manejar roles D:'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'mute'
        self.help = 'Mutea usuarios'
        self.owner_only = True
        self.db_models = [MutedUser]
        self.allow_pm = False

    async def handle(self, cmd):
        if cmd.argc < 1:
            delta = Mute.current_delta(cmd.author.id, cmd.message.server.id)
            if delta is None:
                await cmd.answer('no estás actualmente muteado')
            else:
                await cmd.answer('te queda(n) {} de mute'.format(delta))
            return

        if cmd.args[0] == 'list':
            curr = self.current_server_deltas(cmd.message.server.id)
            x = ['- {} ({})'.format(getattr(user, 'display_name', str(user)), delta) for user, delta in curr]
            await cmd.answer('actualmente hay {} usuarios muteados:\n{}'.format(len(curr), '\n'.join(x)))
            return

        sv_role = cmd.config.get(Mute.cfg_muted_role, Mute.default_muted_role)
        member = await cmd.get_user(cmd.args[0], member_only=True)
        server = cmd.message.server
        await cmd.typing()

        if member is None:
            await cmd.answer('no se encontró al usuario')
            return

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

        # Obtener tiempo del mute
        until = None
        deltatime = None
        if len(cmd.args) > 1:
            if Mute.rx_timediff_all.match(cmd.args[1]) is None:
                await cmd.answer('tiempo de mute no válido')
                return

            deltatime = Mute.timediff_parse(cmd.args[1])
            until = dt.now() + deltatime

        str_deltatime = '' if deltatime is None else ' por ' + utils.deltatime_to_str(deltatime)
        if deltatime is not None and str_deltatime == '':
            await cmd.answer('si quieres desmutear a alguien, utiliza !unmute <user>')
            return

        # Quitar mute de la db si ya está muteado
        MutedUser.delete().where(MutedUser.userid == member.id).execute()

        # Revisar si el usuario ya tiene el rol
        mutedrole = None
        for role in member.roles:
            if role.name == sv_role:
                mutedrole = role
                break

        # Si el usuario ya tiene el rol, no es necesario agregarlo
        if mutedrole is None:
            mutedrole = utils.get_server_role(server, sv_role)
            # if mutedrole is still None
            if mutedrole is None:
                self.log.warning('El rol "%s" no existe (server: %s)', sv_role, server)
                await cmd.answer('el rol "{}" no existe!'.format(sv_role))
                return

            await self.bot.add_roles(member, mutedrole)

        reason = ' '.join(cmd.args[2:]).strip()
        str_reason = ' debido a: **{}**'.format(reason) if reason != '' else ''
        MutedUser.insert(userid=member.id, serverid=server.id, until=until, reason=reason,
                         author_name=str(cmd.author), author_id=cmd.author.id).execute()

        # Enviar PM con el aviso del mute
        try:
            await self.bot.send_message(member, 'Hola! Lamentablemente has sido muteado en el servidor **{}**{}{}.'
                                        .format(server.name, str_deltatime, str_reason))
        except discord.errors.Forbidden as e:
            self.log.exception(e)

        # Avisar por el canal donde se envió el comando
        await cmd.answer('**{}** ha sido mutead@{}{}!'.format(member.display_name, str_deltatime, str_reason))

    # Restaurar el rol de muteado una vez que el usuario ha reingresado
    async def on_member_join(self, member):
        server = member.server
        if not self.can_manage_roles(server):
            self.log.warning(Mute.cant_manage_msg)
            return

        mgr = self.config_mgr(member.server.id)
        sv_role = mgr.get(Mute.cfg_muted_role, Mute.default_muted_role)
        role = utils.get_server_role(server, sv_role)
        if role is None:
            self.log.warning('El rol "%s" no existe (server: %s)', sv_role, server)
            return

        try:
            MutedUser.get((MutedUser.until > dt.now()) | MutedUser.until.is_null(),
                          MutedUser.userid == member.id)
            self.bot.add_roles(member, role)
            self.log.info('Rol de muteado agregado a %s server %s', member.display_name, server)
            return
        except MutedUser.DoesNotExist:
            pass

    # Elimina los roles de muteado una vez que ha terminado
    async def task(self):
        try:
            muted = MutedUser.select().where((MutedUser.until <= dt.now()) & MutedUser.until.is_null(False))
            for muteduser in muted:
                server = self.bot.get_server(muteduser.serverid)
                if server is None:
                    continue

                self_member = server.get_member(self.bot.user.id)
                if self_member is not None and not self_member.server_permissions.manage_roles:
                    self.log.warning(Mute.cant_manage_msg + ' (server: %s)', server)
                    continue

                mgr = self.config_mgr(muteduser.serverid)
                sv_role = mgr.get(Mute.cfg_muted_role, Mute.default_muted_role)
                member = server.get_member(muteduser.userid)
                role = utils.get_server_role(server, sv_role)

                if role is None:
                    self.log.warning('El rol "%s" no existe (server: %s)', sv_role, server)
                    continue
                elif member is None:
                    continue
                else:
                    await self.bot.remove_roles(member, role)
                    MutedUser.delete_instance(muteduser)
                    self.log.info('Rol de muteado eliminado a "%s", server "%s"', member.display_name, server)
        except Exception as e:
            self.log.exception(e)

        await asyncio.sleep(5)
        if not self.bot.is_closed:
            self.bot.loop.create_task(self.task())

    def current_deltas_for(self, userid):
        muted = MutedUser.select().where(MutedUser.userid == userid, MutedUser.until > dt.now())
        return [(self.bot.get_server(f.serverid) or f.serverid, utils.deltatime_to_str(f.until - dt.now()))
                for f in muted]

    def current_server_deltas(self, serverid):
        muted = MutedUser.select().where(MutedUser.serverid == serverid, MutedUser.until > dt.now())
        server = self.bot.get_server(serverid)
        if server is None:
            return []

        return [(server.get_member(f.userid) or f.userid, utils.deltatime_to_str(f.until - dt.now()))
                for f in muted]

    @staticmethod
    def timediff_parse(timediff):
        timediff = timediff.lower()
        result = datetime.timedelta(minutes=0)
        if Mute.rx_timediff_all.match(timediff) is None:
            return result

        times = Mute.rx_timediff.findall(timediff)
        ds = {'s': 0, 'm': 0, 'h': 0, 'd': 0}

        for t in times:
            if t[-1] not in 'smhd':
                t += 'm'

            ds[t[-1]] += int(t[:-1])

        return datetime.timedelta(seconds=ds['s'], minutes=ds['m'], hours=ds['h'], days=ds['d'])

    @staticmethod
    def current_delta(userid, serverid):
        try:
            muted = MutedUser.get(MutedUser.userid == userid, MutedUser.serverid == serverid)

            if dt.now() > muted.until:
                return None
            else:
                return utils.deltatime_to_str(muted.until - dt.now())
        except MutedUser.DoesNotExist:
            return None


class Unmute(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'unmute'
        self.help = 'Quita el mute de usuarios'
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, cmd):
        if len(cmd.args) != 1:
            await cmd.answer('formato: !unmute <usuario, id, @mención>')
            return

        member = await cmd.get_user(cmd.args[0], member_only=True)
        if member is None:
            await cmd.answer('usuario no encontrado')
            return

        sv_role = cmd.config.get(Mute.cfg_muted_role, Mute.default_muted_role)
        mutedrole = utils.get_server_role(cmd.message.server, sv_role)

        if mutedrole is None:
            await cmd.answer('el usuario no tiene el rol de muteado ({})'.format(sv_role))
            return

        try:
            await self.bot.remove_roles(member, mutedrole)
        except discord.errors.Forbidden:
            await cmd.answer('no pude quitar el rol! Revisa los permisos del bot (¿está el rol de usuarios muteados por'
                             ' sobre el del bot?')
            return

        try:
            muteduser = MutedUser.get(MutedUser.userid == member.id)
            muteduser.delete()
        except MutedUser.DoesNotExist:
            pass

        await cmd.answer('usuario desmuteado!')


class SetMutedRole(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'setmutedrole'
        self.help = 'Determina el nombre del rol del mute'
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, cmd):
        if len(cmd.args) != 1:
            await cmd.answer('formato: $PX$NM <rol>')
            return

        r = utils.get_server_role(cmd.message.server, cmd.args[0])
        if r is None:
            await cmd.answer('el rol especificado no existe')
            return

        cmd.config.set(Mute.cfg_muted_role, cmd.args[0])
        await cmd.answer('rol definido en **{}**'.format(cmd.args[0]))


class MutedUser(BaseModel):
    userid = peewee.TextField(null=False)
    serverid = peewee.TextField(null=False)
    until = peewee.DateTimeField(null=True)
    reason = peewee.TextField(default='')
    author_name = peewee.TextField(null=False)
    author_id = peewee.TextField(null=False)
