import json

from modules.base.command import Command
from cleverwrap import CleverWrap
import random


class CleverbotHandler(Command):
    enabled = True
    check = False

    def __init__(self, bot):
        super().__init__(bot)
        self.mention_handler = True
        self.allow_pm = False

        key = self.bot.config['cleverbot_key'].strip()
        if key == '':
            CleverbotHandler.enabled = False
            CleverbotHandler.check = False
            self.log.warning('El valor "cleverbot_key" no se ha definido. La conversación será desactivada.')
            return

        self.cbot = CleverWrap(key)
        self.log.info('Conectando con Cleverbot API...')
        CleverbotHandler.check = self.cbot.say('test') is not None

        if self.cbot.say('test') is None:
            self.log.warning('No se pudo conectar con Cleverbot. La API key podría ser incorrecta.')
            CleverbotHandler.enabled = False
            CleverbotHandler.check = False
        else:
            self.log.info('CleverWrap iniciado correctamente.')

    async def handle(self, message, cmd):
        if not self.bot.rx_mention.match(message.content):
            return

        if not CleverbotHandler.enabled:
            await cmd.answer('l-lo siento sempai, no puedo hablar ahora uwu')
            return

        msg = self.bot.rx_mention.sub('', message.content).strip()
        if msg == '':
            reply = '*Si querías decirme algo, dílo de la siguiente forma: <@bot> <texto>*'
        else:
            await cmd.typing()
            try:
                self.log.debug('Cleverbot <- "%s" (%s, %s)', msg, str(cmd.author), str(message.channel))
                reply = self.cbot.say(msg)
            except json.decoder.JSONDecodeError as e:
                reply = 'pucha sorry, no puedo responderte ahora'
                self.log.error('Ocurrió un error con Cleverbot')
                self.log.exception(e)

        await cmd.answer(reply)


class ToggleConversation(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'toggleconversation'
        self.help = 'Activa/desactiva la conversación con el bot'
        self.owner_only = True

    async def handle(self, message, cmd):
        if not CleverbotHandler.check:
            await cmd.answer('Comando no disponible')
            return

        CleverbotHandler.enabled = not CleverbotHandler.enabled
        resp = ['desactivada', 'activada'][int(CleverbotHandler.enabled)]
        await cmd.answer('Conversación {}'.format(resp))
