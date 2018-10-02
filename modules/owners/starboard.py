import re
from datetime import datetime

import peewee
import emoji
from discord import Emoji, Object, Embed

from bot import Command, categories
from bot.libs.configuration import BaseModel

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
        self.help = '$[starboard-help]'
        self.format = '$[starboard-format]'
        self.category = categories.STAFF

    async def handle(self, cmd):
        args = [] if cmd.argc == 0 else cmd.args[1:]
        argc = len(args)
        subcmd = None if cmd.argc == 0 else cmd.args[0]

        if subcmd == 'channel':
            channel = None
            if argc == 0:
                channel = cmd.message.channel
            elif argc == 1:
                if len(cmd.message.channel_mentions) > 0:
                    channel = cmd.message.channel_mentions[0]
                else:
                    channel = cmd.find_channel(args[0])

            if channel is None:
                await cmd.answer('$[channel-not-found]')
                return

            cmd.config.set(cfg_starboard_channel, channel.id)
            await cmd.answer('$[starboard-channel-set]', locales={'channel_id': channel.id})
        elif subcmd == 'disable':
            cmd.config.set(cfg_starboard_channel, '')
            await cmd.answer('$[starboard-disabled]')
        elif subcmd == 'count':
            if argc == 0:
                count = cmd.config.get(cfg_starboard_tcount, default_count)
                await cmd.answer('$[starboard-count-status]', locales={'count': count})
                return

            if not args[0].isdigit():
                await cmd.answer('$[starboard-err-count]')
                return

            count = int(args[0])
            if count < 1 or count > 1000:
                await cmd.answer('$[starboard-err-count]')
                return

            cmd.config.set(cfg_starboard_tcount, count)
            await cmd.answer('$[starboard-count-set]', locales={'count': count})
        elif subcmd == 'emojis':
            emojis = cmd.config.get(cfg_starboard_emojis)

            if argc == 0:
                val = '$[starboard-none]' if emojis == '' else emojis
                await cmd.answer('$[starboard-emoji-list]', locales={'emojis': val})
                return

            if argc > 10:
                await cmd.answer('$[format]: $[starboard-emoji-format]')
                return

            for arg in cmd.args:
                if not pat_emoji.match(arg) and arg not in emoji.UNICODE_EMOJI:
                    await cmd.answer('$[format]: $[starboard-emoji-format]')
                    return

            res = cmd.config.set(cfg_starboard_emojis, cmd.text)
            await cmd.answer('$[starboard-emoji-set]', locales={'emojis': res})
        elif subcmd == 'delemojis':
            cmd.config.set(cfg_starboard_emojis, '')
            await cmd.answer('$[starboard-emoji-deleted]')
        elif subcmd == 'nsfw':
            if argc == 0:
                val = cmd.config.get(cfg_starboard_nsfw, '0')
                msg = ['$[starboard-nsfw-disabled]', '$[starboard-nsfw-enabled]'][val == '1']
                await cmd.answer('$[starboard-nsfw-status] {}'.format(msg))
            else:
                arg = cmd.args[0].lower()
                if arg in ['true', '1'] + cmd.lang.get_list('starboard-nsfw-on'):
                    cmd.config.set(cfg_starboard_nsfw, '1')
                    await cmd.answer('$[starboard-nsfw-set-enabled]')
                elif arg in ['false', '0'] + cmd.lang.get_list('starboard-nsfw-off'):
                    cmd.config.set(cfg_starboard_nsfw, '0')
                    await cmd.answer('$[starboard-nsfw-set-disabled]')
                else:
                    await cmd.answer('$[format]: $[starboard-nsfw-format]')
        else:
            await cmd.answer('$[starboard-format].', locales={'command_name': cmd.cmdname})

    async def on_reaction_add(self, reaction, user):
        msg = reaction.message
        if msg.server is None:
            return

        config = self.config_mgr(reaction.message.server.id)
        # Load allowed reactions
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

        # Get the starboard channel
        channelid = config.get(cfg_starboard_channel)
        if channelid == '':
            return

        ct_config = config.get(cfg_starboard_tcount, default_count)
        if not ct_config.isdigit():
            config.set(cfg_starboard_tcount, default_count)
            count_trigger = default_count
        else:
            count_trigger = int(ct_config)

        # Ignore messages on the starboard channel or from the bot itself
        if channelid == msg.channel.id or msg.author.id == self.bot.user.id:
            return

        # Ignore NSFW channels if they are ignored
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
        embed.add_field(name='$[starboard-reactions]', value=reactions)

        await self.bot.send_message(channel, embed=embed)


class Starboard(BaseModel):
    message_id = peewee.TextField()
    timestamp = peewee.DateTimeField(null=False)
