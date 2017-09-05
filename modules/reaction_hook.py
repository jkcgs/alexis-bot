from datetime import datetime

import peewee
from discord import Object, Embed, Emoji
from modules.base.command import Command
from modules.base.database import BaseModel


async def reaction_hook(bot, reaction, user):
    msg = reaction.message
    if msg.server is None:
        return

    channels = bot.config['starboard_channels']
    count_trigger = bot.config['starboard_trigger_count']
    reaction_triggers = bot.config['starboard_trigger_reactions']

    if msg.server.id not in channels.keys() \
            or channels[msg.server.id] == msg.channel.id \
            or 'nsfw' in msg.channel.name.lower():
        return

    star_item = Starboard.select().where(Starboard.message_id == msg.id)
    if len(star_item) >= 1:
        return

    max_count = 0
    for reaction in msg.reactions:
        emoji = reaction.emoji
        if len(reaction_triggers) != 0:
            if isinstance(emoji, str) and emoji not in reaction_triggers:
                bot.log.debug('reaction str not suitable %s', emoji)
                continue

            if isinstance(emoji, Emoji) \
                    and emoji.id not in reaction_triggers \
                    and emoji.name not in reaction_triggers:
                bot.log.debug('reaction emoji not suitable %s', emoji.name)
                continue

        if reaction.count > max_count:
            max_count = reaction.count

    if max_count < count_trigger:
        return

    timestamp = datetime.now()
    Starboard.insert(message_id=msg.id, timestamp=timestamp).execute()
    channel = Object(id=bot.config['starboard_channels'][msg.server.id])

    embed = Embed()
    title = '{} - #{}'.format(Command.final_name(msg.author), msg.channel.name)
    embed.set_author(name=title, icon_url=msg.author.avatar_url)
    embed.description = msg.content
    embed.set_footer(text=str(timestamp))

    if len(msg.attachments):
        embed.set_image(url=msg.attachments[0]['url'])

    reactions = ' | '.join(['{}: {}'.format(str(r.emoji), r.count) for r in msg.reactions])
    embed.add_field(name='Reacciones', value=reactions)

    await bot.send_message(channel, embed=embed)


class Starboard(BaseModel):
    message_id = peewee.TextField(primary_key=True)
    timestamp = peewee.DateTimeField(null=False)
