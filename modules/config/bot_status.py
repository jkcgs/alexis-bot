from discord import Game

from bot import Command


class BotStatus(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.count = 0

    async def on_ready(self):
        self.bot.schedule(self.task_other, 15)

    async def task_other(self):
        status = ''
        if self.count == 0:
            status = 'Agrégame con !invite'
        elif self.count == 1:
            status = 'Estoy en {} servidores'.format(len(self.bot.servers))
        elif self.count == 2:
            users = set([u.id for u in self.bot.get_all_members() if not u.bot])
            status = 'Ayudando a {} personas'.format(len(users))

        self.count += 1
        if self.count > 2:
            self.count = 0

        await self.bot.change_presence(game=Game(name=status))
