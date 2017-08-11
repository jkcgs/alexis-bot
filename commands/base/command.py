class Command:
    def __init__(self, bot):
        self.bot = bot
        self.name = ''
        self.allow_pm = True
        self.owner_only = False

    def parse(self, message):
        return Message(message, self.bot)


class Message:
    def __init__(self, message, bot):
        self.bot = bot
        self.message = message
        self.author = message.author.name
        self.is_pm = message.server is None
        self.own = message.author.id == bot.user.id

        allargs = message.content.replace('  ', '').split(' ')
        self.args = [] if len(allargs) == 1 else allargs[1:]
        self.cmdname = allargs[0][1:]
        self.text = ' '.join(self.args)

    async def answer(self, content):
        self.bot.log.debug('Sending message "%s" to %s', content, self.message.channel)
        await self.bot.send_message(self.message.channel, content)
