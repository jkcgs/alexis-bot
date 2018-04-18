from .message_event import MessageEvent


class BotMentionEvent(MessageEvent):
    def __init__(self, message, bot):
        super().__init__(message, bot)

        if not bot.user.mentioned_in(message):
            raise RuntimeError('The message does not contain a bot mention')

        mentions = ['<@{}>'.format(bot.user.id), '<@!{}>'.format(bot.user.id)]
        self.starts_with = message.content.startswith(tuple(mentions))

        self.args = None
        self.argc = None

        if self.starts_with:
            self.args = message.content.replace('  ', ' ').split(' ')[1:]
            self.argc = len(self.args)
            self.text = ' '.join(self.args)
