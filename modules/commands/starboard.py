import re
from datetime import datetime

import peewee
import emoji
from discord import Emoji, Object, Embed

from modules.base.command import Command
from modules.base.database import BaseModel, ServerConfig

default_count = 10
cfg_starboard_emojis = 'starboard_emojis'
cfg_starboard_channel = 'starboard_channel'
cfg_starboard_tcount = 'starboard_trigger_count'
pat_emoji = re.compile('^<:[a-zA-Z0-9\-_]+:[0-9]+>$')


class StarboardHook(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.db_models = [Starboard]
        self.allow_pm = False
        self.owner_only = True
        self.name = 'starboard'

    async def handle(self, message, cmd):
        args = [] if cmd.argc == 0 else cmd.args[1:]
        argc = len(args)
        subcmd = None if cmd.argc == 0 else cmd.args[0]

        if subcmd == 'channel':
            channel = None
            if argc == 0:
                channel = message.channel
            elif argc == 1:
                if len(message.channel_mentions) > 0:
                    channel = message.channel_mentions[0]
                else:
                    channel = cmd.find_channel(args[0])

            if channel is None:
                await cmd.answer('Canal no encontrado')
                return

            config, _ = ServerConfig.get_or_create(serverid=message.server.id, name=cfg_starboard_channel)
            config.value = channel.id
            config.save()

            await cmd.answer('Canal de starboard actualizado a <#{}>!'.format(channel.id))
        elif subcmd == 'disable':
            config, _ = ServerConfig.get_or_create(serverid=message.server.id, name=cfg_starboard_channel)
            config.value = ''
            config.save()

            await cmd.answer('Starboard desactivado! Para volver a activarlo, utiliza el subcomando "channel".')
        elif subcmd == 'count':
            config, _ = ServerConfig.get_or_create(defaults={'value': str(default_count)},
                                                   serverid=message.server.id, name=cfg_starboard_tcount)
            if argc == 0:
                await cmd.answer('Cuenta trigger actual: ' + str(config.value))
                return

            if not args[0].isdigit():
                await cmd.answer('Utiliza un número entero entre 1 y 10, inclusive.')
                return

            count = int(args[0])
            if count < 1 or count > 1000:
                await cmd.answer('Utiliza un número entero entre 1 y 10, inclusive.')
                return

            config.value = str(count)
            config.save()

            await cmd.answer('Número de trigger definido en **{}**'.format(count))
        elif subcmd == 'emojis':
            config, _ = ServerConfig.get_or_create(defaults={'value': ''},
                                                   serverid=message.server.id, name=cfg_starboard_emojis)

            if argc == 0:
                val = 'Ninguno' if config.value == '' else config.value
                await cmd.answer('Emojis: ' + val)
                return

            if argc > 10:
                await cmd.answer('Formato: <inserte formato aquí>')
                return

            for arg in cmd.args:
                if not pat_emoji.match(arg) and arg not in emoji.UNICODE_EMOJI:
                    await cmd.answer('Formato: <inserte formato aquí>')
                    return

            config, _ = ServerConfig.get_or_create(defaults={'value': ''},
                                                   serverid=message.server.id, name=cfg_starboard_emojis)
            config.value = ' '.join(cmd.text)
            config.save()

            await cmd.answer('Emojis guardados: ' + cmd.text)
        elif subcmd == 'delemojis':
            config, _ = ServerConfig.get_or_create(defaults={'value': ''},
                                                   serverid=message.server.id, name=cfg_starboard_emojis)
            if config.value == '':
                await cmd.answer('No hay emojis definidos para este servidor')
                return

            config.value = ''
            config.save()
            await cmd.answer('Emojis de starboard eliminados (ahora se reacciona con cualquiera).')
        else:
            await cmd.answer('Formato: !{} <subcomando> <opts>.\n'
                             'Subcomandos: channel, disable, count, emojis, delemojis.'.format(cmd.cmdname))

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
        channelid = self.bot.sv_config.get(reaction.message.server.id, cfg_starboard_channel)
        if channelid == '':
            return

        ct_config, _ = ServerConfig.get_or_create(defaults={'value': str(default_count)},
                                                  serverid=reaction.message.server.id,
                                                  name=cfg_starboard_tcount)
        if not ct_config.value.isdigit():
            count_trigger = default_count
            ct_config.value = str(default_count)
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


class Starboard(BaseModel):
    message_id = peewee.TextField(primary_key=True)
    timestamp = peewee.DateTimeField(null=False)
