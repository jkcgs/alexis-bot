from alexis import Command
from discord import Embed
import random


class EightBall(Command):
    resp = ['Si', 'No', 'Quizá', 'no preguntis weas xfa', 'jaja xd', 'mira yo opino lo siguiente', 'si weon oh',
            'la respuesta a todo es jesús', 'nopo', 'nopo wn no digai esa wea', 'nuu uwu', 'sip :3',
            'la respuesta está en tu corazón', 'demah po', 'si po wn ta diciendo', 'keate piola mejor',
            'no cacho', 'sinceramente, no sé', 'quizá', 'eso deberías saberlo ya', 'y a mi me lo preguntas?',
            '._.', ':thumbsup:', ':thumbsdown:', 'no entendí', 'hable más fuerte que traigo una toalla',
            'no va a poder ser ná', 'sipo ta bn eso', 'nopo ta mal eso', 'xd', 'si pero no',
            'esa es una muy buena pregunta']

    def __init__(self, bot):
        super().__init__(bot)
        self.name = '8ball'
        self.aliases = ['bola8', '8']
        self.help = 'Responde al texto de forma afirmativa, negativa o dudosa'

    async def handle(self, cmd):
        text = cmd.text if cmd.text != '' else 'seré weón?'
        resp = random.choice(EightBall.resp) if cmd.text != '' else 'si po jajaj XDD'

        embed = Embed()
        embed.add_field(name='Pregunta:', value=':8ball: ' + text, inline=False)
        embed.add_field(name='Respuesta:', value=':speech_balloon: ' + resp, inline=False)

        await cmd.answer(embed=embed)
