from discord import Embed

from modules.base.database import ServerConfig, ServerConfigMgrSingle

import traceback
from datetime import datetime as dt
from datetime import timedelta


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
    def img_embed(url, title=''):
        embed = Embed()
        embed.set_image(url=url)
        if title != '':
            embed.title = title
        return embed

    @staticmethod
    def get_server_role(server, role_name):
        for role in server.roles:
            if role.name == role_name:
                return role
        return None

    @staticmethod
    def parse(message, bot):
        # TODO: setear instancia del comando que llama si es posible
        msg = MessageCmd(message, bot)
        msg.owner = Command.is_owner(bot, message.author, message.server)
        return msg

    @staticmethod
    def is_owner(bot, member, server):
        if server is None:
            return False

        if member.id in bot.config['owners']:
            return True

        for role in member.roles:
            owner_role = server.id + "@" + role.id
            if owner_role in bot.config['owners']:
                return True

        return False

    @staticmethod
    async def message_handler(message, bot):
        if not bot.initialized:
            return

        cmd = Command.parse(message, bot)

        # Mandar PMs al log
        if cmd.is_pm:
            if cmd.own:
                bot.log.info('[PM] (-> %s): %s', message.channel.user, cmd.text)
            else:
                bot.log.info('[PM] %s: %s', cmd.author, cmd.text)

        # Si es posible, revisar que el canal no ha sido bloqueado (no se revisa si es un PM, si es owner, o si es
        # el comando !lock o lockbot)
        if not cmd.is_pm and not cmd.owner and 'lockbot' in bot.cmds:
            lbinstance = bot.cmds['lockbot']
            lbname = lbinstance.name
            lbnames = [lbname] if isinstance(lbname, str) else lbname
            is_lb_cmd = cmd.is_cmd and cmd.cmdname not in lbnames
            if not is_lb_cmd and lbinstance.is_locked(message.server.id, message.channel.id):
                return

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
                if cmd_ins.owner_only and not (cmd.owner or cmd.bot_owner):
                    # await cmd.answer(cmd_ins.owner_error)
                    return
                # Comando deshabilitado por PM
                elif not cmd_ins.allow_pm and cmd.is_pm:
                    # await cmd.answer(cmd_ins.pm_error)
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
        except Exception as e:
            if bot.config['debug']:
                await cmd.answer('ALGO PASÓ OwO\n```{}```'.format(traceback.format_exc()))
            else:
                await cmd.answer('ocurr.. 1.error c0n\'el$##com@nd..\n```{}```'.format(str(e)))
            bot.log.exception(e)

        # 'startswith' handlers
        swbreak = False
        for swtext in bot.swhandlers.keys():
            if swbreak:
                break

            if message.content.startswith(swtext):
                bot.log.debug('[sw] %s sent message: "%s" handler "%s"', message.author, cmd.text, swtext)
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


class MessageCmd:
    def __init__(self, message, bot):
        self.bot = bot
        self.message = message
        self.author = message.author
        self.author_name = message.author.display_name
        self.is_pm = message.server is None
        self.own = message.author.id == bot.user.id
        self.owner = False
        self.server_member = None
        self.is_cmd = False
        self.text = message.content
        self.config = None
        self.bot_owner = message.author.id in bot.config['bot_owners']

        self.cmdname = ''
        self.prefix = bot.config['command_prefix']
        self.args = []
        self.argc = 0

        if message.content.startswith(self.prefix):
            self.is_cmd = True
            allargs = message.content.replace('  ', ' ').split(' ')
            self.args = [] if len(allargs) == 1 else [f for f in allargs[1:] if f.strip() != '']
            self.argc = len(self.args)
            self.cmdname = allargs[0][1:]
            self.text = ' '.join(self.args)

        if not self.is_pm:
            self.server_member = message.server.get_member(self.bot.user.id)
            self.config = ServerConfigMgrSingle(self.bot.sv_config, message.server.id)

    async def answer(self, content='', to_author=False, withname=True, **kwargs):
        content = content.replace('$PX', self.bot.config['command_prefix'])
        content = content.replace('$NM', self.cmdname)
        content = content.replace('$AU', self.author_name)

        if withname:
            if content != '':
                content = ', ' + content
            content = self.author_name + content

        if to_author:
            await self.bot.send_message(self.message.author, content, **kwargs)
        else:
            await self.bot.send_message(self.message.channel, content, **kwargs)

    async def typing(self):
        await self.bot.send_typing(self.message.channel)

    def member_by_id(self, user_id):
        if self.is_pm:
            return None

        for member in self.message.server.members:
            if member.id == user_id:
                return member

        return None

    def find_channel(self, name_or_id):
        if self.is_pm:
            return None

        for channel in self.message.server.channels:
            if channel.id == name_or_id or channel.name == name_or_id:
                return channel

        return None

    def is_owner(self, user):
        return Command.is_owner(self.bot, user, self.message.server)

    def __str__(self):
        return '[MessageCmd name="{}", channel="{}#{}" text="{}"]'.format(
            self.cmdname, self.message.server, self.message.channel, self.text)
