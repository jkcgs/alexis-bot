from datetime import datetime

import discord
import peewee
from discord import Embed

from bot import Command
from bot.utils import is_int
from bot.libs.configuration import BaseModel


class Warn(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'warn'
        self.aliases = ['warning']
        self.help = 'Advertir a un usuario'
        self.allow_pm = False
        self.owner_only = True
        self.db_models = [UserWarn]

    async def handle(self, cmd):
        if len(cmd.args) < 2:
            await cmd.answer('formato: $PX$NM <id, mención> <razón>')
            return

        member = await cmd.get_user(cmd.args[0], member_only=True)
        server = cmd.message.server
        await cmd.typing()

        if member is None:
            await cmd.answer('no se encontró al usuario')
            return

        if member.id == self.bot.user.id:
            await cmd.answer('oye pero no po si no hice nada')
            return

        if member.id == cmd.author.id:
            await cmd.answer('jajajajajajajaj ya.')
            return

        reason = ' '.join(cmd.args[1:])
        UserWarn.create(serverid=server.id, userid=member.id, reason=reason)
        num = get_member_warns(member).count()
        adv = ['advertencias', 'advertencia'][bool(num == 1)]

        # Enviar PM con el aviso de la advertencia
        try:
            await self.bot.send_message(member, 'Hola! Se te ha dado una advertencia en el servidor **{}** por *{}*. '
                                                'Ahora tienes {} {}.'.format(server.name, reason, num, adv))
        except discord.errors.Forbidden as e:
            self.log.exception(e)

        # Avisar por el canal donde se envió el comando
        msg = 'a **{}** se le ha dado una advertencia por: **{}**! Ahora tiene {} {}.'.format(
            member.display_name, reason, num, adv)
        await cmd.answer(msg)
        # await ModLog.send_modlog(cmd, message=msg)


class Warns(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'warns'
        self.aliases = ['warnings']
        self.help = 'Muestra el número de advertencias que tiene el usuario'
        self.allow_pm = False

    async def handle(self, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('formato: $PX$NM <id, mención>')
            return

        member = await cmd.get_user(cmd.args[0], member_only=True)
        await cmd.typing()

        if member is None:
            await cmd.answer('no se encontró al usuario')
            return

        num = get_member_warns(member).count()
        adv = ['advertencias', 'advertencia'][bool(num == 1)]
        if num > 0:
            await cmd.answer('**{}** tiene {} {}.'.format(member.display_name, num, adv))
        else:
            await cmd.answer('**{}** no tiene advertencias :3'.format(member.display_name, num, adv))


class ClearWarns(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'clearwarns'
        self.aliases = ['clearwarnings', 'unwarn']
        self.help = 'Elimina las advertencias del usuario'
        self.allow_pm = False
        self.owner_only = True

    async def handle(self, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('formato: $PX$NM <id, mención>')
            return

        member = await cmd.get_user(cmd.args[0], member_only=True)
        await cmd.typing()

        if member is None:
            await cmd.answer('no se encontró al usuario')
            return

        if get_member_warns(member).count() == 0:
            await cmd.answer('el usuario no tiene advertencias')
            return

        UserWarn.delete().where(UserWarn.serverid == cmd.message.server.id, UserWarn.userid == member.id).execute()
        await cmd.answer('advertencias eliminadas para **{}**'.format(member.display_name))


class DeleteWarn(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'deletewarn'
        self.aliases = ['delwarn']
        self.help = 'Elimina una advertencia de un usuario, según el número de warn del comando $PXwarnlist'
        self.allow_pm = False
        self.owner_only = True

    async def handle(self, cmd):
        if len(cmd.args) < 2:
            await cmd.answer('formato: $PX$NM <id, mención> <índice>')
            return

        if not is_int(cmd.args[1]) or int(cmd.args[1]) < 1:
            await cmd.answer('el índice debe ser un número entero mayor que cero')
            return

        member = await cmd.get_user(cmd.args[0], member_only=True)
        await cmd.typing()

        if member is None:
            await cmd.answer('no se encontró al usuario')
            return

        if get_member_warns(member).count() == 0:
            await cmd.answer('el usuario no tiene advertencias')
            return

        idx = int(cmd.args[1])
        warns = list(get_member_warns(member).order_by(UserWarn.timestamp.desc()))
        if len(warns) < idx:
            await cmd.answer('índice de advertencia fuera de rango')
            return

        UserWarn.delete_instance(warns[idx-1])
        await cmd.answer('advertencia eliminada')


class WarnList(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'warnlist'
        self.help = 'Muestra las últimas advertencias o el número de advertencias que tiene el usuario'
        self.allow_pm = False
        self.owner_only = True

    async def handle(self, cmd):
        if len(cmd.args) < 1:
            warns = UserWarn.select().order_by(UserWarn.timestamp.desc()).limit(5)
            if warns.count() == 0:
                await cmd.answer('no hay advertencias registradas')
                return

            warnlist = []
            for warn in warns:
                fdate = warn.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                u = cmd.message.server.get_member(warn.userid)
                if u is None:
                    u = '<@{}> ({})'.format(warn.userid, warn.userid)
                else:
                    u = u.display_name

                warnlist.append('`[{}]` {}: {}'.format(fdate, u, warn.reason))

            await cmd.answer(Embed(title='Últimas advertencias', description='\n'.join(warnlist)))
            return

        member = await cmd.get_user(cmd.args[0], member_only=True)
        await cmd.typing()

        if member is None:
            await cmd.answer('no se encontró al usuario')
            return

        warns = get_member_warns(member).order_by(UserWarn.timestamp.desc())
        num = warns.count()
        adv = ['advertencias', 'advertencia'][bool(num == 1)]

        if num == 0:
            await cmd.answer('**{}** no tiene advertencias :3'.format(member.display_name))
            return

        warnlist = []
        for i, warn in enumerate(warns):
            fdate = warn.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            warnlist.append('`[{} - {}]` {}'.format(i+1, fdate, warn.reason))

        msg = '**{}** tiene {} {}.'.format(member.display_name, num, adv)
        emb = Embed()
        emb.description = '\n'.join(warnlist)
        await cmd.answer(msg, embed=emb)


class WarnRank(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'warnrank'
        self.help = 'Muestra un ránking de advertencias'
        self.allow_pm = False

    async def handle(self, cmd):
        e = UserWarn.select(UserWarn.serverid, UserWarn.userid, UserWarn.timestamp, UserWarn.reason,
                            peewee.fn.COUNT(UserWarn.userid).alias('num_warns')) \
            .group_by(UserWarn.userid) \
            .order_by(peewee.fn.COUNT(UserWarn.userid).desc())

        if e.count() == 0:
            await cmd.answer('no hay registros de warns')
            return

        msg = []
        for xd in e:
            u = cmd.message.server.get_member(xd.userid)
            d = xd.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            if u is None:
                u = 'ID {}'.format(xd.userid, xd.userid)
            else:
                u = u.display_name

            msg.append('{} - {} (último: {}, "{}")'.format(xd.num_warns, u, d, xd.reason))

        await cmd.answer(Embed(title='Ranking de advertencias', description='\n'.join(msg)))
        return


def get_member_warns(member):
    if not isinstance(member, discord.Member):
        raise RuntimeError('The member argument value is not an instance of discord.Member')

    return UserWarn.select().where(UserWarn.serverid == member.server.id, UserWarn.userid == member.id)


class UserWarn(BaseModel):
    serverid = peewee.TextField()
    userid = peewee.TextField()
    reason = peewee.TextField()
    timestamp = peewee.DateTimeField(default=datetime.now)
