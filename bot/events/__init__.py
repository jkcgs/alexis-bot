from .message_event import MessageEvent
from .command_event import CommandEvent
from .bot_mention_event import BotMentionEvent


def is_bot_command(event):
    return isinstance(event, CommandEvent) or (isinstance(event, BotMentionEvent) and event.starts_with)
