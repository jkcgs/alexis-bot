import json

from os import path

import yaml

from modules.base.command import Command
from cleverwrap import CleverWrap
import random


class CleverbotHandler(Command):
    check = False
    cfg_enabled = 'cbot_enabled'

    def __init__(self, bot):
        super().__init__(bot)
        self.mention_handler = True
        self.allow_pm = False
        self.config = self.load_config()

        key = self.config['api_key']
        if key == '':
            CleverbotHandler.check = False
            self.log.warning('El valor "api_key" no se ha definido. La conversación será desactivada.')
            return

        self.cbot = CleverWrap(key)
        self.log.info('Conectando con Cleverbot API...')
        CleverbotHandler.check = self.cbot.say('test') is not None

        if self.cbot.say('test') is None:
            self.log.warning('No se pudo conectar con Cleverbot. La API key podría ser incorrecta.')
            CleverbotHandler.check = False
        else:
            self.log.info('CleverWrap iniciado correctamente.')

    def load_config(self):
        try:
            config_path = path.join(path.dirname(path.realpath(__file__)), 'pats.yml')
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            if config is None:
                raise Exception('La configuración está vacía')

            res_config = {
                'api_key': config.get('api_key', '')
            }
            return res_config
        except Exception as ex:
            self.log.exception(ex)
            return {
                'api_key': ''
            }

    async def handle(self, message, cmd):
        if not self.bot.rx_mention.match(message.content):
            return

        if not CleverbotHandler.check or cmd.config.get(CleverbotHandler.cfg_enabled, '1') != '0':
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

        new_val = ['0', '1'][int(cmd.config.get(CleverbotHandler.cfg_enabled, '1') == '0')]
        cmd.config.set(CleverbotHandler.cfg_enabled, new_val)
        resp = ['desactivada', 'activada'][int(new_val == '1')]
        await cmd.answer('Conversación {}'.format(resp))
