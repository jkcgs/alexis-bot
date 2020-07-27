from datetime import datetime

import discord
import peewee
from discord.utils import escape_markdown

from bot import Command, utils, categories, BaseModel
from discord import Embed, AuditLogAction

from bot.regex import pat_channel
from bot.utils import deltatime_to_str
from modules.user import UserInfo

modlog_types = ['user_join', 'user_leave', 'message_delete', 'username', 'nick', 'invite_filter', 'message_edit']


class UserNameReg(BaseModel):
    userid = peewee.TextField()
    name = peewee.TextField()
    timestamp = peewee.DateTimeField(default=datetime.now)


class ModLog(Command):
    __author__ = 'makzk'
    __version__ = '1.0.2'
    chan_config_name = 'join_send_channel'

    async def on_member_join(self, member):
        await self.bot.send_modlog(
            member.guild, '$[modlog-new-user]',
            embed=UserInfo.gen_embed(member, more=True), locales={'mid': member.id}, logtype='user_join')

    async def on_member_remove(self, member):
        dt = deltatime_to_str(datetime.now() - member.joined_at)
        locales = {
            'mid': member.id,
            'username': escape_markdown(str(member)),
            'dt': dt
        }

        await self.bot.send_modlog(member.guild, '$[modlog-user-left]', locales=locales, logtype='user_leave')

    async def on_message_delete(self, message):
        if message.guild is None or message.author.id == self.bot.user.id:
            return

        footer = '$[modlog-msg-sent]: ' + utils.format_date(message.created_at)
        if message.edited_at is not None:
            footer += ', $[modlog-msg-edited]: ' + utils.format_date(message.edited_at)

        embed = Embed(description='($[modlog-no-text])' if message.content == '' else message.content)
        embed.set_footer(text=footer)
        if len(message.attachments) > 0:
            with_img = False
            if message.attachments[0].width:
                fn_value = '[{}]({})'.format(message.attachments[0].filename, message.attachments[0].url)
                embed.set_image(url=message.attachments[0].url)
                embed.add_field(name='$[modlog-file-name]', value=fn_value)
                with_img = True

            if with_img and len(message.attachments) > 1 or not with_img:
                i = 1 if with_img else 0
                x = ['[{}]({})'.format(f.filename, f.url) for f in message.attachments[i:]]
                t = [
                        ['$[modlog-attatched]', '$[modlog-attached-other]'],
                        ['$[modlog-attached-single]', '$[modlog-attached-other-single]']
                    ][int(len(x) == 1)][i]
                embed.add_field(name=t, value=', '.join(x))

        msg = '$[modlog-user-deleted-msg]'
        locales = {
            'username': escape_markdown(message.author.display_name),
            'channel_name': message.channel.mention
        }

        if message.id in self.bot.deleted_messages:
            if message.id in self.bot.deleted_messages_nolog:
                self.bot.deleted_messages_nolog.remove(message.id)
                return
            else:
                msg = '$[modlog-bot-deleted-msg]'
        else:
            try:
                last = await self.get_last_alog(message.guild)
                if last is not None and last.action == AuditLogAction.message_delete and \
                        last.extra.channel.id == message.channel.id and last.target.id == message.author.id:
                    who = last.user
                    if who == self.bot.user.id:
                        msg = '$[modlog-bot-deleted-msg]'
                    else:
                        locales['deleter_name'] = who.display_name
                        msg = '$[modlog-user-deleted-other]'
            except discord.Forbidden:
                msg = '$[modlog-somehow-deleted-msg]'

        await self.bot.send_modlog(message.guild, msg, embed=embed, locales=locales, logtype='message_delete')

    async def on_message_edit(self, before, after):
        # Ignore on PM or self message
        if not isinstance(before.channel, discord.TextChannel) or before.author.id == self.bot.user.id:
            return

        # Ignore if no content changes were made
        if before.content.strip() == after.content.strip():
            return

        footer = '$[modlog-msg-sent]: {}, $[modlog-msg-edited]: {}'.format(
            utils.format_date(before.created_at),
            utils.format_date(after.created_at)
        )

        embed = Embed(title='📝 $[modlog-user-edited-msg]', description='$[modlog-user-edited-channel]')
        embed.set_footer(text=footer)

        locales = {
            'username': escape_markdown(after.author.display_name),
            'channel': after.channel.mention,
            'link': utils.message_link(after)
        }

        cont_before = '($[modlog-no-text])' if before.content == '' else before.content
        cont_after = '($[modlog-no-text])' if after.content == '' else after.content
        embed.add_field(name='$[modlog-user-edited-before]', value=utils.text_cut(cont_before, 1000), inline=False)
        embed.add_field(name='$[modlog-user-edited-after]', value=utils.text_cut(cont_after, 1000), inline=False)

        await self.bot.send_modlog(after.guild, embed=embed, locales=locales, logtype='message_edit')

    async def on_member_update(self, before, after):
        guild = after.guild

        if before.name != after.name:
            if after.display_name != after.name:
                name_before = escape_markdown(before.name)
                name_after = escape_markdown(after.name)
                nick = escape_markdown(after.display_name)

                await self.bot.send_modlog(
                    guild, '$[modlog-username-changed-nick]',
                    locales={'prev_name': name_before, 'new_name': name_after, 'nick': nick},
                    logtype='username')
            else:
                name_before = escape_markdown(before.name)
                name_after = escape_markdown(after.name)

                await self.bot.send_modlog(
                    guild, '$[modlog-username-changed]',
                    locales={'prev_name': name_before, 'new_name': name_after}, logtype='username')

        if (before.nick or after.nick) and before.nick != after.nick:
            try:
                alog = await self.get_last_alog(after.guild)
            except discord.Forbidden:
                alog = None

            if alog is not None and alog.action == AuditLogAction.member_update and alog.changes.after.nick:
                by = alog.user
            else:
                by = None

            prev_nick = escape_markdown(before.nick or '') or '$[modlog-nick-none]'
            after_nick = escape_markdown(after.nick or '') or '$[modlog-nick-none]'
            target = escape_markdown(after.name)

            locales = {'author': '' if by is None else by.name,
                       'target': target, 'previous': prev_nick, 'after': after_nick}

            if by is None:
                # default entry, no author
                await self.bot.send_modlog(guild, '$[modlog-nick-other]', logtype='nick', locales=locales)
            elif by.id == after.id:
                # self updated
                if by.id == self.bot.user.id:
                    await self.bot.send_modlog(guild, '$[modlog-nick-bot-self]', logtype='nick', locales=locales)
                else:
                    await self.bot.send_modlog(guild, '$[modlog-nick-self]', logtype='nick', locales=locales)
            else:
                # someone updated other's nick
                if after.id == self.bot.user.id:
                    await self.bot.send_modlog(guild, '$[modlog-nick-other-bot]', logtype='nick', locales=locales)
                else:
                    await self.bot.send_modlog(guild, '$[modlog-nick-by]', logtype='nick', locales=locales)

    async def get_last_alog(self, guild):
        try:
            entries = await guild.audit_logs(limit=1).flatten()
        except discord.Forbidden:
            return None
        except AttributeError:
            self.log.warning('There was probably an unknown (for discord.py) Audit Log action and triggered this error')
            return None

        if len(entries) == 0:
            return None

        return entries[0]


class ModLogChannel(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'logchannel'
        self.aliases = ['modlogchannel', 'modlogchan', 'logchan']
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
        if chan not in ['off', 'disable', 'here'] and not pat_channel.match(chan):
            await cmd.answer('$[modlog-channel-err-off]')
            return

        if chan == 'here':
            value = cmd.channel.id
        elif chan in ['off', 'disable']:
            value = ''
        else:
            value = chan[2:-1]

        cmd.config.set(ModLog.chan_config_name, value)
        if value == '':
            await cmd.answer('$[modlog-channel-off]')
        else:
            await cmd.answer('$[modlog-channel-set]', locales={'channel_id': value})


class LogToggle(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'logtoggle'
        self.help = '$[modlog-toggle-help]'
        self.format = '$[modlog-toggle-format]'
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, cmd):
        disabled = cmd.config.get_list('logtype_disabled')
        enabled = [x for x in modlog_types if x not in disabled]

        if cmd.argc == 0:
            await cmd.answer('$[modlog-toggle-list]\n$[modlog-toggle-list-disabled]', locales={
                'enabled_logs': ', '.join(enabled) or '$[modlog-none]',
                'disabled_logs': ', '.join(disabled) or '$[modlog-none]'
            })
            return

        ltype = cmd.args[0]
        if ltype not in modlog_types:
            await cmd.answer('Invalid log type')
            return

        if ltype in disabled:
            cmd.config.remove('logtype_disabled', ltype)
            await cmd.answer('Log type enabled.')
        else:
            cmd.config.add('logtype_disabled', ltype)
            await cmd.answer('Log type disabled.')
