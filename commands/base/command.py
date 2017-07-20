class Command:
    def __init__(self, bot, message):
        self.bot = bot
        self.message = message
        self.author = message.author.name
        self.is_pm = message.server is None
        self.own = message.author.id == self.bot.user.id
