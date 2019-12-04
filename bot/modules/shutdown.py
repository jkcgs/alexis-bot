import sys

from bot import Command, categories


class ShutdownCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'shutdown'
        self.help = '$[config-shutdown-help]'
        self.bot_owner_only = True
        self.category = categories.SETTINGS

    async def handle(self, cmd):
        self.bot.config['shutdown_channel'] = cmd.message.channel.id
        await cmd.answer('$[config-goodbye]')
        await self.bot.close()
        sys.exit(0)

    async def on_ready(self):
        if self.bot.config.get('shutdown_channel', '') != '':
            chan = self.bot.get_channel(self.bot.config['shutdown_channel'])
            if chan is None:
                return

            await self.bot.send_message(chan, '$[config-back]')
            self.bot.config['shutdown_channel'] = ''
