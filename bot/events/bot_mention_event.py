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

    async def handle(self):
        for cmd in self.bot.manager.mention_handlers:
            if cmd.bot_owner_only and not self.bot_owner:
                continue
            if cmd.owner_only and not (self.owner or self.bot_owner):
                continue
            if not cmd.allow_pm and self.is_pm:
                continue

            await cmd.handle(self)
