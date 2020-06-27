import discord
from bot.lib.configuration import yaml

from bot import Command
from bot.regex import pat_channel, pat_snowflake
from bot.utils import auto_int, compare_ids

letters = {}
reacts_url = 'https://l.owo.cl/reaction_ids'


class React(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'react'
        self.allow_pm = False
        self.owner_only = True
        self.default_enabled = False

    async def on_ready(self):
        await React.load(self)

    async def handle(self, cmd):
        if cmd.argc < 2:
            await cmd.answer('$[format]: $CMD [#channel=here] <id_message> <text>')
            return

        if pat_channel.match(cmd.args[0]):
            if cmd.argc < 3 or not pat_snowflake.match(cmd.args[1]):
                await cmd.answer('$[format]: $CMD [#channel] <id_message> <text>')
                return

            try:
                chan = await cmd.guild.get_channel(auto_int(cmd.args[0][2:-1]))
            except discord.NotFound:
                await cmd.answer('Channel not found')
                return

            msgid = cmd.args[1]
            text = cmd.args[2]
        else:
            chan = cmd.channel
            msgid = cmd.args[0]
            text = cmd.args[1]

        if not cmd.permissions.add_reactions:
            await cmd.answer('I have no permission to add reactions to that message')
            return

        try:
            msg = await self.bot.get_message(chan, msgid)
        except discord.NotFound:
            await cmd.answer('Message not found')
            return
        except discord.Forbidden or discord.HTTPException:
            await cmd.answer('Could not retrieve the message')
            return

        text = ''.join([c for c in text.lower() if c in letters.keys()])
        if len(text) != len(cmd.args[1]):
            await cmd.answer('Send only allowed characters!')
            return

        if len(text) > 20:
            await cmd.answer('20 characters maximum allowed')
            return

        char_index = {}
        for c in text:
            if c not in char_index:
                char_index[c] = 0

            if char_index[c] >= len(letters[c]):
                continue

            try:
                await msg.add_reaction(letters[c][char_index[c]])
                char_index[c] += 1
            except Exception as e:
                self.log.warn('Could not add a reaction to the message (%s)', letters[c][char_index[c]])
                self.log.exception(e)

    @staticmethod
    async def load(ins):
        ins.log.debug('Loading reaction characters...')
        async with ins.http.get(reacts_url) as r:
            global letters
            letters = yaml.load(await r.text())
            ins.log.debug('Reaction characters loaded!')

        all_reacts = ins.bot.emojis

        for letter, reacts in letters.items():
            for react in reacts:
                if isinstance(react, str) and react.startswith(('\\U', '\\u')):
                    try:
                        reacts[reacts.index(react)] = bytes(react, 'ascii').decode('unicode_escape')
                    except SyntaxError:
                        pass
                elif pat_snowflake.match(react):
                    react_ins = next((x for x in all_reacts if compare_ids(x.id, react)), None)
                    if react_ins is None:
                        reacts.remove(react)
                    else:
                        reacts[reacts.index(react)] = react_ins


class ReactReload(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reactreload'
        self.bot_owner_only = True

    async def handle(self, cmd):
        await cmd.typing()
        await React.load(self)
        await cmd.answer('Done.')
