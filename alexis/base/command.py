import traceback
from datetime import datetime as dt
from datetime import timedelta

from alexis.base.database import ServerConfigMgrSingle


class Command:
    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.log
        self.name = ''
        self.aliases = []
        self.swhandler = None
        self.swhandler_break = False
        self.mention_handler = False
        self.help = '<el que hizo la weaita no le puso texto de ayuda jij>'
        self.allow_pm = True
        self.allow_nsfw = True  # TODO
        self.nsfw_only = False  # TODO
        self.pm_error = 'este comando no se puede usar via PM'
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

    @staticmethod
    async def message_handler(message, bot, cmd):
        if not bot.initialized:
            return

        # Mandar PMs al log
        if cmd.is_pm:
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

                # Sólo owner del bot
                if cmd_ins.bot_owner_only and not cmd.bot_owner:
                    return
                # Sólo owner
                elif cmd_ins.owner_only and not cmd.owner:
                    # await cmd.answer(cmd_ins.owner_error)
                    return
                # Comando deshabilitado por PM
                elif not cmd_ins.allow_pm and cmd.is_pm:
                    # await cmd.answer(cmd_ins.pm_error)
                    return
                elif not cmd.is_pm and not cmd.is_enabled():
                    return
                # Delay para el comando
                elif cmd_ins.user_delay > 0 and cmd.author.id in cmd_ins.users_delay \
                        and cmd_ins.users_delay[cmd.author.id] + timedelta(0, cmd_ins.user_delay) > dt.now() \
                        and not cmd.owner:
                    # await cmd.answer(cmd_ins.user_delay_error)
                    return
                # Ejecutar el comando
                else:
                    cmd_ins.users_delay[cmd.author.id] = dt.now()
                    await cmd_ins.handle(message, cmd)

            # 'startswith' handlers
            swbreak = False
            for swtext in bot.swhandlers.keys():
                if swbreak:
                    break

                swtextrep = swtext.replace('$PX', cmd.prefix)
                if message.content.startswith(swtextrep):
                    swhandler = bot.swhandlers[swtext]
                    if swhandler.bot_owner_only and not cmd.bot_owner:
                        continue
                    if swhandler.owner_only and not (cmd.owner or cmd.bot_owner):
                        # await cmd.answer(swhandler.owner_error)
                        continue
                    elif not swhandler.allow_pm and cmd.is_pm:
                        # await cmd.answer(swhandler.pm_error)
                        continue
                    else:
                        await swhandler.handle(message, cmd)

                    if swhandler.swhandler_break:
                        swbreak = True
                        break

            # Mention handlers
            if bot.user.mentioned_in(message):
                for cmd_ins in bot.mention_handlers:
                    if cmd_ins.bot_owner_only and not cmd.bot_owner:
                        continue
                    if cmd_ins.owner_only and not (cmd.owner or cmd.bot_owner):
                        # await cmd.answer(cmd_ins.owner_error)
                        continue
                    elif not cmd_ins.allow_pm and cmd.is_pm:
                        # await cmd.answer(cmd_ins.pm_error)
                        continue
                    else:
                        await cmd_ins.handle(message, cmd)

        except Exception as e:
            if str(e) == 'BAD REQUEST (status code: 400)':
                e = Exception('Command failed successfully')

            if bot.config['debug']:
                await cmd.answer('ALGO PASÓ OwO\n```{}```'.format(traceback.format_exc()))
            else:
                await cmd.answer('ocurr.. 1.error c0n\'el$##com@nd..\n```{}```'.format(str(e)))
            bot.log.exception(e)
