from modules.base.command import Command


class AltoEn(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ship'
        self.help = 'Forma parejas entre dos usuarios'
        self.allow_pm = False

    async def handle(self, message, cmd):
        if len(cmd.args) != 2 or len(message.mentions) != 2:
            await cmd.answer('Formato: !ship @mención1 @mención2')
            return

        user1 = message.mentions[0].display_name
        user2 = message.mentions[1].display_name
        if user1 == user2:
            await cmd.answer('Sólo hago parejas con personas distintas, bueno? :3')
            return

        ship_name = user1[0:int(len(user1)/2)] + user2[int(len(user2)/2):]
        await cmd.answer('Formando la pareja: **{}**'.format(ship_name))
