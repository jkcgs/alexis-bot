from bot import Command, Configuration, categories
from discord import Embed
import random

defaults = {
    'slots_fruits': [':cookie:', ':apple:', ':tangerine:', ':lemon:', ':cherries:', ':grapes:', ':watermelon:',
                     ':strawberry:', ':peach:', ':melon:', ':banana:', ':pear:', ':pineapple:']
}


class Slots(Command):
    __author__ = 'Yaranaika'
    __version__ = '1.0.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'slots'
        self.mention_handler = False
        self.help = '$[slots-help]'
        self.owner_only = False
        self.enabled = True
        self.category = categories.FUN
        self.config = Configuration.get_config('slots', defaults)

    async def handle(self, cmd):
        frutas = self.config['slots_fruits']
        if len(frutas) < 3:
            await cmd.answer('$[slots-error-notavailable]')
            return

        slot1 = random.choice(frutas)
        slot2 = random.choice(frutas)
        slot3 = random.choice(frutas)
        if slot1 == slot2 == slot3:
            text = '$[slots-win-3-3]'
        elif slot1 == slot2 or slot1 == slot3 or slot2 == slot3:
            text = '$[slots-win-2-3]'
        else:
            text = '$[slots-win-1-3]'

        slots = Embed(color=0xf07247)
        desc = '$[slots-play]\n\n**[ {} | {} | {} ]**\n\n{}'
        desc = desc.format(slot1, slot2, slot3, text)
        slots.description = desc
        await cmd.answer(embed=slots, locales={'user': cmd.author_name})
