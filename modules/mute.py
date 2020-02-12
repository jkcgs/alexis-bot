import re
import datetime
from datetime import datetime as dt

import discord
import peewee

from bot import Command, utils, categories, BaseModel
from bot.guild_configuration import GuildConfiguration
from bot.utils import auto_int


class MutedUser(BaseModel):
    userid = peewee.TextField(null=False)
    serverid = peewee.TextField(null=False)
    until = peewee.DateTimeField(null=True)
    reason = peewee.TextField(default='')
    author_name = peewee.TextField(null=False)
    author_id = peewee.TextField(null=False)


class Mute(Command):
    __version__ = '1.0.1'
    __author__ = 'makzk'

    default_muted_role = 'Muted'
    cfg_muted_role = 'muted_role'
    rx_timediff_all = re.compile('^([0-9]+[smhdSMDH]?)+$')
    rx_timediff = re.compile('([0-9]+[smhdSMDH]?)')
    db_models = [MutedUser]

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'mute'
        self.help = '$[mute-help]'
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.MODERATION
        self.schedule = (self.mute_task, 5)

    async def handle(self, cmd):
        if cmd.argc < 1:
            delta = Mute.current_delta(cmd.author.id, cmd.message.guild.id)
            if delta is None:
                await cmd.answer('$[mute-actually-not]')
            else:
                await cmd.answer('$[mute-remaining]', locales={'time': delta})
            return

        if cmd.args[0] == 'list':
            curr = self.current_server_deltas(cmd.message.guild.id)
            x = ['- {} ({})'.format(getattr(user, 'display_name', str(user)), delta) for user, delta in curr]
            await cmd.answer('$[mute-list]\n{}'.format('\n'.join(x)), locales={'muted_amount': len(curr)})
            return

        sv_role = cmd.config.get(Mute.cfg_muted_role, Mute.default_muted_role)
        member = cmd.get_member(cmd.args[0])
        guild = cmd.message.guild
        await cmd.typing()

        if member is None:
            await cmd.answer('$[user-not-found]')
            return

        if member.id == self.bot.user.id:
            await cmd.answer('$[mute-err-bot]')
            return

        if member.id == cmd.author.id:
            await cmd.answer('$[mute-err-self]')
            return

        # Check if roles can be managed
        if not cmd.can_manage_roles():
            self.log.warning('I can\'t manage roles on guild: %s', str(guild))
            await cmd.answer('$[mute-err-perms]')
            return

        # Get mute time
        until = None
        deltatime = None
        if len(cmd.args) > 1:
            if Mute.rx_timediff_all.match(cmd.args[1]) is None:
                await cmd.answer('$[mute-err-time]')
                return

            deltatime = Mute.timediff_parse(cmd.args[1])
            until = dt.now() + deltatime

        str_deltatime = '' if deltatime is None else ' ' + cmd.lang.format('$[mute-time]', locales={
            'delta_time': utils.deltatime_to_str(deltatime)})
        if deltatime is not None and str_deltatime == '':
            await cmd.answer('$[mute-err-unmute]')
            return

        # Remove mute from DB if user was already muted (i.e. change the mute time)
        MutedUser.delete().where(MutedUser.userid == member.id).execute()

        # Check if the user already has the role
        mutedrole = None
        for role in member.roles:
            if role.name == sv_role:
                mutedrole = role
                break

        # Add the muted role only if the user does not have it
        if mutedrole is None:
            mutedrole = utils.get_guild_role(guild, sv_role)
            # if mutedrole is still None
            if mutedrole is None:
                self.log.warning('Role "%s" does not exist (guild: %s)', sv_role, guild)
                await cmd.answer('$[mute-err-noex-role]', locales={'muted_role': sv_role})
                return

            await member.add_roles(mutedrole)

        reason = ' '.join(cmd.args[2:]).strip()
        str_reason = (' ' + cmd.lang.format('$[mute-reason]', locales={'reason': reason})) if reason != '' else ''
        MutedUser.insert(userid=member.id, serverid=guild.id, until=until, reason=reason,
                         author_name=str(cmd.author), author_id=cmd.author.id).execute()

        # Tell the user about the mute, via PM
        if not member.bot:
            try:
                await self.bot.send_message(member, '$[mute-msg]{}{}.'.format(str_deltatime, str_reason),
                                            locales={'server_name': guild.name})
            except discord.errors.Forbidden as e:
                self.log.exception(e)

        # Answer to the mute command with information about the mute
        await cmd.answer('$[mute-answer]{}{}!'.format(str_deltatime, str_reason),
                         locales={'username': member.display_name})

    # Restore the mute role if user left and joined the guild again
    async def on_member_join(self, member):
        guild = member.guild
        if not guild.me.guild_permissions.manage_roles:
            self.log.warning('Can\'t manage roles on the guild %s (%s)', str(guild), guild.id)
            return

        mgr = GuildConfiguration.get_instance(member.guild)
        sv_role = mgr.get(Mute.cfg_muted_role, Mute.default_muted_role)
        role = utils.get_guild_role(guild, sv_role)
        if role is None:
            self.log.warning('Role "%s" does not exist (guild: %s)', sv_role, guild)
            return

        try:
            MutedUser.get((MutedUser.until > dt.now()) | MutedUser.until.is_null(),
                          MutedUser.userid == member.id)
            member.add_roles(role)
            self.log.info('Muted role added to "%s", guild "%s"', member.display_name, guild)
            return
        except MutedUser.DoesNotExist:
            pass

    # Removes muted role once the mute time has ended
    async def mute_task(self):
        muted = MutedUser.select().where((MutedUser.until <= dt.now()) & MutedUser.until.is_null(False))
        for muteduser in muted:
            guildid = auto_int(muteduser.serverid)
            mutedid = auto_int(muteduser.userid)

            guild = self.bot.get_guild(guildid)
            if guild is None:
                self.log.debug('Guild ID %s not found', guildid)
                continue

            if not guild.me.guild_permissions.manage_roles:
                self.log.warning('I can\'t manage roles on guild: %s', guild)
                continue

            config = GuildConfiguration.get_instance(guild)
            guild_role = config.get(Mute.cfg_muted_role, Mute.default_muted_role)
            member = guild.get_member(mutedid)
            role = utils.get_guild_role(guild, guild_role)

            if role is None:
                self.log.warning('Role "%s" does not exist (guild: %s)', guild_role, guild)
                continue
            elif member is None:
                # self.log.warning('Member ID %s not found (guild: %s)', mutedid, guild)
                continue
            else:
                await member.remove_roles(role)
                MutedUser.delete_instance(muteduser)
                self.log.info('Muted role removed from "%s", guild "%s"', member.display_name, guild)

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
        self.help = '$[unmute-help]'
        self.format = '$[unmute-format]'
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.MODERATION

    async def handle(self, cmd):
        if len(cmd.args) != 1:
            await cmd.answer('$[format]: $[unmute-format]')
            return

        member = cmd.get_member(cmd.args[0])
        if member is None:
            await cmd.answer('$[user-not-found]')
            return

        sv_role = cmd.config.get(Mute.cfg_muted_role, Mute.default_muted_role)
        mutedrole = utils.get_guild_role(cmd.message.guild, sv_role)

        if mutedrole is None:
            await cmd.answer('$[unmute-no-muted-role]'.format(sv_role), locales={'role_name'})
            return

        try:
            await member.remove_roles(mutedrole)
        except discord.errors.Forbidden:
            await cmd.answer('$[unmute-err-perms]')
            return

        try:
            muteduser = MutedUser.get(MutedUser.userid == member.id)
            muteduser.delete()
        except MutedUser.DoesNotExist:
            pass

        await cmd.answer('$[unmute-done]')


class SetMutedRole(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'setmutedrole'
        self.aliases = ['mutedrole']
        self.help = '$[mutedrole-help]'
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.STAFF

    async def handle(self, cmd):
        if len(cmd.args) != 1:
            await cmd.answer('$[format]: $[mutedrole-format]')
            return

        r = utils.get_guild_role(cmd.message.guild, cmd.args[0])
        if r is None:
            await cmd.answer('$[mute-err-noex-role]', locales={'muted_role': cmd.args[0]})
            return

        cmd.config.set(Mute.cfg_muted_role, cmd.args[0])
        await cmd.answer('$[mutedrole-set]', locales={'muted_role': cmd.args[0]})
