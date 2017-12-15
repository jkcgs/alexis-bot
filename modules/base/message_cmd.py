from modules.base.database import ServerConfigMgrSingle
from modules.base import utils


class MessageCmd:
    def __init__(self, message, bot):
        self.bot = bot
        self.message = message
        self.author = message.author
        self.author_name = message.author.display_name
        self.is_pm = message.server is None
        self.own = message.author.id == bot.user.id
        self.owner = utils.is_owner(bot, message.author, message.server)
        self.server_member = None
        self.is_cmd = False
        self.text = message.content
        self.config = None
        self.bot_owner = message.author.id in bot.config['bot_owners']

        self.cmdname = ''
        self.args = []
        self.argc = 0

        if not self.is_pm:
            self.server_member = message.server.get_member(self.bot.user.id)
            self.config = ServerConfigMgrSingle(self.bot.sv_config, message.server.id)
            self.prefix = self.config.get('command_prefix', bot.config['command_prefix'])
        else:
            self.prefix = bot.config['command_prefix']

        if message.content.startswith(self.prefix):
            self.is_cmd = True
            allargs = message.content.replace('  ', ' ').split(' ')
            self.args = [] if len(allargs) == 1 else [f for f in allargs[1:] if f.strip() != '']
            self.argc = len(self.args)
            self.cmdname = allargs[0][len(self.prefix):]
            self.text = ' '.join(self.args)

    async def answer(self, content='', to_author=False, withname=True, **kwargs):
        content = content.replace('$PX', self.prefix)
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
        return utils.is_owner(self.bot, user, self.message.server)

    def no_tags(self):
        txt = self.text
        for mention in self.message.mentions:
            txt = txt.replace(mention.mention, mention.display_name)

        return txt

    def __str__(self):
        return '[MessageCmd name="{}", channel="{}#{}" text="{}"]'.format(
            self.cmdname, self.message.server, self.message.channel, self.text)
