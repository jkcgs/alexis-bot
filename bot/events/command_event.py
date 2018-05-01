import traceback
from datetime import timedelta, datetime

from bot.utils import serialize_avail, replace_everywhere, no_tags
from bot.logger import log
from .message_event import MessageEvent


class CommandEvent(MessageEvent):
    def __init__(self, message, bot):
        super().__init__(message, bot)

        # Prefix retrieval
        prefix = MessageEvent.get_prefix(message, bot)
        if not self.text.startswith(prefix):
            raise RuntimeError('The message is not a command')
        self.prefix = prefix

        # Command definition
        self.allargs = message.content.replace('  ', ' ').split(' ')
        cmd_parts = self.allargs[0][len(self.prefix):].split(':')
        self.cmdname = cmd_parts[0]
        self.subcmd = '' if len(cmd_parts) < 2 else cmd_parts[1]

        # Arguments definition
        self.args = [] if len(self.allargs) == 1 else [f for f in self.allargs[1:] if f.strip() != '']
        self.argc = len(self.args)
        self.text = ' '.join(self.args)

    async def answer(self, content='', to_author=False, withname=True, **kwargs):
        if 'locales' not in kwargs:
            kwargs['locales'] = {}

        kwargs['event'] = self
        kwargs['locales']['$CMD'] = '$PX' + self.cmdname
        kwargs['locales']['$NM'] = self.cmdname
        return await super().answer(content, to_author, withname, **kwargs)

    def is_enabled(self):
        if self.is_pm:
            return True

        data_db = self.config.get('cmd_status', '')
        avail = serialize_avail(data_db)
        cmd = self.bot.manager[self.cmdname]
        enabled_db = avail.get(cmd.name, '+' if cmd.default_enabled else '-')
        return enabled_db == '+'

    def no_tags(self, users=True, channels=True, emojis=True):
        return no_tags(self.text, self.bot, users, channels, emojis)

    def __str__(self):
        return '[{} name="{}", channel="{}#{}", author="{}" text="{}"]'.format(
            self.__class__.__name__, self.cmdname, self.message.server,
            self.message.channel, self.message.author, self.text
        )

    async def handle(self):
        try:
            cmd = self.bot.manager[self.cmdname]
            # Filtro de permisos y tiempo
            if (cmd.bot_owner_only and not self.bot_owner) \
                    or (cmd.owner_only and not self.owner) \
                    or (not cmd.allow_pm and self.is_pm) \
                    or (not self.is_pm and not self.is_enabled()):
                return
            elif (cmd.user_delay > 0 and self.author.id in cmd.users_delay
                  and cmd.users_delay[self.author.id] + timedelta(0, cmd.user_delay) > datetime.now()
                  and not self.owner):
                await self.answer('aún no puedes usar ese comando')
                return
            elif not self.is_pm and cmd.nsfw_only and 'nsfw' not in self.channel.name:
                await self.answer('este comando sólo puede ser usado en un canal NSFW')
                return
            else:
                # Ejecutar el comando
                result = await cmd.handle(self)
                fine = result is None or (isinstance(result, bool) and result)
                if fine and cmd.user_delay > 0:
                    cmd.users_delay[self.author.id] = datetime.now()
        except Exception as e:
            if self.bot.config['debug']:
                await self.answer('ALGO PASÓ OwO\n```{}```'.format(traceback.format_exc()))
            else:
                await self.answer('ocurr.. 1.error c0n\'el$##com@nd..\n```{}```'.format(str(e)))
            log.exception(e)

    @staticmethod
    def is_command(message, bot):
        prefix = MessageEvent.get_prefix(message, bot)
        if message.content.startswith(prefix):
            cmdname = message.content[len(prefix):].split(' ')[0].split(':')[0]
            return cmdname in bot.manager
        else:
            return False

