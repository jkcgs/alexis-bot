import traceback

from discord import Colour

from bot import Command, CommandEvent, BotMentionEvent, MessageEvent
from bot.lib.common import is_bot_owner, is_owner, is_pm
from bot.lib.guild_configuration import GuildConfiguration


class CommandHandler(Command):
    __author__ = 'makzk'
    __version__ = '1.0.1'

    async def on_message(self, message):
        if CommandEvent.is_command(message, self.bot):
            event = CommandEvent(message, self.bot)
        elif self.bot.user.mentioned_in(message) and message.author != self.bot.user:
            event = BotMentionEvent(message, self.bot)
        else:
            return

        if isinstance(event, CommandEvent):
            self.log.debug('[command] %s: %s', event.author, str(event))

        try:
            await event.handle()
        except Exception as e:
            if self.bot.config['debug']:
                content = '```{}```'.format(traceback.format_exc())
                title = '$[error-debug]'
            else:
                content = '```{}```'.format(str(e))
                title = '$[error-msg]'

            await event.answer(content, title=title, as_embed=True, colour=Colour.red())
            self.log.exception(e)


class StartsWithHandler(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    async def on_message(self, message):
        try:
            mgr_swhandlers = self.bot.manager.swhandlers
            swhandlers = []
            config = GuildConfiguration.get_instance(message.guild)
            for swtext in mgr_swhandlers.keys():
                swtextrep = swtext.replace('$PX', config.prefix)
                if message.content.startswith(swtextrep):
                    swhandler = mgr_swhandlers[swtext]
                    if (swhandler.bot_owner_only and not is_bot_owner(message.author, self.bot))\
                            or swhandler.owner_only and not is_owner(self.bot, message)\
                            or not swhandler.allow_pm and is_pm(message):
                        continue

                    swhandlers.append(swhandler)
                    if swhandler.swhandler_break:
                        break

            if len(swhandlers) > 0:
                event = MessageEvent(message, self.bot)
                for handler in swhandlers:
                    await handler.handle(event)

        except Exception as e:
            self.log.exception(e)
