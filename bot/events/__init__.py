from .message_event import MessageEvent
from .command_event import CommandEvent
from .bot_mention_event import BotMentionEvent


def parse_event(message, bot):
    if CommandEvent.is_command(message, bot):
        return CommandEvent(message, bot)

    if bot.user.mentioned_in(message) and message.author != bot.user:
        return BotMentionEvent(message, bot)

    return MessageEvent(message, bot)


def is_bot_command(event):
    return isinstance(event, CommandEvent) or (isinstance(event, BotMentionEvent) and event.starts_with)

