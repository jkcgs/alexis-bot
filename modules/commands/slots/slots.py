from os import path

import yaml

from modules.base.command import Command
from discord import Embed
import random


class Slots(Command):
    def_frutas = [':cookie:', ':apple:', ':tangerine:', ':lemon:', ':cherries:', ':grapes:', ':watermelon:',
                  ':strawberry:', ':peach:', ':melon:', ':banana:', ':pear:', ':pineapple:']

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'slots'
        self.mention_handler = False
        self.help = 'Juega al Tragamonedas favorito de tu abuela'
        self.owner_only = False
        self.frutas = self.load_config()
        if len(self.frutas) < 3:
            self.frutas = set(list(self.frutas) + self.def_frutas)

    async def handle(self, message, cmd):
        if len(self.frutas) < 3:
            await cmd.answer('este comando no funciona u_u')
            return

        slot1 = random.choice(self.frutas)
        slot2 = random.choice(self.frutas)
        slot3 = random.choice(self.frutas)
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

    def load_config(self):
        try:
            config_path = path.join(path.dirname(path.realpath(__file__)), 'frutas.yml')
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)

            return [] if 'frutas' not in config else config['frutas']
        except Exception as ex:
            self.log.exception(ex)
            return []
