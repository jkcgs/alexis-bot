import re
from datetime import datetime

import peewee
import emoji
from discord import Emoji, Object, Embed

from alexis import Command
from alexis.base.database import BaseModel, ServerConfig

default_count = 10
cfg_starboard_emojis = 'starboard_emojis'
cfg_starboard_channel = 'starboard_channel'
cfg_starboard_tcount = 'starboard_trigger_count'
cfg_starboard_nsfw = 'starboard_watch_nsfw'
pat_emoji = re.compile('^<:[a-zA-Z0-9\-_]+:[0-9]+>$')


class StarboardHook(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.db_models = [Starboard]
        self.allow_pm = False
        self.owner_only = True
        self.name = 'starboard'
        self.help = 'Administrar el starboard'

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

            cmd.config.set(cfg_starboard_channel, channel.id)
            await cmd.answer('canal de starboard actualizado a <#{}>!'.format(channel.id))
        elif subcmd == 'disable':
            cmd.config.set(cfg_starboard_channel, '')
            await cmd.answer('Starboard desactivado! Para volver a activarlo, utiliza el subcomando "channel".')
        elif subcmd == 'count':
            if argc == 0:
                count = cmd.config.get(cfg_starboard_tcount, default_count)
                await cmd.answer('cuenta trigger actual: ' + count)
                return

            if not args[0].isdigit():
                await cmd.answer('utiliza un número entero entre 1 y 10, inclusive.')
                return

            count = int(args[0])
            if count < 1 or count > 1000:
                await cmd.answer('utiliza un número entero entre 1 y 10, inclusive.')
                return

            cmd.config.set(cfg_starboard_tcount, count)
            await cmd.answer('número de trigger definido en **{}**'.format(count))
        elif subcmd == 'emojis':
            emojis = cmd.config.get(cfg_starboard_emojis)

            if argc == 0:
                val = 'Ninguno' if emojis == '' else emojis
                await cmd.answer('emojis: ' + val)
                return

            if argc > 10:
                await cmd.answer('formato: <inserte formato aquí>')
                return

            for arg in cmd.args:
                if not pat_emoji.match(arg) and arg not in emoji.UNICODE_EMOJI:
                    await cmd.answer('formato: <inserte formato aquí>')
                    return

            res = cmd.config.set(cfg_starboard_emojis, cmd.text)
            await cmd.answer('emojis guardados: ' + res)
        elif subcmd == 'delemojis':
            cmd.config.set(cfg_starboard_emojis, '')
            await cmd.answer('emojis de starboard eliminados (ahora se reacciona con cualquiera).')
        elif subcmd == 'nsfw':
            if argc == 0:
                val = cmd.config.get(cfg_starboard_nsfw, '0')
                msg = 'activado :speak_no_evil:' if val == '1' else 'desactivado :dolphin:'
                await cmd.answer('starboard para canales NSFW: {}'.format(msg))
            else:
                arg = cmd.args[0].lower()
                if arg in ['yes', 'true', '1', 'on', 'si']:
                    cmd.config.set(cfg_starboard_nsfw, '1')
                    await cmd.answer('starboard para NSFW activado :flushed:')
                elif arg in ['no', 'false', '0', 'off']:
                    cmd.config.set(cfg_starboard_nsfw, '0')
                    await cmd.answer('starboard para NSFW desactivado :two_hearts:')
                else:
                    await cmd.answer('Formato: nsfw [on|off]')
        else:
            await cmd.answer('formato: $PX{} <subcomando> <opts>.\n'
                             'Subcomandos: channel, disable, count, emojis, delemojis, nfsw.'.format(cmd.cmdname))

    async def on_reaction_add(self, reaction, user):
        msg = reaction.message
        if msg.server is None:
            return

        config = self.config_mgr(reaction.message.server.id)
        # Cargar reacciones admitidas
        emojis = config.get(cfg_starboard_emojis)
        reaction_triggers = []
        if emojis != '':
            reaction_filtered = emojis.split(' ')
            for react in reaction_filtered:
                if pat_emoji.match(react):
                    idx = react.rfind(':') + 1
                    reaction_triggers.append(react[idx:-2])
                else:
                    reaction_triggers.append(react)
            reaction_triggers = reaction_filtered

        # Obtener el canal de starboard
        channelid = config.get(cfg_starboard_channel)
        if channelid == '':
            return

        ct_config = config.get(cfg_starboard_tcount, default_count)
        if not ct_config.isdigit():
            config.set(cfg_starboard_tcount, default_count)
            count_trigger = default_count
        else:
            count_trigger = int(ct_config)

        # Ignorar mensaje si es del mismo canal del starboard o del mismo bot
        if channelid == msg.channel.id or msg.author.id == self.bot.user.id:
            return

        # Ignorar mensaje si es de un canal NSFW
        if 'nsfw' in msg.channel.name.lower() and config.get(cfg_starboard_nsfw, '0') == '0':
            return

        star_item = Starboard.select().where(Starboard.message_id == msg.id)
        if len(star_item) >= 1:
            return

        max_count = 0
        for reaction in msg.reactions:
            emoji_react = reaction.emoji
            if len(reaction_triggers) != 0:
                if isinstance(emoji_react, str) and emoji_react not in reaction_triggers:
                    continue

                if isinstance(emoji_react, Emoji) and emoji_react.id not in reaction_triggers:
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
