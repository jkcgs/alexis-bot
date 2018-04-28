import random

from discord import Embed

from bot import Command
from bot.libs.configuration import ServerConfiguration
from bot.utils import is_int


class Greeting(Command):
    cfg_welcome_channel = 'welcome_channel'
    cfg_welcome_messages = 'welcome_messages'
    cfg_goodbye_channel = 'goodbye_channel'
    cfg_goodbye_messages = 'goodbye_messages'
    separator = '|'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'welcome'
        self.aliases = ['goodbye']
        self.help = '$[greeting-help]'
        self.owner_only = True
        self.default_config = {
            'greeting_max_messages': 10,
            'greeting_max_length': 100
        }

    async def handle(self, cmd):
        max_msgs = self.bot.config.get('greeting_max_messages', 10)
        max_length = self.bot.config.get('greeting_max_length', 100)

        is_welcome = cmd.cmdname == self.name
        cfg_channel = self.cfg_welcome_channel if is_welcome else self.cfg_goodbye_channel
        cfg_messages = self.cfg_welcome_messages if is_welcome else self.cfg_goodbye_messages

        if cmd.argc == 0 or cmd.args[0] not in ['set', 'message', 'channel', 'disable']:
            if cmd.argc > 0 and cmd.find_channel(cmd.args[0]) is not None:
                subcmd = 'channel' if cmd.argc == 1 else 'set'
                cmd.args.insert(0, subcmd)
                cmd.argc += 1
            else:
                await cmd.answer('$[greeting-format]')
                return

        if cmd.args[0] == 'set':
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
            cmd.config.set_list(cfg_messages, msgs, Greeting.separator)
            await cmd.answer('$[greeting-settings-saved]')

        elif cmd.args[0] == 'message':
            if cmd.argc < 2 or (cmd.argc < 3 and cmd.args[1] != 'list') \
                    or cmd.args[1] not in ['list', 'show', 'add', 'remove', 'set']:
                await cmd.answer('$[greeting-message-format]')
                return

            if cmd.config.get(cfg_channel) == '':
                await cmd.answer('$[greeting-disabled-alert]')
                return
            msgs = cmd.config.get_list(cfg_messages, Greeting.separator)

            if cmd.args[1] in ['list', 'show']:
                if len(msgs) == 0:
                    await cmd.answer('$[greeting-no-messages]')
                    return

                description = '\n'.join(['{}.- {}'.format(i+1, f) for i, f in enumerate(msgs)])
                description += '\n\n**$[greeting-current-channel]**: <#{}>'.format(cmd.config.get(Greeting.cfg_welcome_channel))
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

                cmd.config.add(cfg_messages, msg, Greeting.separator)
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

                cmd.config.remove_index(cfg_messages, idx, Greeting.separator)

                await cmd.answer('$[greeting-message-deleted]')
            elif cmd.args[1] == 'set':
                msgs = ' '.join(cmd.args[2:]).split(Greeting.separator)
                for m in msgs:
                    if Greeting.separator in m:
                        await cmd.answer('$[greeting-character-alert]', locales={'separator': Greeting.separator})
                        return

                cmd.config.set_list(cfg_messages, msgs, Greeting.separator)
                msg = ['$[greeting-messages-saved]', '$[greeting-message-saved]'][int(len(msgs) == 1)]
                await cmd.answer(msg)

        elif cmd.args[0] == 'channel':
            chan = cmd.find_channel(cmd.args[1])
            if chan is None:
                await cmd.answer('$[channel-not-found]')
                return

            cmd.config.set(cfg_channel, chan.id)
            await cmd.answer('$[channel-saved]')

        elif cmd.args[0] == 'disable':
            cmd.config.set(cfg_channel, '')
            await cmd.answer('$[greeting-messages-disabled]')

    async def send_greeting(self, member, is_welcome):
        cfg_channel = self.cfg_welcome_channel if is_welcome else self.cfg_goodbye_channel
        cfg_messages = self.cfg_welcome_messages if is_welcome else self.cfg_goodbye_messages

        cfg = ServerConfiguration(self.bot.sv_config, member.server)
        chanid = cfg.get(cfg_channel)
        msgs = cfg.get_list(cfg_messages, Greeting.separator)
        if chanid == '' or len(msgs) == 0:
            return

        chan = member.server.get_channel(chanid)
        if chan is None:
            return

        msg = random.choice(msgs)
        msg = msg.replace('$name', member.display_name)
        msg = msg.replace('$mention', member.mention)
        msg = msg.replace('$server', member.server.name)

        await self.bot.send_message(chan, msg)

    async def on_member_join(self, member):
        await self.send_greeting(member, True)

    async def on_member_remove(self, member):
        await self.send_greeting(member, False)
