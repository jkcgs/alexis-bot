from datetime import datetime

import discord
import peewee
from discord import Embed

from bot import Command, categories, BaseModel
from bot.utils import is_int


class UserWarn(BaseModel):
    serverid = peewee.TextField()
    userid = peewee.TextField()
    reason = peewee.TextField()
    timestamp = peewee.DateTimeField(default=datetime.now)


class Warn(Command):
    db_models = [UserWarn]

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'warn'
        self.aliases = ['warning']
        self.help = '$[warn-help]'
        self.allow_pm = False
        self.owner_only = True
        self.category = categories.MODERATION

    async def handle(self, cmd):
        if len(cmd.args) < 2:
            await cmd.answer('$[format]: $[warn-format]')
            return

        member = cmd.get_member(cmd.args[0])
        guild = cmd.message.guild
        await cmd.typing()

        if member is None:
            await cmd.answer('$[user-not-found]')
            return

        if member.id == self.bot.user.id:
            await cmd.answer('$[warn-err-bot]')
            return

        if member.id == cmd.author.id:
            await cmd.answer('$[warn-err-self]')
            return

        reason = ' '.join(cmd.args[1:])
        UserWarn.create(serverid=guild.id, userid=member.id, reason=reason)
        num = get_member_warns(member).count()
        adv = ['$[warn-now]', '$[warn-now-single]'][num == 1]

        # Tell user via PM about the warn
        try:
            await self.bot.send_message(member, '$[warn-msg] {}'.format(adv),
                                        locales={'guild_name': guild.name, 'reason': reason, 'count': num})
        except discord.errors.Forbidden as e:
            self.log.exception(e)

        # Answer to the command with warn information
        adv = ['$[warn-answer-count]', '$[warn-answer-count-single]'][num == 1]
        msg = '$[warn-answer] {}'.format(adv)
        await cmd.answer(msg, locales={'username': member.display_name, 'reason': reason, 'count': num})
        # await ModLog.send_modlog(cmd, message=msg)


class Warns(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'warns'
        self.aliases = ['warnings']
        self.help = '$[warns-help]'
        self.allow_pm = False
        self.category = categories.MODERATION

    async def handle(self, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('$[format]: $[warns-format]')
            return

        member = cmd.get_member(cmd.args[0])
        await cmd.typing()

        if member is None:
            await cmd.answer('$[user-not-found]')
            return

        num = get_member_warns(member).count()
        if num > 0:
            if num == 1:
                await cmd.answer('$[warns-has-single]', locales={'username': member.display_name})
            else:
                await cmd.answer('$[warns-has]', locales={'username': member.display_name, 'count': num})
        else:
            await cmd.answer('$[warns-hasnt]', locales={'username': member.display_name})


class ClearWarns(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'clearwarns'
        self.aliases = ['clearwarnings', 'unwarn']
        self.help = '$[clrw-format]'
        self.allow_pm = False
        self.owner_only = True
        self.category = categories.STAFF

    async def handle(self, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('$[format]: $[clrw-format]')
            return

        member = cmd.get_member(cmd.args[0])
        await cmd.typing()

        if member is None:
            await cmd.answer('$[user-not-found]')
            return

        if get_member_warns(member).count() == 0:
            await cmd.answer('$[clrw-hasnt]')
            return

        UserWarn.delete().where(UserWarn.serverid == cmd.message.guild.id, UserWarn.userid == member.id).execute()
        await cmd.answer('$[clrw-cleared]', locales={'username': member.display_name})


class DeleteWarn(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'deletewarn'
        self.aliases = ['delwarn']
        self.help = '$[delw-help]'
        self.allow_pm = False
        self.owner_only = True
        self.category = categories.STAFF

    async def handle(self, cmd):
        if len(cmd.args) < 2:
            await cmd.answer('$[delw-format]: $[delw-format]')
            return

        if not is_int(cmd.args[1]) or int(cmd.args[1]) < 1:
            await cmd.answer('$[delw-err-index]')
            return

        member = cmd.get_member(cmd.args[0])
        await cmd.typing()

        if member is None:
            await cmd.answer('$[user-not-found]')
            return

        if get_member_warns(member).count() == 0:
            await cmd.answer('$[clrw-hasnt]')
            return

        idx = int(cmd.args[1])
        warns = list(get_member_warns(member).order_by(UserWarn.timestamp.desc()))
        if len(warns) < idx:
            await cmd.answer('$[delw-err-out-of-bounds]')
            return

        UserWarn.delete_instance(warns[idx-1])
        await cmd.answer('$[delw-deleted]')


def auto_id(userid):
    pass


class WarnList(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'warnlist'
        self.help = '$[warnlist-help]'
        self.allow_pm = False
        self.owner_only = True
        self.category = categories.MODERATION

    async def handle(self, cmd):
        if len(cmd.args) < 1:
            warns = UserWarn.select().order_by(UserWarn.timestamp.desc()).limit(5)
            if warns.count() == 0:
                await cmd.answer('$[clrw-hasnt]')
                return

            warnlist = []
            for warn in warns:
                fdate = warn.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                u = cmd.get_member(warn.userid)
                if u is None:
                    u = '<@{}> ({})'.format(warn.userid, warn.userid)
                else:
                    u = u.display_name

                warnlist.append('`[{}]` {}: {}'.format(fdate, u, warn.reason))

            await cmd.answer(Embed(title='$[warnlist-last]', description='\n'.join(warnlist)))
            return

        member = cmd.get_member(cmd.args[0])
        await cmd.typing()

        if member is None:
            await cmd.answer('$[user-not-found]')
            return

        warns = get_member_warns(member).order_by(UserWarn.timestamp.desc())
        num = warns.count()

        if num == 0:
            await cmd.answer('$[warns-hasnt]', locales={'username': member.display_name})
            return

        warnlist = []
        for i, warn in enumerate(warns):
            fdate = warn.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            warnlist.append('`[{} - {}]` {}'.format(i+1, fdate, warn.reason))

        emb = Embed()
        emb.description = '\n'.join(warnlist)
        if num == 1:
            await cmd.answer('$[warns-has]', embed=emb, locales={'username': member.display_name, 'count': num})
        else:
            await cmd.answer('$[warns-has-single]', embed=emb, locales={'username': member.display_name})


class WarnRank(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'warnrank'
        self.help = '$[warnrank-help]'
        self.allow_pm = False
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        query = UserWarn.select(
            UserWarn.serverid, UserWarn.userid, UserWarn.timestamp, UserWarn.reason,
            peewee.fn.COUNT(UserWarn.userid).alias('num_warns')
        ).group_by(UserWarn.userid).order_by(peewee.fn.COUNT(UserWarn.userid).desc())

        if query.count() == 0:
            await cmd.answer('$[warnrank-none]')
            return

        msg = []
        for result in query:
            member = cmd.get_member(result.userid)
            timestr = result.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            if member is None:
                member = 'ID {}'.format(result.userid, result.userid)
            else:
                member = member.display_name

            msg.append('{} - {} ($[warnrank-last]: {}, "{}")'.format(result.num_warns, member, timestr, result.reason))

        await cmd.answer(Embed(title='$[warnrank-title]', description='\n'.join(msg)))
        return


def get_member_warns(member):
    if not isinstance(member, discord.Member):
        raise RuntimeError('The member argument value is not an instance of discord.Member')

    return UserWarn.select().where(UserWarn.serverid == member.guild.id, UserWarn.userid == member.id)
