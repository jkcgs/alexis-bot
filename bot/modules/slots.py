from bot import Command, StaticConfig
from discord import Embed
import random

defaults = {
    'slots_fruits': [':cookie:', ':apple:', ':tangerine:', ':lemon:', ':cherries:', ':grapes:', ':watermelon:',
                     ':strawberry:', ':peach:', ':melon:', ':banana:', ':pear:', ':pineapple:']
}


class Slots(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'slots'
        self.mention_handler = False
        self.help = 'Juega al Tragamonedas favorito de tu abuela'
        self.owner_only = False
        self.enabled = True
        self.config = StaticConfig.get_config('slots', defaults)

    async def handle(self, cmd):
        frutas = self.config['slots_fruits']
        if len(frutas) < 3:
            await cmd.answer('este comando no funciona u_u')
            return

        slot1 = random.choice(frutas)
        slot2 = random.choice(frutas)
        slot3 = random.choice(frutas)
        if slot1 == slot2 == slot3:
            text = 'Ganaste wn!  :confetti_ball:'
        elif slot1 == slot2 or slot1 == slot3 or slot2 == slot3:
            text = 'Casi wn, casi. [2/3]'
        else:
            text = 'Mala cuea. Pa\' la otra será.'

        slots = Embed(color=0xf07247)
        desc = '**{}** tiró la palanca...\n\n**[ {} | {} | {} ]**\n\n{}'
        desc = desc.format(cmd.author_name, slot1, slot2, slot3, text)
        slots.description = desc
        await cmd.answer(embed=slots)
        return
