from discord import Embed

from modules.base.database import ServerConfig

from datetime import datetime as dt
from datetime import timedelta


class Command:
    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.log
        self.name = ''
        self.swhandler = None
        self.swhandler_break = False
        self.mention_handler = False
        self.configurations = {}
        self.run_task = False
        self.help = ''
        self.allow_pm = True
        self.pm_error = 'Este comando no se puede usar via PM'
        self.owner_only = False
        self.owner_error = 'No puedes usar este comando'

        self.user_delay = 0
        self.users_delay = {}
        self.user_delay_error = 'Aún no puedes usar este comando'

        self.db_models = []
        self.http = bot.http_session

    async def on_member_join(self, member):
        pass

    def task(self):
        pass

    async def config_handler(self, config, value, cmd):
        pass

    def can_manage_roles(self, server):
        self_member = server.get_member(self.bot.user.id)
        return self_member.server_permissions.manage_roles

    def get_config(self, name, server):
        if server is None:
            raise ConfigError('No se puede obtener configuración sin servidor')

        if name not in self.bot.config_handlers:
            raise ConfigError('Esa configuración no existe')

        try:
            conf, created = ServerConfig.get_or_create(name=name, serverid=server.id)
            if created:
                conf.value = self.bot.config_defaults[name]
                conf.save()

            return conf.value
        except ServerConfig.DoesNotExist:
            raise ConfigError('Esa configuración no existe')

    def set_config(self, name, value, server):
        if server is None:
            raise ConfigError('No se puede obtener configuración sin servidor')

        if name not in self.bot.config_handlers:
            raise ConfigError('Esa configuración no existe')

        conf, created = ServerConfig.get_or_create(name=name, serverid=server.id)
        conf.value = value
        conf.save()

    def is_owner(self, member, server):
        return Command.is_owner(self.bot, member, server)

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
            lbinstance = bot.cmds['lockbot'][0]
            lbname = lbinstance.name
            lbnames = [lbname] if isinstance(lbname, str) else lbname
            is_lb_cmd = cmd.is_cmd and cmd.cmdname not in lbnames
            if not is_lb_cmd and lbinstance.is_locked(message.server.id, message.channel.id):
                return

        # Command handler
        try:
            if cmd.is_cmd and cmd.cmdname in bot.cmds:
                bot.log.debug('[command] %s: %s', cmd.author, str(cmd))
                for i in bot.cmds[cmd.cmdname]:
                    if i.owner_only and not cmd.owner:
                        await cmd.answer(i.owner_error)
                    elif not i.allow_pm and cmd.is_pm:
                        await cmd.answer(i.pm_error)
                    elif i.user_delay > 0 and cmd.author.id in i.users_delay \
                            and i.users_delay[cmd.author.id] + timedelta(0, i.user_delay) > dt.now() \
                            and not cmd.owner:
                        await cmd.answer(i.user_delay_error)
                    else:
                        i.users_delay[cmd.author.id] = dt.now()
                        await i.handle(message, cmd)
                return
        except Exception as e:
            await cmd.answer('ocurr.. 1.error c0n\'el$##com@nd..\n```{}```'.format(str(e)))
            bot.log.exception(e)

        # 'startswith' handlers
        swbreak = False
        for swtext in bot.swhandlers.keys():
            if swbreak:
                break

            if message.content.startswith(swtext):
                bot.log.debug('[sw] %s sent message: "%s" handler "%s"', message.author, cmd.text, swtext)
                for swhandler in bot.swhandlers[swtext]:
                    if swhandler.owner_only and not cmd.owner:
                        await cmd.answer(swhandler.owner_error)
                    elif not swhandler.allow_pm and cmd.is_pm:
                        await cmd.answer(swhandler.pm_error)
                    else:
                        await swhandler.handle(message, cmd)

                    if swhandler.swhandler_break:
                        swbreak = True
                        break

        # Mention handlers
        if bot.user.mentioned_in(message):
            for i in bot.mention_handlers:
                if i.owner_only and not cmd.owner:
                    await cmd.answer(i.owner_error)
                elif not i.allow_pm and cmd.is_pm:
                    await cmd.answer(i.pm_error)
                else:
                    await i.handle(message, cmd)


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

        self.cmdname = ''
        self.args = []
        self.argc = 0

        if message.content.startswith(bot.config['command_prefix']):
            self.is_cmd = True
            allargs = message.content.replace('  ', ' ').split(' ')
            self.args = [] if len(allargs) == 1 else [f for f in allargs[1:] if f.strip() != '']
            self.argc = len(self.args)
            self.cmdname = allargs[0][1:]
            self.text = ' '.join(self.args)

        if not self.is_pm:
            self.server_member = message.server.get_member(self.bot.user.id)

    async def answer(self, content='', **kwargs):
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

    def __str__(self):
        return '[MessageCmd name="{}", channel="{}#{}" text="{}"]'.format(
            self.cmdname, self.message.server, self.message.channel, self.text)


class ConfigError(BaseException):
    pass
