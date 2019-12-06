import discord

from bot import Command, categories
from bot.regex import pat_channel, pat_snowflake


class ClearReactions(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'clearreactions'
        self.aliases = ['clr']
        self.help = '$[clr-help]'
        self.owner_only = True
        self.category = categories.STAFF

    async def handle(self, cmd):
        if cmd.argc < 1:
            await cmd.answer('$[format]: $[clr-format]')
            return

        await cmd.typing()

        channel = cmd.message.channel
        if pat_channel.match(cmd.args[0]):
            channel = cmd.message.channel_mentions[0]
            cmd.args = cmd.args[1:]
            cmd.argc -= 1

        filtered_len = len([f for f in cmd.args if pat_snowflake.match(f)])
        if cmd.argc != filtered_len:
            await cmd.answer('$[clr-err-ids]')
            return

        success_count = 0
        not_found = []
        for arg in cmd.args:
            try:
                msg = await self.bot.get_message(channel, arg)
                await self.bot.clear_reactions(msg)
                success_count += 1
            except discord.Forbidden:
                pass
            except discord.NotFound:
                not_found.append(arg)

        if success_count == 0:
            msg = ['$[clr-err-any]', '$[clr-err-any-singular]'][cmd.argc == 1]
            locales = {}
            if len(not_found) > 0:
                if cmd.argc == 1:
                    msg += ': $[clr-err-not-found]'
                elif len(not_found) > 1:
                    msg += ': $[clr-err-some-not-found] '
                    msg += '({})'.format(', '.join(not_found))
                else:
                    msg += ': $[clr-err-single-not-found]'
                    locales['message_id'] = not_found[0]
            await cmd.answer(msg, locales=locales)
        elif success_count < cmd.argc:
            msg = '$[clr-err-some-deleted]'
            locales = {}

            if len(not_found) > 1:
                msg += ': $[clr-err-some-not-found] '
                msg += '({})'.format(', '.join(not_found))
            else:
                msg += ': clr-err-single-not-found'
                locales['message_id'] = not_found[0]

            await cmd.answer(msg, locales=locales)
        else:
            await cmd.answer('$[clr-success]')
