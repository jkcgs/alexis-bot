import traceback
from datetime import datetime as dt
from datetime import timedelta

from .configuration import ServerConfigMgrSingle


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
        return ServerConfigMgrSingle(self.bot.sv_config, serverid)

    def right_cmd(self, cmd):
        return cmd.is_cmd and cmd.cmdname == self.name or cmd.cmdname in self.aliases

    def handle(self, cmd):
        pass


async def message_handler(message, bot, cmd):
    if not bot.initialized:
        return

    # Mandar PMs al log
    if cmd.is_pm and message.content != '':
        if cmd.own:
            bot.log.info('[PM] (-> %s): %s', message.channel.user, cmd.text)
        else:
            bot.log.info('[PM] %s: %s', cmd.author, cmd.text)

    # Command handler
    try:
        # Comando válido
        if cmd.is_cmd and cmd.cmdname in bot.cmds:
            # Actualizar id del último que usó un comando (omitir al mismo bot)
            if not cmd.own:
                bot.last_author = message.author.id

            bot.log.debug('[command] %s: %s', cmd.author, str(cmd))
            cmd_ins = bot.cmds[cmd.cmdname]

            # Filtro de permisos y tiempo
            if (cmd_ins.bot_owner_only and not cmd.bot_owner) \
                    or (cmd_ins.owner_only and not cmd.owner) \
                    or (not cmd_ins.allow_pm and cmd.is_pm) \
                    or (not cmd.is_pm and not cmd.is_enabled()):
                return
            elif (cmd_ins.user_delay > 0 and cmd.author.id in cmd_ins.users_delay
                  and cmd_ins.users_delay[cmd.author.id] + timedelta(0, cmd_ins.user_delay) > dt.now()
                  and not cmd.owner):
                await cmd.answer('aún no puedes usar ese comando')
                return
            elif not cmd.is_pm and cmd_ins.nsfw_only and 'nsfw' not in message.channel.name:
                await cmd.answer('este comando sólo puede ser usado en un canal NSFW')
                return
            # Ejecutar el comando
            else:
                if cmd_ins.user_delay > 0:
                    cmd_ins.users_delay[cmd.author.id] = dt.now()

                await cmd_ins.handle(cmd)

        # 'startswith' handlers
        for swtext in bot.swhandlers.keys():
            swtextrep = swtext.replace('$PX', cmd.prefix)
            if message.content.startswith(swtextrep):
                swhandler = bot.swhandlers[swtext]
                if (swhandler.bot_owner_only and not cmd.bot_owner) \
                        or (swhandler.owner_only and not (cmd.owner or cmd.bot_owner))\
                        or (not swhandler.allow_pm and cmd.is_pm):
                    continue
                else:
                    await swhandler.handle(cmd)

                if swhandler.swhandler_break:
                    break

        # Mention handlers
        if bot.user.mentioned_in(message):
            for cmd_ins in bot.mention_handlers:
                if (cmd_ins.bot_owner_only and not cmd.bot_owner)\
                        or (cmd_ins.owner_only and not (cmd.owner or cmd.bot_owner))\
                        or (not cmd_ins.allow_pm and cmd.is_pm):
                    continue

                await cmd_ins.handle(cmd)

    except Exception as e:
        if str(e) == 'BAD REQUEST (status code: 400)':
            e = Exception('Command failed successfully')

        if bot.config['debug']:
            await cmd.answer('ALGO PASÓ OwO\n```{}```'.format(traceback.format_exc()))
        else:
            await cmd.answer('ocurr.. 1.error c0n\'el$##com@nd..\n```{}```'.format(str(e)))
        bot.log.exception(e)
