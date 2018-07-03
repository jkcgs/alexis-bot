from discord import Embed

from bot import Command
from bot.utils import split_list
from bot import categories


class Help(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'help'
        self.aliases = ['ayuda']
        self.help = '$[help-help]'
        self.format = '$[help-usage]'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        if cmd.argc > 0:
            ins = self.bot.manager.get_cmd(cmd.args[0])
            if ins is None or (ins.owner_only and not cmd.owner) or (ins.bot_owner_only and not cmd.bot_owner):
                await cmd.answer('comando no disponible')
            else:
                embed = Embed(title='$PXhelp', description=ins.help)
                embed.add_field(name='$[help-format-title]', value=ins.format, inline=False)
                embed.set_footer(text='$[help-footer-for]')
                await cmd.answer(embed, withname=False)

            return

        commands = {}
        for k in self.bot.manager.cmds.keys():
            ins = self.bot.manager[k]

            if ins.owner_only and not cmd.owner or ins.bot_owner_only and not cmd.bot_owner:
                continue

            if ins.category not in commands:
                commands[ins.category] = []

            suffix = ''
            if ins.owner_only:
                suffix = '*'
            if ins.bot_owner_only:
                suffix = '**'

            commands[ins.category].append(k + suffix)

        embed = Embed(title='$[help-title]')
        embed.description = '$[help-description]'
        if cmd.owner:
            embed.description += ' $[help-description-owner]'

        for k in categories.names:
            if k not in commands or len(commands[k]) < 1:
                continue

            commands[k].sort()
            lists = split_list(commands[k], 1000, ', ')
            name = '$[help-category-{}]'
            for i, cmd_list in enumerate(lists):
                name_l = name
                if len(lists) > 1:
                    name_l = name + " {}/{}".format(i+1, len(lists))

                content = '```{}```'.format(', '.join(cmd_list))
                if i == 0:
                    content = '$[help-category-{}-description]'.format(k) + content
                embed.add_field(name=name_l.format(k), value=content, inline=False)

        await cmd.answer(embed)
