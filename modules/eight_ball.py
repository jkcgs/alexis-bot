from bot import Command, categories
from discord import Embed
import random


class EightBall(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'

    resp = ['affirmative', 'negative', 'probably', 'unknown', 'wont-answer']

    def __init__(self, bot):
        super().__init__(bot)
        self.name = '8ball'
        self.aliases = ['bola8', '8']
        self.help = '$[8b-help]'
        self.category = categories.FUN

    async def handle(self, cmd):
        text = cmd.text if cmd.text != '' else '$[8b-default-question]'
        resp = '$[8b-default-answer]'

        if cmd.text != '':
            resp = random.choice(cmd.lng('8b-' + random.choice(EightBall.resp)).split('|'))

        embed = Embed()
        embed.add_field(name=':8ball: $[8b-title-question]:', value=text, inline=False)
        embed.add_field(name=':speech_balloon: $[8b-title-answer]:', value=resp, inline=False)

        await cmd.answer(embed)
