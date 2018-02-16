from alexis import Command
from discord import Embed
import random


class EightBall(Command):
    resp = ['affirmative', 'negative', 'probably', 'unknown', 'wont-answer']

    def __init__(self, bot):
        super().__init__(bot)
        self.name = '8ball'
        self.aliases = ['bola8', '8']
        self.help = '$[8b-help]'

    async def handle(self, cmd):
        text = cmd.text if cmd.text != '' else '$[8b-default-question]'

        if cmd.text != '':
            resp = random.choice(cmd.l('8b-' + random.choice(EightBall.resp)).split('|'))
        else:
            resp = '$[8b-default-answer]'

        embed = Embed()
        embed.add_field(name='$[8b-title-question]:', value=':8ball: ' + text, inline=False)
        embed.add_field(name='$[8b-title-answer]:', value=':speech_balloon: ' + resp, inline=False)

        await cmd.answer(embed=embed)
