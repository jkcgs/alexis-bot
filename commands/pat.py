from commands.base.command import Command
import random


class Pat(Command):

    def __init__(self, bot):

        super().__init__(bot)
        self.name = 'pat'
        self.help = 'Te envía una imagen de animé de una caricia en la cabeza y algo más'
        pats = self.bot.config['pats']
        self_pats = self.bot.config['self_pats']
        bot_pat = self.bot.config['bot_pat']

    async def handle(self, message, cmd):
        if len(cmd.args) != 1 or len(message.mentions) != 1:
            await cmd.answer('Formato: !pat <@mención>')
            return

        mention = message.mentions[0]
        text = '{}, {} te ha dado una palmadita :3'.format(
            Command.final_name(mention), cmd.author_name
        )

        if mention.id == cmd.author.id:
            url = random.choice(self.bot.config['self_pats'])
        elif mention.id == self.bot.user.id:
            url = self.bot.config['bot_pat']
            text = 'oye nuuuu >_<'
        else:
            url = random.choice(self.bot.config['pats'])

        await cmd.answer(embed=Command.img_embed(url, text))
