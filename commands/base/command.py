import aiohttp
from discord import Embed


class Command:
    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.log
        self.name = ''
        self.swhandler = None
        self.mention_handler = False
        self.help = ''
        self.allow_pm = True
        self.pm_error = 'Este comando no se puede usar via PM'
        self.owner_only = False
        self.owner_error = 'No puedes usar este comando'

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

    @staticmethod
    def img_embed(url, title=''):
        embed = Embed()
        embed.set_image(url=url)
        if title != '':
            embed.title = title
        return embed

    @staticmethod
    def final_name(user):
        if user is None:
            return 'None'
        return user.nick if hasattr(user, 'nick') and user.nick else user.name


class Message:
    def __init__(self, message, bot):
        self.bot = bot
        self.message = message
        self.author = message.author
        self.author_name = Command.final_name(message.author)
        self.is_pm = message.server is None
        self.own = message.author.id == bot.user.id
        self.owner = False

        allargs = message.content.replace('  ', '').split(' ')
        self.args = [] if len(allargs) == 1 else allargs[1:]
        self.argc = len(self.args)
        self.cmdname = allargs[0][1:]
        self.text = ' '.join(self.args)

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
