import traceback
from datetime import datetime as dt
from datetime import timedelta

from bot.events import CommandEvent, BotMentionEvent
from bot.libs.configuration import ServerConfiguration


class Command:
    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.log
        self.name = ''
        self.aliases = []
        self.swhandler = []
        self.swhandler_break = False
        self.mention_handler = False
        self.help = '$[missing-help]'
        self.allow_pm = True
        self.allow_nsfw = True  # TODO
        self.nsfw_only = False  # TODO
        self.pm_error = '$[disallowed-via-pm]'
        self.bot_owner_only = False
        self.owner_only = False
        self.owner_error = 'no puedes usar este comando'
        self.format = ''  # TODO
        self.default_enabled = True
        self.default_config = None

        self.user_delay = 0
        self.users_delay = {}
        self.user_delay_error = 'aún no puedes usar este comando'

        self.db_models = []
        self.http = bot.http_session

    def can_manage_roles(self, server):
        self_member = server.get_member(self.bot.user.id)
        return self_member.server_permissions.manage_roles

    def config_mgr(self, serverid):
        return ServerConfiguration(self.bot.sv_config, serverid)

    def right_cmd(self, cmd):
        return cmd.is_cmd and cmd.cmdname == self.name or cmd.cmdname in self.aliases

    def handle(self, cmd):
        pass


async def message_handler(message, bot, event):
    if not bot.initialized:
        return

    # Mandar PMs al log
    if event.is_pm and message.content != '':
        if event.own:
            bot.log.info('[PM] (-> %s): %s', message.channel.user, event.text)
        else:
            bot.log.info('[PM] %s: %s', event.author, event.text)

    # Command handler
    try:
        # Comando válido
        if isinstance(event, CommandEvent):
            # Actualizar id del último que usó un comando (omitir al mismo bot)
            if not event.self:
                bot.last_author = message.author.id

            bot.log.debug('[command] %s: %s', event.author, str(event))
            cmd_ins = bot.manager[event.cmdname]

            # Filtro de permisos y tiempo
            if (cmd_ins.bot_owner_only and not event.bot_owner) \
                    or (cmd_ins.owner_only and not event.owner) \
                    or (not cmd_ins.allow_pm and event.is_pm) \
                    or (not event.is_pm and not event.is_enabled()):
                return
            elif (cmd_ins.user_delay > 0 and event.author.id in cmd_ins.users_delay
                  and cmd_ins.users_delay[event.author.id] + timedelta(0, cmd_ins.user_delay) > dt.now()
                  and not event.owner):
                await event.answer('aún no puedes usar ese comando')
                return
            elif not event.is_pm and cmd_ins.nsfw_only and 'nsfw' not in message.channel.name:
                await event.answer('este comando sólo puede ser usado en un canal NSFW')
                return
            # Ejecutar el comando
            else:
                result = await cmd_ins.handle(event)
                fine = result is None or (isinstance(result, bool) and result)
                if fine and cmd_ins.user_delay > 0:
                    cmd_ins.users_delay[event.author.id] = dt.now()

        # 'startswith' handlers
        for swtext in bot.manager.swhandlers.keys():
            swtextrep = swtext.replace('$PX', event.prefix)
            if message.content.startswith(swtextrep):
                swhandler = bot.manager.swhandlers[swtext]
                if swhandler.bot_owner_only and not event.bot_owner:
                    continue
                if swhandler.owner_only and not (event.owner or event.bot_owner):
                    continue
                if not swhandler.allow_pm and event.is_pm:
                    continue

                await swhandler.handle(event)
                if swhandler.swhandler_break:
                    break

        # Mention handlers
        if isinstance(event, BotMentionEvent):
            for cmd_ins in bot.manager.mention_handlers:
                if cmd_ins.bot_owner_only and not event.bot_owner:
                    continue
                if cmd_ins.owner_only and not (event.owner or event.bot_owner):
                    continue
                if not cmd_ins.allow_pm and event.is_pm:
                    continue

                await cmd_ins.handle(event)

    except Exception as e:
        if str(e) == 'BAD REQUEST (status code: 400)':
            e = Exception('Command failed successfully')

        if bot.config['debug']:
            await event.answer('ALGO PASÓ OwO\n```{}```'.format(traceback.format_exc()))
        else:
            await event.answer('ocurr.. 1.error c0n\'el$##com@nd..\n```{}```'.format(str(e)))
        bot.log.exception(e)
