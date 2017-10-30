from discord import Embed

from modules.base.database import ServerConfig


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

    def parse(self, message):
        msg = Message(message, self.bot)
        msg.owner = self.is_owner(message.author, message.server)
        return msg

    def is_owner(self, member, server):
        if server is None:
            return False

        if member.id in self.bot.config['owners']:
            return True

        for role in member.roles:
            owner_role = server.id + "@" + role.id
            if owner_role in self.bot.config['owners']:
                return True

        return False

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


class Message:
    def __init__(self, message, bot):
        self.bot = bot
        self.message = message
        self.author = message.author
        self.author_name = message.author.display_name
        self.is_pm = message.server is None
        self.own = message.author.id == bot.user.id
        self.owner = False
        self.server_member = None

        allargs = message.content.replace('  ', ' ').split(' ')
        self.args = [] if len(allargs) == 1 else [f for f in allargs[1:] if f.strip() != '']
        self.argc = len(self.args)
        self.cmdname = allargs[0][1:]
        self.text = ' '.join(self.args)
        self.bot.log.debug('args: %s, argc: %s', self.args, self.argc)

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


class ConfigError(BaseException):
    pass
