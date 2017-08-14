from commands.base.command import Command


class CleverbotHandler(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.mention_handler = True
        self.allow_pm = False

    async def handle(self, message, cmd):
        if not self.bot.rx_mention.match(message.content) or not self.bot.conversation or self.bot.cbotcheck is None:
            return

        msg = self.bot.rx_mention.sub('', message.content).strip()
        if msg == '':
            reply = '{}\n\n*Si querías decirme algo, dílo de la siguiente forma: <@bot> <texto>*'.format(frase)
        else:
            reply = self.bot.cbot.say(msg)

        await cmd.answer(reply)
