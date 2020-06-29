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
    # 'typing': ['channel', 'user', 'when']
}
