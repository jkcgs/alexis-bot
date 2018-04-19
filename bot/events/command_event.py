from bot.utils import serialize_avail, replace_everywhere
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
        content = replace_everywhere(content, '$CMD', '$PX$NM')
        content = replace_everywhere(content, '$NM', self.cmdname)
        if kwargs.get('embed', None) is not None:
            kwargs['embed'] = replace_everywhere(kwargs.get('embed'), '$CMD', '$PX$NM')
            kwargs['embed'] = replace_everywhere(kwargs.get('embed'), '$NM', self.cmdname)

        return await super().answer(content, to_author, withname, **kwargs)

    def is_enabled(self):
        if self.is_pm:
            return True

        data_db = self.config.get('cmd_status', '')
        avail = serialize_avail(data_db)
        cmd = self.bot.manager[self.cmdname]
        enabled_db = avail.get(cmd.name, '+' if cmd.default_enabled else '-')
        return enabled_db == '+'

    def __str__(self):
        return '[{} name="{}", channel="{}#{}", author="{}" text="{}"]'.format(
            self.__class__.__name__, self.cmdname, self.message.server,
            self.message.channel, self.message.author, self.text
        )

    @staticmethod
    def is_command(message, bot):
        prefix = MessageEvent.get_prefix(message, bot)
        if message.content.startswith(prefix):
            cmdname = message.content[len(prefix):].split(' ')[0].split(':')[0]
            return cmdname in bot.manager
        else:
            return False

