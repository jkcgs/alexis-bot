from models import Starboard
from datetime import datetime
from discord import Object, Embed, Message
from commands.base.command import Command


async def reaction_hook(bot, reaction, user):
    bot.log.debug('reaction to: "%s"', reaction.message.content)
    msg = reaction.message
    if msg.server is None:
        return

    if msg.server.id not in bot.config['starboard_channels'].keys() \
            or bot.config['starboard_channels'][msg.server.id] == msg.id:
        bot.log.debug('not suitable reaction')
        return

    star_item = Starboard.select().where(Starboard.message_id == msg.id)
    if len(star_item) >= 1:
        bot.log.debug('already starboard')
        return

    max_count = 0
    for reaction in msg.reactions:
        if reaction.count > max_count:
            max_count = reaction.count

    if max_count < bot.config['starboard_reactions']:
        bot.log.debug('not enough reaction')
        return

    timestamp = datetime.now()
    Starboard.insert(message_id=msg.id, timestamp=timestamp).execute()
    channel = Object(id=bot.config['starboard_channels'][msg.server.id])

    embed = Embed()
    embed.set_author(name=Command.final_name(msg.author), icon_url=msg.author.avatar_url)
    embed.description = msg.content
    embed.set_footer(text=str(timestamp))

    if len(msg.attachments):
        embed.set_image(url=msg.attachments[0]['url'])

    await bot.send_message(channel, embed=embed)
