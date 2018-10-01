import re

import discord

from bot import AlexisBot, Command, categories
from bot.events import is_bot_command
from bot.utils import unserialize_avail, get_server_role, serialize_avail

rx_snowflake = re.compile('^\d{10,19}$')
rx_channel = re.compile('^<#\d{10,19}>$')


class InfoCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'info'
        self.aliases = ['version']
        self.help = '$[info-help]'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        info_msg = "```\n$[info-authors]: {}\n$[info-version]: {}```"
        info_msg = info_msg.format(AlexisBot.__author__, AlexisBot.__version__)
        await cmd.answer(info_msg)


class ClearReactions(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'clearreactions'
        self.aliases = ['clr']
        self.help = '$[clr-help]'
        self.owner_only = True
        self.category = categories.STAFF

    async def handle(self, cmd):
        if cmd.argc < 1:
            await cmd.answer('$[format]: $[clr-format]')
            return

        await cmd.typing()

        channel = cmd.message.channel
        if rx_channel.match(cmd.args[0]):
            channel = cmd.message.channel_mentions[0]
            cmd.args = cmd.args[1:]
            cmd.argc -= 1

        filtered_len = len([f for f in cmd.args if rx_snowflake.match(f)])
        if cmd.argc != filtered_len:
            await cmd.answer('$[clr-err-ids]')
            return

        success_count = 0
        not_found = []
        for arg in cmd.args:
            try:
                msg = await self.bot.get_message(channel, arg)
                await self.bot.clear_reactions(msg)
                success_count += 1
            except discord.Forbidden:
                pass
            except discord.NotFound:
                not_found.append(arg)

        if success_count == 0:
            msg = ['$[clr-err-any]', '$[clr-err-any-singular]'][cmd.argc == 1]
            locales = {}
            if len(not_found) > 0:
                if cmd.argc == 1:
                    msg += ': $[clr-err-not-found]'
                elif len(not_found) > 1:
                    msg += ': $[clr-err-some-not-found] '
                    msg += '({})'.format(', '.join(not_found))
                else:
                    msg += ': $[clr-err-single-not-found]'
                    locales['message_id'] = not_found[0]
            await cmd.answer(msg, locales=locales)
        elif success_count < cmd.argc:
            msg = '$[clr-err-some-deleted]'
            locales = {}

            if len(not_found) > 1:
                msg += ': $[clr-err-some-not-found] '
                msg += '({})'.format(', '.join(not_found))
            else:
                msg += ': clr-err-single-not-found'
                locales['message_id'] = not_found[0]

            await cmd.answer(msg, locales=locales)
        else:
            await cmd.answer('$[clr-success]')


class ChangePrefix(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.mention_handler = True
        self.name = 'prefix'
        self.aliases = ['changeprefix']
        self.help = '$[prefix-help]'
        self.owner_only = True
        self.category = categories.STAFF

    async def handle(self, cmd):
        if not is_bot_command(cmd):
            return

        if cmd.argc < 1:
            await cmd.answer('$[prefix-current]',
                             locales={'command_name': self.name, 'self_mention': self.bot.user.mention})
            return

        if len(cmd.text) > 3:
            return

        cmd.config.set('command_prefix', cmd.args[0])
        await cmd.answer('$[prefix-set]', locales={'new_prefix': cmd.args[0]})


class CommandConfig(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'cmd'
        self.help = '$[cmd-help]'
        self.format = '$[cmd-format]'
        self.owner_only = True
        self.category = categories.STAFF

    async def handle(self, cmd):
        if cmd.argc < 2:
            await cmd.answer('$[format]: $[cmd-format]')
            return

        if cmd.args[1] not in self.bot.manager:
            await cmd.answer('$[cmd-not-found]')
            return

        if cmd.args[1] == self.name:
            await cmd.answer('$[cmd-not-allowed]')
            return

        avail = serialize_avail(cmd.config.get('cmd_status', ''))
        cmd_ins = self.bot.manager[cmd.args[1]]
        current = avail.get(cmd_ins.name, '+' if cmd_ins.default_enabled else '-')

        if cmd.args[0] == 'enable':
            if current == '+':
                await cmd.answer('$[cmd-already-enabled]')
                return
            else:
                avail[cmd_ins.name] = '+'
                cmd.config.set('cmd_status', unserialize_avail(avail))
                await cmd.answer('$[cmd-enabled]')
                return
        elif cmd.args[0] == 'disable':
            if current == '-':
                await cmd.answer('$[cmd-already-disabled]')
                return
            else:
                avail[cmd_ins.name] = '-'
                cmd.config.set('cmd_status', unserialize_avail(avail))
                await cmd.answer('$[cmd-disabled]')
                return
        else:
            await cmd.answer('$[format]: $[cmd-format]')


class OwnerRoles(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ownerrole'
        self.help = '$[owr-help]'
        self.format = '$[owr-format]'
        self.owner_only = True
        self.category = categories.STAFF

    async def handle(self, cmd):
        if cmd.argc < 1:
            await cmd.answer('$[format]: $[owr-format]')
            return

        await cmd.typing()
        owner_roles = cmd.config.get('owner_roles', self.bot.config['owner_role'])
        owner_roles = [owner_roles.split('\n'), []][int(owner_roles == '')]

        if cmd.args[0] in ['set', 'add', 'remove']:
            if cmd.argc < 2:
                await cmd.answer('$[format]: $[owr-format]')
                return

            cmd_role = ' '.join(cmd.args[1:])
            role = get_server_role(cmd.message.server, cmd_role)
            if role is None and cmd_role not in owner_roles:
                await cmd.answer('$[owr-role-not-found]')
                return

            if cmd.args[0] == 'set':
                if role is None:  # doble check
                    await cmd.answer('$[owr-role-not-found]')
                    return

                cmd.config.set('owner_roles', role.id)
                await cmd.answer('$[owr-set]', locales={'role_name': role.name})
            elif cmd.args[0] == 'add':
                if role.id in owner_roles:
                    await cmd.answer('$[owr-already-owner]')
                    return

                cmd.config.set('owner_roles', '\n'.join(owner_roles + [role.id]))
                await cmd.answer('$[owr-added]', locales={'role_name': role.name})
            elif cmd.args[0] == 'remove':
                if role.id not in owner_roles:
                    await cmd.answer('$[owr-not-owner]')
                    return

                owner_roles.remove(role.id)
                cmd.config.set('owner_roles', '\n'.join(owner_roles))
                await cmd.answer('$[owr-removed]', locales={'role_name': role.name})
        elif cmd.args[0] == 'list':
            msg = '$[owr-title] '
            msg_list = []
            for roleid in owner_roles:
                srole = get_server_role(cmd.message.server, roleid)
                if srole is not None:
                    msg_list.append(srole.name)
                else:
                    member = cmd.message.server.get_member(roleid)
                    if member is not None:
                        msg_list.append('$[owr-usr]:' + member.display_name)
                    else:
                        msg_list.append('id:' + roleid)
            await cmd.answer(msg + ', '.join(msg_list))
        else:
            await cmd.answer('$[owr-format]')


class SetLanguage(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'setlanguage'
        self.aliases = ['setlang', 'lang']
        self.help = '$[lang-cmd-help]'
        self.category = categories.STAFF
        self.allow_pm = False
        self.owner_only = True

    async def handle(self, cmd):
        if cmd.argc == 0:
            self.log.debug('Lang updated to %s for server %s', cmd.config.get('lang'), cmd.server)
            await cmd.answer('$[current-lang]', locales={'lang': cmd.config.get('lang')})
            return

        if not self.bot.lang.has(cmd.text):
            await cmd.answer('$[lang-not-available]')
            return

        cmd.config.set('lang', cmd.text)
        await cmd.answer(self.bot.lang.get('lang-set-to', cmd.text, lang=cmd.text))
