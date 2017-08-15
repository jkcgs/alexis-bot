from commands.base.command import Command
from cleverwrap import CleverWrap
import random


class CleverbotHandler(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.mention_handler = True
        self.allow_pm = False

        self.cbot = CleverWrap(self.bot.config['cleverbot_key'])
        self.cbotcheck = False
        self.bot.sharedcfg['conversation'] = True

        self.log.info('Conectando con Cleverbot API...')
        self.cbotcheck = self.cbot.say('test') is not None
        if self.cbotcheck:
            self.log.info('CleverWrap iniciado correctamente.')
        else:
            self.log.warning('El valor "cleverbot_key" es inválido.')

    async def handle(self, message, cmd):
        if not self.bot.rx_mention.match(message.content) or self.cbotcheck is None:
            return

        if not self.bot.sharedcfg['conversation']:
            self.cbot.say('l-lo siento sempai, no puedo hablar ahora uwu')

        msg = self.bot.rx_mention.sub('', message.content).strip()
        if msg == '':
            frase = random.choice(self.bot.config['frases'])
            reply = '{}\n\n*Si querías decirme algo, dílo de la siguiente forma: <@bot> <texto>*'.format(frase)
        else:
            reply = self.cbot.say(msg)

        await cmd.answer(reply)


class ToggleConversation(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'toggleconversation'
        self.help = 'Activa/desactiva la conversación con el bot'
        self.owner_only = True

        if 'conversation' not in self.bot.sharedcfg:
            self.bot.sharedcfg['conversation'] = True

    async def handle(self, message, cmd):
        self.bot.sharedcfg['conversation'] = not self.bot.sharedcfg['conversation']
        resp = 'activada' if self.bot.sharedcfg['conversation'] else 'desactivada'
        await cmd.answer('Conversación {}'.format(resp))
