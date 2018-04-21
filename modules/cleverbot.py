import json

from bot import Command, BotMentionEvent
from cleverwrap import CleverWrap


class CleverbotHandler(Command):
    check = True
    cfg_enabled = 'cbot_enabled'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'c'
        self.allow_pm = False
        self.mention_handler = True
        self.cbot = None
        self.default_config = {
            'cleverbot_apikey': ''
        }

    def on_loaded(self):
        config_key = self.bot.config.get('cleverbot_apikey', '')
        if config_key == '':
            CleverbotHandler.check = False
            self.log.warn('La API key de CleverBot no está configurada. Puedes agregarla con el valor '
                          'cleverbot_apikey en el archivo de configuración')
        else:
            self.cbot = CleverWrap(config_key)
            self.log.debug('CleverWrap cargado')

    async def handle(self, cmd):
        if not (isinstance(cmd, BotMentionEvent) and cmd.starts_with and len(cmd.text) > 3):
            return

        if not CleverbotHandler.check or cmd.config.get(CleverbotHandler.cfg_enabled, '1') != '1':
            await cmd.answer('conversación desactivada uwu')
            return

        if cmd.text == '':
            reply = '*si querías decirme algo, dílo de la siguiente forma: <@bot> <texto>*'
            await cmd.answer(reply)
            return

        await cmd.typing()
        try:
            self.log.debug('Cleverbot <- "%s" (%s, %s)', cmd.text, str(cmd.author), str(cmd.message.channel))
            reply = self.cbot.say(cmd.text)
            if reply is None:
                self.log.warn('No se pudo conectar con Cleverbot. La API key podría ser incorrecta.')
                CleverbotHandler.check = False
                reply = 'noooo que pasa D:'

        except json.decoder.JSONDecodeError as e:
            reply = 'pucha sorry, no puedo responderte ahora'
            self.log.error('Ocurrió un error con Cleverbot')
            self.log.exception(e)

        await cmd.answer(reply)

    def load_config(self):
        self.on_loaded()


class ToggleConversation(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'toggleconversation'
        self.help = 'Activa/desactiva la conversación con el bot'
        self.owner_only = True

    async def handle(self, cmd):
        if not CleverbotHandler.check:
            await cmd.answer('comando no disponible')
            return

        new_val = ['0', '1'][int(cmd.config.get(CleverbotHandler.cfg_enabled, '1') == '0')]
        cmd.config.set(CleverbotHandler.cfg_enabled, new_val)
        resp = ['desactivada', 'activada'][int(new_val == '1')]
        await cmd.answer('Conversación {}'.format(resp))
