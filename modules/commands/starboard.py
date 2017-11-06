from datetime import datetime

import peewee
from discord import Emoji, Object, Embed

from modules.base.command import Command
from modules.base.database import BaseModel, ServerConfig


class StarboardHook(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.db_models = [Starboard]

    async def on_reaction_add(self, reaction, user):
        msg = reaction.message
        if msg.server is None:
            return

        # TODO: stub, implementar y hacer configurable
        reaction_triggers = []

        # TODO: optimizar
        config, _ = ServerConfig.get_or_create(serverid=reaction.message.server.id, name=StarboardChanSet.cfg)
        if config.value == '':
            return
        channelid = config.value

        ct_config, _ = ServerConfig.get_or_create(defaults={'value': str(StarboardTriggerCount.default)},
                                                  serverid=reaction.message.server.id,
                                                  name=StarboardTriggerCount.cfg)
        if not ct_config.value.isdigit():
            count_trigger = StarboardTriggerCount.default
            ct_config.value = str(StarboardTriggerCount.default)
            ct_config.save()
        else:
            count_trigger = int(ct_config.value)

        # Ignorar mensaje si es del mismo canal del starboard o si es de un canal NSFW
        # TODO: ignorar NSFW configurable
        if channelid == msg.channel.id or 'nsfw' in msg.channel.name.lower():
            return

        star_item = Starboard.select().where(Starboard.message_id == msg.id)
        if len(star_item) >= 1:
            return

        max_count = 0
        for reaction in msg.reactions:
            emoji = reaction.emoji
            if len(reaction_triggers) != 0:
                if isinstance(emoji, str) and emoji not in reaction_triggers:
                    self.log.debug('reaction str not suitable %s', emoji)
                    continue

                if isinstance(emoji, Emoji) \
                        and emoji.id not in reaction_triggers \
                        and emoji.name not in reaction_triggers:
                    self.log.debug('reaction emoji not suitable %s', emoji.name)
                    continue

            if reaction.count > max_count:
                max_count = reaction.count

        if max_count < count_trigger:
            return

        timestamp = datetime.now()
        Starboard.insert(message_id=msg.id, timestamp=timestamp).execute()
        channel = Object(id=channelid)

        embed = Embed()
        title = '{} - #{}'.format(msg.author.display_name, msg.channel.name)
        embed.set_author(name=title, icon_url=msg.author.avatar_url)
        embed.description = msg.content
        embed.set_footer(text=str(timestamp))

        if len(msg.attachments):
            embed.set_image(url=msg.attachments[0]['url'])

        reactions = ' | '.join(['{}: {}'.format(str(r.emoji), r.count) for r in msg.reactions])
        embed.add_field(name='Reacciones', value=reactions)

        await self.bot.send_message(channel, embed=embed)


class StarboardChanSet(Command):
    cfg = 'starboard_channel'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['setstarboardchannel', 'ssc']
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, message, cmd):
        channel = None
        if cmd.argc == 0:
            channel = message.channel
        elif cmd.argc == 1:
            if len(message.channel_mentions) > 0:
                channel = message.channel_mentions[0]
            else:
                channel = cmd.find_channel(cmd.args[0])

        if channel is None:
            await cmd.answer('Canal no encontrado')
            return

        config, _ = ServerConfig.get_or_create(serverid=message.server.id, name=StarboardChanSet.cfg)
        config.value = channel.id
        config.save()

        await cmd.answer('Canal de starboard actualizado a <#{}>!'.format(channel.id))


class StarboardChanUnset(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['usetstarboardchannel', 'usc', 'disablestarboard']
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, message, cmd):
        config, _ = ServerConfig.get_or_create(serverid=message.server.id, name=StarboardChanSet.cfg)
        config.value = ''
        config.save()

        await cmd.answer('Starboard desactivado!')


class StarboardTriggerCount(Command):
    cfg = 'starboard_trigger_count'
    default = 10

    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['setstarboardtriggercount', 'starboardcount', 'stc']
        self.owner_only = True
        self.allow_pm = False
        self.format = 'Formato: !{} <cuenta (0>N>=1000)>'

    async def handle(self, message, cmd):
        if cmd.argc == 0 or not cmd.args[0].isdigit():
            await cmd.answer(self.format.format(cmd.cmdname))
            return

        count = int(cmd.args[0])
        if count > 1000:
            await cmd.answer(self.format.format(cmd.cmdname))
            return

        config, _ = ServerConfig.get_or_create(defaults={'value': str(StarboardTriggerCount.default)},
                                               serverid=message.server.id, name=StarboardTriggerCount.cfg)
        config.value = str(count)
        config.save()

        await cmd.answer('Número de trigger definido en **{}**'.format(count))


class Starboard(BaseModel):
    message_id = peewee.TextField(primary_key=True)
    timestamp = peewee.DateTimeField(null=False)
