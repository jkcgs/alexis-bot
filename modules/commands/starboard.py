import re
from datetime import datetime

import peewee
import emoji
from discord import Emoji, Object, Embed

from modules.base.command import Command
from modules.base.database import BaseModel, ServerConfig

cfg_starboard_emojis = 'starboard_emojis'
cfg_starboard_channel = 'starboard_channel'
cfg_starboard_tcount = 'starboard_trigger_count'
pat_emoji = re.compile('^<:[a-zA-Z0-9\-_]+:[0-9]+>$')


class StarboardHook(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.db_models = [Starboard]

    async def on_reaction_add(self, reaction, user):
        msg = reaction.message
        if msg.server is None:
            return

        # Cargar reacciones admitidas
        emojis_cfg, _ = ServerConfig.get_or_create(defaults={'value': ''},
                                                   serverid=msg.server.id, name=cfg_starboard_emojis)
        reaction_triggers = []
        if emojis_cfg.value != '':
            reaction_filtered = emojis_cfg.value.split(' ')
            for react in reaction_filtered:
                if pat_emoji.match(react):
                    idx = react.rfind(':') + 1
                    reaction_triggers.append(react[idx:-2])
                else:
                    reaction_triggers.append(react)
            reaction_triggers = reaction_filtered

        # Obtener el canal de starboard
        # TODO: optimizar
        config, _ = ServerConfig.get_or_create(serverid=reaction.message.server.id, name=cfg_starboard_channel)
        if config.value == '':
            return
        channelid = config.value

        ct_config, _ = ServerConfig.get_or_create(defaults={'value': str(StarboardTriggerCount.default)},
                                                  serverid=reaction.message.server.id,
                                                  name=cfg_starboard_tcount)
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
            emoji_react = reaction.emoji
            if len(reaction_triggers) != 0:
                if isinstance(emoji_react, str) and emoji_react not in reaction_triggers:
                    self.log.debug('reaction str not suitable %s', emoji_react)
                    continue

                if isinstance(emoji_react, Emoji) and emoji_react.id not in reaction_triggers:
                    self.log.debug('reaction emoji not suitable %s', emoji_react.name)
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

        config, _ = ServerConfig.get_or_create(serverid=message.server.id, name=cfg_starboard_channel)
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
        config, _ = ServerConfig.get_or_create(serverid=message.server.id, name=cfg_starboard_channel)
        config.value = ''
        config.save()

        await cmd.answer('Starboard desactivado!')


class StarboardTriggerCount(Command):
    default = 10

    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['setstarboardtriggercount', 'starboardcount', 'stc']
        self.owner_only = True
        self.allow_pm = False
        self.format = 'Formato: !{} <cuenta (0>N>=1000)>'

    async def handle(self, message, cmd):
        config, _ = ServerConfig.get_or_create(defaults={'value': str(StarboardTriggerCount.default)},
                                               serverid=message.server.id, name=cfg_starboard_tcount)
        if cmd.argc == 0:
            await cmd.answer('Cuenta trigger actual: ' + str(config.value))
            return

        if not cmd.args[0].isdigit():
            await cmd.answer(self.format.format(cmd.cmdname))
            return

        count = int(cmd.args[0])
        if count < 1 or count > 1000:
            await cmd.answer(self.format.format(cmd.cmdname))
            return

        config.value = str(count)
        config.save()

        await cmd.answer('Número de trigger definido en **{}**'.format(count))


class StarboardSetEmojis(Command):

    default = 10

    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['setstarboardemojis', 'sse', 'setemojis']
        self.owner_only = True
        self.allow_pm = False
        self.format = 'Formato: !{} <emoji1 emoji2...emoji10>'

    async def handle(self, message, cmd):
        config, _ = ServerConfig.get_or_create(defaults={'value': ''},
                                               serverid=message.server.id, name=cfg_starboard_emojis)

        if cmd.argc == 0:
            val = 'Ninguno' if config.value == '' else config.value
            await cmd.answer('Emojis: ' + val)
            return

        if cmd.argc > 10:
            await cmd.answer(self.format.format(cmd.cmdname))
            return

        for arg in cmd.args:
            if not pat_emoji.match(arg) and arg not in emoji.UNICODE_EMOJI:
                await cmd.answer(self.format.format(cmd.cmdname))
                return

        config, _ = ServerConfig.get_or_create(defaults={'value': ''},
                                               serverid=message.server.id, name=cfg_starboard_emojis)
        config.value = ' '.join(cmd.text)
        config.save()

        await cmd.answer('Emojis guardados: ' + cmd.text)


class StarboardUnsetEmojis(Command):
    default = 10

    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['unsetstarboardemojis', 'unsetemojis']
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, message, cmd):
        config, _ = ServerConfig.get_or_create(defaults={'value': ''},
                                               serverid=message.server.id, name=cfg_starboard_emojis)
        if config.value == '':
            await cmd.answer('No hay emojis definidos para este servidor')
            return

        config.value = ''
        config.save()
        await cmd.answer('Emojis de starboard eliminados (ahora se reacciona con cualquiera).')


class Starboard(BaseModel):
    message_id = peewee.TextField(primary_key=True)
    timestamp = peewee.DateTimeField(null=False)
