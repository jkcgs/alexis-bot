import re
from datetime import datetime

import discord
import peewee
from discord.http import Route

from bot import Command, utils, categories
from discord import Embed

from bot.libs.configuration import BaseModel
from bot.utils import deltatime_to_str


class ModLog(Command):
    rx_channel = re.compile('^<#[0-9]+>$')
    chan_config_name = 'join_send_channel'

    def __init__(self, bot):
        super().__init__(bot)

    async def on_member_join(self, member):
        await self.bot.send_modlog(
            member.server, '$[modlog-new-user]',
            embed=ModLog.gen_embed(member, more=True), locales={'mid': member.id})

    async def on_member_remove(self, member):
        dt = deltatime_to_str(datetime.now() - member.joined_at)
        await self.bot.send_modlog(member.server, '$[modlog-user-left]',
                                   locales={'mid': member.id, 'username': str(member), 'dt': dt})

    async def on_message_delete(self, message):
        if message.server is None or message.author.id == self.bot.user.id:
            return

        footer = '$[modlog-msg-sent]: ' + utils.format_date(message.timestamp)
        if message.edited_timestamp is not None:
            footer += ', $[modlog-msg-edited]: ' + utils.format_date(message.edited_timestamp)

        embed = Embed(description='($[modlog-no-text])' if message.content == '' else message.content)
        embed.set_footer(text=footer)
        if len(message.attachments) > 0:
            with_img = False
            if 'width' in message.attachments[0] is not None:
                fn_value = '[{}]({})'.format(message.attachments[0]['filename'], message.attachments[0]['url'])
                embed.set_image(url=message.attachments[0]['url'])
                embed.add_field(name='$[modlog-file-name]', value=fn_value)
                with_img = True

            if with_img and len(message.attachments) > 1 or not with_img:
                i = 1 if with_img else 0
                x = ['[{}]({})'.format(f['filename'], f['url']) for f in message.attachments[i:]]
                t = [
                        ['$[modlog-attatched]', '$[modlog-attached-other]'],
                        ['$[modlog-attached-single]', '$[modlog-attached-other-single]']
                    ][int(len(x) == 1)][i]
                embed.add_field(name=t, value=', '.join(x))

        msg = '$[modlog-user-deleted-msg]'
        locales = {'username': message.author.display_name, 'channel_name': message.channel.mention}
        if message.id in self.bot.deleted_messages:
            if message.id in self.bot.deleted_messages_nolog:
                self.bot.deleted_messages_nolog.remove(message.id)
                return
            else:
                msg = '$[modlog-bot-deleted-msg]'
        else:
            try:
                last = await self.get_last_alog(message.server.id)
                if last['action_type'] == 72 and last['options']['channel_id'] == message.channel.id and \
                        last['target_id'] == message.author.id:
                    who = last['user_id']
                    if who == self.bot.user.id:
                        msg = '$[modlog-bot-deleted-msg]'
                    else:
                        u = message.server.get_member(who)
                        u = '<@' + who + '>' if u is None else u.display_name

                        locales['deleter_name'] = u
                        msg = '$[modlog-user-deleted-other]'
            except discord.Forbidden:
                msg = '$[modlog-somehow-deleted-msg]'

        await self.bot.send_modlog(message.server, msg, embed=embed, locales=locales)

    async def get_last_alog(self, guild_id):
        x = await self.bot.http.request(Route('GET', '/guilds/{guild_id}/audit-logs', guild_id=guild_id))
        x = x['audit_log_entries']
        if len(x) == 0:
            return None

        return x[0]

    @staticmethod
    def get_note(member):
        if not isinstance(member, discord.Member):
            raise RuntimeError('member argument can only be a discord.Member')

        xd, _ = UserNote.get_or_create(serverid=member.server.id, userid=member.id)
        return xd.note

    @staticmethod
    def set_note(member, note):
        if not isinstance(member, discord.Member):
            raise RuntimeError('member argument can only be a discord.Member')

        xd, _ = UserNote.get_or_create(serverid=member.server.id, userid=member.id)
        xd.note = note
        xd.save()

    @staticmethod
    def get_names(userid):
        xd = UserNameReg.select().where(UserNameReg.userid == userid).order_by(UserNameReg.timestamp.desc()).limit(10)
        return [u.name for u in xd]

    @staticmethod
    def gen_embed(member, more=False):
        embed = Embed()
        embed.add_field(name='$[modlog-e-name]', value=str(member))
        embed.add_field(name='$[modlog-e-nick]', value=member.nick if member.nick is not None else '$[modlog-no-nick]')
        embed.add_field(name='$[modlog-e-user-created]', value=utils.format_date(member.created_at))
        embed.add_field(name='$[modlog-e-user-join]', value=utils.format_date(member.joined_at))
        embed.add_field(name='$[modlog-e-stance]',
                        value=deltatime_to_str(datetime.now() - member.joined_at), inline=False)

        if member.avatar_url != '':
            embed.set_thumbnail(url=member.avatar_url)
        else:
            embed.set_thumbnail(url=member.default_avatar_url)

        if more and isinstance(member, discord.Member):
            n = ModLog.get_note(member)
            names = ModLog.get_names(member.id)
            if len(names) == 0:
                names = [member.name]

            embed.add_field(name='$[modlog-e-notes]', value=n if n != '' else '$[modlog-no-notes]')
            embed.add_field(name='$[modlog-e-names]', value=', '.join(names))
            embed.add_field(name='$[modlog-e-age]', value=deltatime_to_str(member.joined_at - member.created_at))

        return embed


class UserCommand(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'user'
        self.aliases = [bot.config['command_prefix'] + 'user']
        self.help = '$[modlog-cmd-help]'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        if cmd.cmdname == self.aliases[0] and not cmd.owner:
            return

        if cmd.argc == 0:
            user = cmd.author
        else:
            user = await cmd.get_user(cmd.text, member_only=True)
            if user is None:
                await cmd.answer('$[user-not-found]')
                return

        with_notes = cmd.cmdname == self.aliases[0] and cmd.owner
        embed = ModLog.gen_embed(user, with_notes)
        await cmd.answer('$[modlog-cmd-title]', embed=embed, locales={'user_id': user.id})


class ModLogChannel(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'logchannel'
        self.help = '$[modlog-channel-help]'
        self.format = '$[modlog-cmd-format'
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.STAFF

    async def handle(self, cmd):
        if cmd.argc != 1:
            await cmd.answer('$[format]: $[modlog-channel-format]')
            return

        chan = cmd.args[0]
        if chan != 'off' and not ModLog.rx_channel.match(chan):
            await cmd.answer('$[modlog-channel-err-off]')
            return

        value = '' if chan == 'off' else chan[2:-1]
        cmd.config.set(ModLog.chan_config_name, value)

        if value == '':
            await cmd.answer('$[modlog-channel-off]')
        else:
            await cmd.answer('$[modlog-channel-set]', locales={'channel_id': value})


class UserNoteCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'usernote'
        self.help = '$[modlog-note-help]'
        self.db_models = [UserNote]
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.STAFF

    async def handle(self, cmd):
        if cmd.argc < 1:
            return

        member = await cmd.get_user(cmd.args[0], member_only=True)
        if member is None:
            await cmd.answer('$[user-not-found]')
            return

        note = ' '.join(cmd.args[1:])
        if len(note) > 1000:
            await cmd.answer('$[modlog-note-err-length]')
            return

        ModLog.set_note(member, ' '.join(cmd.args[1:]))
        await cmd.answer('$[modlog-note-set]')


class UpdateUsername(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.db_models = [UserNameReg]
        self.updating = False
        self.updated = False

    async def on_ready(self):
        if self.updating or self.updated:
            return

        self.log.debug('Updating users\' names...')
        c = self.all()

        if c is not None:
            self.log.debug('Users updated: %i', c)

    async def on_member_join(self, member):
        if not self.updating:
            self.do_it(member)

    async def on_member_update(self, before, after):
        if not self.updating:
            self.do_it(after)

        server = after.server

        if before.name != after.name:
            if after.display_name != after.name:
                await self.bot.send_modlog(
                    server, '$[modlog-username-changed-nick]',
                    locales={'prev_name': before.name, 'new_name': after.name, 'nick': after.display_name})
            else:
                await self.bot.send_message(
                    server, '$[modlog-username-changed]',
                    locales={'prev_name': before.name, 'new_name': after.name})

        if (before.nick or after.nick) and before.nick != after.nick:
            if not before.nick and after.nick:
                await self.bot.send_modlog(server, '**{}**\'s nick set to "{}"'.format(after.name, after.nick))
            elif before.nick and not after.nick:
                await self.bot.send_modlog(server, '**{}**\'s nick removed (it was "{}")'.format(
                    after.name, before.nick))
            else:
                await self.bot.send_modlog(server, '**{}**\'s nick updated (before: "{}", after: "{}")'.format(
                    after.name, before.nick, after.nick))

    def all(self):
        if self.updating or self.updated:
            return

        self.updating = True

        # Retrieve every last user name
        # SELECT * FROM usernamereg t1 WHERE timestamp = (
        #   SELECT MAX(timestamp) FROM t1 WHERE t1.timestamp = usernamereg.timestamp
        # ) ORDER BY timestamp DESC
        u_alias = UserNameReg.alias()
        j = {u.userid: u.name for u in
             UserNameReg.select().where(
                 UserNameReg.timestamp == u_alias.select(peewee.fn.MAX(u_alias.timestamp)).where(
                     u_alias.userid == UserNameReg.userid)
             ).order_by(
                 UserNameReg.timestamp.desc()
             )}

        # Filter by unregistered users
        k = [{'userid': m.id, 'name': m.name}
             for m in self.bot.get_all_members() if m.id not in j or j[m.id] != m.name]
        k = [i for n, i in enumerate(k) if i not in k[n + 1:]]  # https://stackoverflow.com/a/9428041

        # Register new users' names
        with self.bot.db.atomic():
            for idx in range(0, len(k), 100):
                UserNameReg.insert_many(k[idx:idx + 100]).execute()

        self.updating = False
        self.updated = True
        return len(k)

    def do_it(self, user):
        if not isinstance(user, discord.User):
            raise RuntimeError('user argument can only be a discord.User')

        r = UserNameReg.select().where(UserNameReg.userid == user.id).order_by(UserNameReg.timestamp.desc()).limit(1)
        u = r.get() if r.count() > 0 else None

        if r.count() == 0 or u.name != user.name:
            old = '(none)' if u is None else u.name
            self.log.debug('Updating user name "%s" -> "%s" ID %s', old, user.name, user.id)
            UserNameReg.create(userid=user.id, name=user.name)
            return True

        return False


class UserNote(BaseModel):
    userid = peewee.TextField()
    serverid = peewee.TextField()
    note = peewee.TextField(default='')


class UserNameReg(BaseModel):
    userid = peewee.TextField()
    name = peewee.TextField()
    timestamp = peewee.DateTimeField(default=datetime.now)
