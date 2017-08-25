from discord import Embed
import alexis
import random


class Slots():
    def __init__(self, bot):
        self.name = ['slot', 'slots']
        self.mention_handler = False
        self.help = 'Juega al Tragamonedas favorito de tu abuela'
        self.owner_only = False
        self.frutas = alexis.config['frutas']

    async def handle(self, message, cmd):
        slot1 = random.choice(self.frutas)
        slot2 = random.choice(self.frutas)
        slot3 = random.choice(self.frutas)
        if slot1 == slot2 == slot3:
            text = "¡Ganaste wn!  :confetti_ball:"
        elif slot1 == slot2 or slot1 == slot3 or slot2 == slot3:
            text = "Casi wn, casi. [2/3]"
        else:
            text = "Mala cuea. Pa' la otra será."

        embed = Embed(title="Slots by Yara Tech", color=0xf07247)
        embed.add_field(name="", value="{} tiró la palanca...".format(cmd.author_name))
        embed.add_field(name="", value="**[ {} {} {} ]**".format(slot1, slot2, slot3))
        embed.add_field(name="", value=text)
        await cmd.answer(embed=embed)