import json

from bot import Command, BotMentionEvent, categories
from cleverwrap import CleverWrap


class CleverbotHandler(Command):
    check = True
    cfg_enabled = 'cbot_enabled'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'c'
        self.allow_pm = False
        self.mention_handler = True
        self.category = categories.FUN
        self.cbot = None
        self.default_config = {
            'cleverbot_apikey': ''
        }

    async def on_ready(self):
        config_key = self.bot.config.get('cleverbot_apikey', '')
        if config_key == '':
            CleverbotHandler.check = False
            self.log.warn('Cleverbot API key not defined. Add it to the \'cleverbot_apikey\' '
                          'value to settings.yml file')
        else:
            self.cbot = CleverWrap(config_key)
            self.log.debug('Loaded CleverWrap')

    async def handle(self, cmd):
        if not (isinstance(cmd, BotMentionEvent) and cmd.starts_with and len(cmd.text) > 3):
            return

        if not CleverbotHandler.check or cmd.config.get(CleverbotHandler.cfg_enabled, '1') != '1':
            await cmd.answer('$[cleverbot-disabled]')
            return

        if cmd.text == '':
            await cmd.answer('$[cleverbot-usage-answer]')
            return

        await cmd.typing()
        try:
            self.log.debug('Cleverbot <- "%s" (%s, %s)', cmd.text, str(cmd.author), str(cmd.message.channel))
            reply = self.cbot.say(cmd.text)
            if reply is None:
                self.log.warn('Could not connect to Cleverbot. The API key is probably wrong.')
                CleverbotHandler.check = False
                reply = '$[cleverbot-no-answer]'

        except json.decoder.JSONDecodeError as e:
            reply = '$[cleverbot-error-answer]'
            self.log.error('An error ocurred with Cleverbot')
            self.log.exception(e)

        await cmd.answer(reply)

    def load_config(self):
        self.on_loaded()


class ToggleConversation(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'toggleconversation'
        self.help = '$[cleverbot-toggle-help]'
        self.owner_only = True
        self.category = categories.STAFF

    async def handle(self, cmd):
        if not CleverbotHandler.check:
            await cmd.answer('$[command-not-available]')
            return

        new_val = ['0', '1'][int(cmd.config.get(CleverbotHandler.cfg_enabled, '1') == '0')]
        cmd.config.set(CleverbotHandler.cfg_enabled, new_val)
        resp = ['cleverbot-enabled', 'cleverbot-disabled'][int(new_val == '1')]
        await cmd.answer('$[cleverbot-toggle-answer]', locales={'status': cmd.lang.get(resp)})
