import math
from discord import Embed

from bot import Command, AlexisBot
from bot.utils import text_cut


class Help(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'help'
        self.aliases = ['ayuda']
        self.help = 'Muestra la lista de comandos y su ayuda'

    async def handle(self, cmd):
        cmds_verif = []
        fields = []

        for i in self.bot.manager.cmds.keys():
            ins = self.bot.manager[i]
            if ins.owner_only and not cmd.owner:
                continue
            if ins.bot_owner_only and not cmd.bot_owner:
                continue

            cmds = (' ' + cmd.prefix).join([ins.name] + ins.aliases)
            if cmds not in cmds_verif:
                cmds_verif.append(cmds)
                fields.append((cmd.prefix + cmds, ins.help))

        if len(cmds_verif) == 0:
            await cmd.answer('no hay comandos disponibles')
            return

        if not cmd.is_pm:
            await cmd.answer('te enviaré la info por PM!')

        pages = math.ceil(len(fields) / 25)
        current = 0
        for i in range(0, len(fields), 25):
            fields_chunk = fields[i:i+25]
            current += 1
            embed = Embed(title='Comandos de {} ({}/{})'.format(
                AlexisBot.name,
                current, pages
            ))
            for field in fields_chunk:
                name, value = field
                embed.add_field(name=text_cut(name, 256), value=text_cut(value, 1024), inline=False)

            await cmd.answer(embed, to_author=True, withname=False)
