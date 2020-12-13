import random

from discord import Embed

from bot import Command, categories
from bot.lib.guild_configuration import GuildConfiguration
from bot.utils import is_int, invite_filter, auto_int
from bot.regex import pat_invite


class Greeting(Command):
    __author__ = 'makzk'
    __version__ = '1.2.0'

    cfg_welcome_channel = 'welcome_channel'
    cfg_welcome_messages = 'welcome_messages'
    cfg_goodbye_channel = 'goodbye_channel'
    cfg_goodbye_messages = 'goodbye_messages'
    cfg_welcome_enabled = 'welcome_enabled'
    cfg_goodbye_enabled = 'goodbye_enabled'
    cfg_pm_enabled = 'welcome_pm_enabled'
    cfg_pm_message = 'welcome_pm_message'
    separator = '|'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'welcome'
        self.aliases = ['goodbye']
        self.help = '$[greeting-help]'
        self.format = '$[greeting-format]'
        self.owner_only = True
        self.category = categories.STAFF
        self.default_config = {
            'greeting_max_messages': 10,
            'greeting_max_length': 1000
        }

    async def handle(self, cmd):
        max_msgs = self.bot.config.get('greeting_max_messages', 10)
        max_length = self.bot.config.get('greeting_max_length', 1000)

        is_welcome = cmd.cmdname == self.name
        cfg_channel = self.cfg_welcome_channel if is_welcome else self.cfg_goodbye_channel
        cfg_messages = self.cfg_welcome_messages if is_welcome else self.cfg_goodbye_messages
        subarg = None if cmd.argc == 0 else cmd.args[0]

        if subarg == 'set':
            if cmd.argc < 2:
                await cmd.answer('$[greeting-set-format]', locales={
                    'limit': max_msgs,
                    'max-length': max_length,
                    'separator': Greeting.separator
                })
                return

            chan = cmd.find_channel(cmd.args[1])
            if chan is None:
                await cmd.answer('$[channel-not-found]')
                return

            msgs = [f.strip() for f in ' '.join(cmd.args[2:]).split(Greeting.separator)]
            for i, m in enumerate(msgs):
                if len(m) > max_length:
                    await cmd.answer('$[greeting-set-limit]', locales={
                        'limit': max_length,
                        'number': i+1,
                        'length': len(m)
                    })
                    return

            cmd.config.set(cfg_channel, chan.id)
            cmd.config.set_list(cfg_messages, msgs)
            await cmd.answer('$[greeting-settings-saved]')

        elif subarg == 'message':
            if cmd.argc < 2 or (cmd.argc < 3 and cmd.args[1] != 'list') \
                    or cmd.args[1] not in ['list', 'show', 'add', 'remove', 'set']:
                await cmd.answer('$[greeting-message-format]')
                return

            if cmd.config.get(cfg_channel) == '':
                await cmd.answer('$[greeting-disabled-alert]')
                return
            msgs = cmd.config.get_list(cfg_messages)

            if cmd.args[1] in ['list', 'show']:
                if len(msgs) == 0:
                    await cmd.answer('$[greeting-no-messages]')
                    return

                description = '\n'.join(['{}.- {}'.format(i+1, f) for i, f in enumerate(msgs)])
                description += '\n\n**$[greeting-current-channel]**: <#{}>'.format(
                    cmd.config.get(Greeting.cfg_welcome_channel))
                title = '$[greeting-welcome-messages]' if is_welcome else '$[greeting-goodbye-messages]'
                embed = Embed(title=title, description=description)
                await cmd.answer(embed)

            elif cmd.args[1] == 'add':
                if len(msgs) >= max_msgs:
                    await cmd.answer('$[greeting-limit-alert]', locales={'limit': max_msgs})
                    return

                msg = ' '.join(cmd.args[2:])
                if Greeting.separator in msg:
                    await cmd.answer('$[greeting-character-alert]', locales={'separator': Greeting.separator})
                    return

                cmd.config.add(cfg_messages, msg)
                await cmd.answer('$[greeting-message-added]')

            elif cmd.args[1] == 'remove':
                if not is_int(cmd.args[2]):
                    await cmd.answer('$[greeting-no-list-numberlist]')
                    return

                if len(msgs) == 0:
                    await cmd.answer('$[greeting-no-messages]')
                    return

                idx = int(cmd.args[2]) - 1
                if idx+1 > len(msgs):
                    await cmd.answer('$[greeting-number-out-of-bounds]')
                    return

                cmd.config.remove_index(cfg_messages, idx)

                await cmd.answer('$[greeting-message-deleted]')
            elif cmd.args[1] == 'set':
                msgs = ' '.join(cmd.args[2:]).split(Greeting.separator)
                for m in msgs:
                    if Greeting.separator in m:
                        await cmd.answer('$[greeting-character-alert]', locales={'separator': Greeting.separator})
                        return

                cmd.config.set_list(cfg_messages, msgs)
                msg = ['$[greeting-messages-saved]', '$[greeting-message-saved]'][int(len(msgs) == 1)]
                await cmd.answer(msg)

        elif subarg == 'channel':
            if cmd.argc == 1:
                cfg_name = self.cfg_welcome_channel if is_welcome else self.cfg_goodbye_channel
                curr_chan_id = cmd.config.get(cfg_name, '')
                if not curr_chan_id:
                    await cmd.answer('$[greeting-no-channel]')
                else:
                    await cmd.answer('**$[greeting-current-channel]**: <#{}>'.format(curr_chan_id))
            else:
                chan = cmd.find_channel(cmd.args[1])
                if chan is None:
                    await cmd.answer('$[channel-not-found]')
                    return

                cmd.config.set(cfg_channel, chan.id)
                await cmd.answer('$[channel-saved]')

        elif subarg == 'enable':
            if cmd.cmdname == self.name:
                cfg_name = self.cfg_welcome_enabled
                cfg_msg_ok = '$[greeting-enabled]'
                cfg_msg_err = '$[greeting-already-enabled]'
            else:
                cfg_name = self.cfg_goodbye_enabled
                cfg_msg_ok = '$[greeting-goodbye-enabled]'
                cfg_msg_err = '$[greeting-goodbye-already-enabled]'

            if cmd.config.get_bool(cfg_name):
                await cmd.answer(cfg_msg_err)
            else:
                cmd.config.set_bool(cfg_name, True)
                await cmd.answer(cfg_msg_ok)

        elif subarg == 'disable':
            if is_welcome:
                cfg_name = self.cfg_welcome_enabled
                cfg_msg_ok = '$[greeting-disabled]'
                cfg_msg_err = '$[greeting-already-disabled]'
            else:
                cfg_name = self.cfg_goodbye_enabled
                cfg_msg_ok = '$[greeting-goodbye-disabled]'
                cfg_msg_err = '$[greeting-goodbye-already-disabled]'

            if not cmd.config.get_bool(cfg_name):
                await cmd.answer(cfg_msg_err)
            else:
                cmd.config.set_bool(cfg_name, False)
                await cmd.answer(cfg_msg_ok)

        elif subarg == 'enablepm':
            if cmd.config.get_bool(self.cfg_pm_enabled, default=False):
                await cmd.answer('$[greeting-pm-already-enabled]')
            else:
                cmd.config.set_bool(self.cfg_pm_enabled, True)
                await cmd.answer('$[greeting-pm-enabled]')

        elif subarg == 'disablepm':
            if not cmd.config.get_bool(self.cfg_pm_enabled, default=False):
                await cmd.answer('$[greeting-pm-already-disabled]')
            else:
                cmd.config.unset(self.cfg_pm_enabled)
                await cmd.answer('$[greeting-pm-disabled]')

        elif subarg == 'pmmessage':
            message = (' '.join(cmd.args[1:])).strip()
            if cmd.argc < 2 or not message:
                pm_message = cmd.config.get(self.cfg_pm_message)
                if not pm_message:
                    await cmd.answer('$[greeting-pm-not-set]')
                else:
                    await cmd.answer('$[greeting-pm-current]: ```{}```'.format(pm_message))
            else:
                cmd.config.set(self.cfg_pm_message, message)
                await cmd.answer('$[greeting-pm-updated]')

        else:
            await cmd.send_usage()

    async def send_greeting(self, member, is_welcome):
        cfg_channel = self.cfg_welcome_channel if is_welcome else self.cfg_goodbye_channel
        cfg_messages = self.cfg_welcome_messages if is_welcome else self.cfg_goodbye_messages
        cfg_enabled = self.cfg_welcome_enabled if is_welcome else self.cfg_goodbye_enabled

        cfg = GuildConfiguration.get_instance(member.guild)
        chanid = cfg.get(cfg_channel)
        msgs = cfg.get_list(cfg_messages)
        if chanid == '' or len(msgs) == 0:
            return

        chan = member.guild.get_channel(auto_int(chanid))
        if chan is None:
            return

        name = member.display_name
        mention = member.mention
        if pat_invite.search(name) or pat_invite.search(mention):
            name = invite_filter(member.display_name)
            mention = name

        msg = random.choice(msgs)
        msg = msg.replace('$name', name)
        msg = msg.replace('$mention', mention)
        msg = msg.replace('$server', member.guild.name)

        if cfg.get_bool(cfg_enabled, default=True) and msg:
            await self.bot.send_message(chan, msg)

        if is_welcome and cfg.get_bool(self.cfg_pm_enabled, default=False):
            pm_message = cfg.get(self.cfg_pm_message)
            pm_message = pm_message.replace('$name', name)
            pm_message = pm_message.replace('$mention', mention)
            pm_message = pm_message.replace('$server', member.guild.name)
            pm_message = pm_message or msg

            if pm_message:
                await self.bot.send_message(member, pm_message or msg)

    async def on_member_join(self, member):
        await self.send_greeting(member, True)

    async def on_member_remove(self, member):
        await self.send_greeting(member, False)
