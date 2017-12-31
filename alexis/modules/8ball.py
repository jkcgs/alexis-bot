from alexis import Command
from discord import Embed
import random


class EightBall(Command):
    resp = ['Si', 'No', 'Quizá', 'no preguntis weas xfa', 'jaja xd', 'mira yo opino lo siguiente', 'si weon oh',
            'la respuesta a todo es jesús', 'nopo', 'nopo wn no digai esa wea', 'nuu uwu', 'sip bn dixo',
            'la respueta está en tu corazón', 'demah po', 'si po wn ta diciendo', 'keate piola mejor']

    def __init__(self, bot):
        super().__init__(bot)
        self.name = '8ball'
        self.aliases = ['bola8', '8']
        self.help = 'Responde al texto de forma afirmativa, negativa o dudosa'

    async def handle(self, message, cmd):
        text = cmd.text if cmd.text != '' else 'seré weón?'
        resp = random.choice(EightBall.resp) if cmd.text != '' else 'si po jajaj XDD'

        embed = Embed()
        embed.add_field(name='Pregunta:', value=':8ball: ' + text)
        embed.add_field(name='Respuesta:', value=':speech_balloon: ' + resp)

        await cmd.answer(embed=embed)
