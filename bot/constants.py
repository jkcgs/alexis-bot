from os import path

bot_root = path.abspath(path.join(path.dirname(__file__), '..'))
BOT_VERSION = '1.0.0-dev7'
REPOSITORY_URL = 'https://github.com/jkcgs/alexis-bot'

DISCORD_BASE = 'https://discord.com'

EVENT_HANDLERS = {
    'message': ['message'],
    'reaction_add': ['reaction', 'user'],
    'reaction_remove': ['reaction', 'user'],
    'reaction_clear': ['message', 'reactions'],
    'member_join': ['member'],
    'member_remove': ['member'],
    'member_update': ['before', 'after'],
    'user_update': ['before', 'after'],
    'message_delete': ['message'],
    'message_edit': ['before', 'after'],
    'guild_join': ['guild'],
    'guild_remove': ['guild'],
    'member_ban': ['guild', 'user'],
    'member_unban': ['guild', 'user'],
    'raw_reaction_add': ['payload'],
    'raw_reaction_remove': ['payload'],
    'raw_reaction_clear': ['payload'],
    'raw_reaction_clear_emoji': ['payload'],
    # 'typing': ['channel', 'user', 'when']
}
