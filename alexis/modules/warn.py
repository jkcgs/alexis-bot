from datetime import datetime

import discord
import peewee
from discord import Embed

from alexis import Command
from alexis.base.database import BaseModel


class Warn(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'warn'
        self.aliases = ['warning']
        self.help = 'Advertir a un usuario'
        self.allow_pm = False
        self.owner_only = True
        self.db_models = [UserWarn]

    async def handle(self, message, cmd):
        if len(cmd.args) < 2:
            await cmd.answer('Formato: $PX$NM <id, mención> <razón>')
            return

        member = await cmd.get_user(cmd.args[0], member_only=True)
        server = message.server
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
        await cmd.answer('A **{}** se le ha dado una advertencia por: **{}**! Ahora tiene {} {}.'
                         .format(member.display_name, reason, num, adv))


class Warns(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'warns'
        self.aliases = ['warnings']
        self.help = 'Muestra el número de advertencias que tiene el usuario'
        self.allow_pm = False

    async def handle(self, message, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('Formato: $PX$NM <id, mención>')
            return

        member = await cmd.get_user(cmd.args[0], member_only=True)
        await cmd.typing()

        if member is None:
            await cmd.answer('no se encontró al usuario')
            return

        # TODO: Listar
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
        self.aliases = ['clearwarnings']
        self.help = 'Elimina las advertencias del usuario'
        self.allow_pm = False
        self.owner_only = True

    async def handle(self, message, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('Formato: $PX$NM <id, mención>')
            return

        member = await cmd.get_user(cmd.args[0], member_only=True)
        await cmd.typing()

        if member is None:
            await cmd.answer('no se encontró al usuario')
            return

        if get_member_warns(member).count() == 0:
            await cmd.answer('el usuario no tiene advertencias')
            return

        UserWarn.delete().where(UserWarn.serverid == message.server.id, UserWarn.userid == member.id).execute()
        await cmd.answer('advertencias eliminadas para **{}**'.format(member.display_name))


class WarnList(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'warnlist'
        self.help = 'Muestra el número de advertencias que tiene el usuario'
        self.allow_pm = False
        self.owner_only = True

    async def handle(self, message, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('Formato: $PX$NM <id, mención>')
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
        for warn in warns.iterator():
            fdate = warn.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            warnlist.append('`[{}]` {}'.format(fdate, warn.reason))

        msg = '**{}** tiene {} {}.'.format(member.display_name, num, adv)
        emb = Embed()
        emb.description = '\n'.join(warnlist)
        await cmd.answer(msg, embed=emb)


def get_member_warns(member):
    if not isinstance(member, discord.Member):
        raise RuntimeError('The member argument value is not an instance of discord.Member')

    return UserWarn.select().where(UserWarn.serverid == member.server.id, UserWarn.userid == member.id)


class UserWarn(BaseModel):
    serverid = peewee.TextField()
    userid = peewee.TextField()
    reason = peewee.TextField()
    timestamp = peewee.DateTimeField(default=datetime.now)
