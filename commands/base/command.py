class Command:
    def __init__(self, bot):
        self.bot = bot

    def parse(self, message, bot):
        return Message(message, bot)


class Message:
    def __init__(self, message, bot):
        self.bot = bot
        self.message = message
        self.author = message.author.name
        self.is_pm = message.server is None
        self.own = message.author.id == bot.user.id

    def answer(self, content):
        self.bot.send_message(self.message.channel, content)
