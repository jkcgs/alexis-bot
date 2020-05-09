import discord
from discord import Embed

from bot import Command
from bot.utils import split_list
from bot import categories


class Help(Command):
    __author__ = 'makzk'
    __version__ = '1.0.1'

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
                await cmd.answer('$[command-not-available]')
            else:
                lang = self.get_lang(cmd.guild, cmd.channel)
                format_cont = lang.format(ins.format).replace('$CMD', '$PX$NM')
                format_cont = format_cont.replace('$NM', cmd.args[0])
                embed = Embed(title='$PX' + cmd.args[0], description=ins.help)
                embed.add_field(name='$[help-format-title]', value=format_cont, inline=False)
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
        embed.set_footer(text='$[help-footer-for]')
        embed.description = '$[help-description]'
        if cmd.owner:
            embed.description += ' $[help-description-owner]'

        cat_values = [getattr(categories, val) for val in dir(categories) if not val.startswith('__')]
        for k in cat_values:
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

        if not cmd.is_pm:
            await cmd.answer('$[help-via-pm]')

        try:
            await cmd.answer(embed, to_author=True)
        except discord.errors.Forbidden:
            await cmd.answer('$[help-via-pm-failed]')
