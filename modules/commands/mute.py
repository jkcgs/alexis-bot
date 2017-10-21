from datetime import datetime

import peewee

from modules.base.command import Command
from modules.base.database import BaseModel


class Mute(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'mute'
        self.help = 'Mutea usuarios'
        self.owner_only = True
        self.db_models = [MutedUser]
        self.run_task = True

    async def handle(self, message, cmd):
        if len(cmd.args) < 1 or len(message.mentions) != 1:
            await cmd.answer('Formato: !mute <@mención> [duración] [razón]')
            return

        await cmd.answer('Este comando aún no está listo')

    async def on_member_join(self, member):
        pass

    async def task(self):
        pass


class Unmute(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'unmute'
        self.help = 'Quita el mute de usuarios'
        self.owner_only = True

    async def handle(self, message, cmd):
        if len(cmd.args) != 1 or len(message.mentions) != 1:
            await cmd.answer('Formato: !unmute <@mención>')
            return

        await cmd.answer('Este comando aún no está listo')


class MutedUser(BaseModel):
    userid = peewee.TextField(null=False)
    serverid = peewee.TextField(null=False)
    until = peewee.DateTimeField(default=datetime.now)
    reason = peewee.TextField(default='')
    author = peewee.TextField(null=False)
