import re
from datetime import datetime

import peewee
from discord import Embed, Colour

from bot import Command, categories, BaseModel
from bot.utils import is_int, get_colour, format_date, colour_list


class EmbedMacro(BaseModel):
    name = peewee.TextField()
    server = peewee.TextField()
    image_url = peewee.TextField(null=True)
    title = peewee.TextField(null=True)
    description = peewee.TextField(null=True)
    embed_color = peewee.IntegerField(default=Colour.default().value)
    created = peewee.DateTimeField(default=datetime.now)
    used_count = peewee.IntegerField(default=0, null=False)


class MacroSet(Command):
    db_models = [EmbedMacro]

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'set'
        self.help = '$[macros-help]'
        self.category = categories.STAFF

    async def handle(self, cmd):
        if not cmd.is_pm and not cmd.owner:
            return

        if cmd.is_pm and not cmd.bot_owner:
            return

        argc_req = 1 if len(cmd.message.attachments) > 0 else 2
        if len(cmd.args) < argc_req:
            await cmd.answer('$[format]: $[macros-format]')
            return

        name = cmd.args[0]
        subargs = ' '.join(cmd.args[1:]).split('|')

        image_url = ''
        title = ''
        description = ''
        embed_colour = Colour.default()

        if name in self.bot.manager:
            await cmd.answer('$[macros-err-cmd-name]')
            return

        if len(name) > 100:
            await cmd.answer('$[macros-err-name-length]')
            return

        if len(subargs) == 1 and subargs[0] != '':
            image_url = None
            title = None
            description = ' '.join(cmd.args[1:])
        else:
            if len(cmd.message.attachments) > 0:
                for atata in cmd.message.attachments:
                    if atata.url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        subargs[0] = atata.url
                        break

            if subargs[0].strip() != '':
                image_url = subargs[0].strip()

            if len(subargs) > 1 and subargs[1].strip() != '':
                title = subargs[1].strip()

            if len(subargs) > 2 and subargs[2].strip() != '':
                description = subargs[2].strip()

            if len(subargs) > 3 and subargs[3].strip() != '':
                embed_colour = get_colour(subargs[3].strip())
                if embed_colour is None:
                    await cmd.answer('$[macros-invalid-colour]')
                    return

            if image_url == '' and title == '' and description == '':
                await cmd.answer('$[macros-missing-fields]')
                return

        guild = 'global' if cmd.is_pm else cmd.message.guild.id
        macro, created = EmbedMacro.get_or_create(name=name, server=guild)
        macro.image_url = image_url
        macro.title = title
        macro.description = description
        macro.embed_color = embed_colour.value
        macro.save()

        if created:
            await cmd.answer('$[macros-created]', locales={'macro_name': name})
        else:
            await cmd.answer('$[macros-updated]', locales={'macro_name': name})


class MacroUnset(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'unset'
        self.help = '$[macros-unset-help]'
        self.format = '$[macros-unset-format]'
        self.category = categories.STAFF

    async def handle(self, cmd):
        if not cmd.is_pm and not cmd.owner:
            return

        if cmd.is_pm and not cmd.bot_owner:
            return

        if len(cmd.args) < 1:
            await cmd.answer('$[format]: $[macros-unset-format]')
            return

        name = cmd.args[0].replace('\\', '')
        server_id = 'global' if cmd.is_pm else cmd.guild.id
        try:
            EmbedMacro.get(name=name, server=server_id)
            q = EmbedMacro.delete().where(EmbedMacro.name == name, EmbedMacro.server == server_id)
            q.execute()
            await cmd.answer('$[macros-deleted]', locales={'macro_name': name})
        except EmbedMacro.DoesNotExist:
            await cmd.answer('$[macros-not-exists]', locales={'macro_name': name})


class MacroRename(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'rename'
        self.help = '$[macros-rename-help]'
        self.format = '$[macros-rename-format]'
        self.category = categories.STAFF

    async def handle(self, cmd):
        if not cmd.is_pm and not cmd.owner:
            return

        if cmd.is_pm and not cmd.bot_owner:
            return

        if cmd.argc != 2:
            await cmd.answer('$[format]: $[macros-rename-format]')
            return

        if cmd.args[1] in self.bot.manager:
            await cmd.answer('$[macros-err-rename-cmd]')
            return

        if len(cmd.args[1]) > 100:
            await cmd.answer('$[macros-err-name-length]')

        serverid = 'global' if cmd.is_pm else cmd.message.guild.id
        try:
            other = EmbedMacro.select().where(EmbedMacro.name == cmd.args[1], EmbedMacro.server == serverid)
            if other.count() > 0:
                await cmd.answer('$[macros-err-rename-exists]')
                return

            macro = EmbedMacro.get(EmbedMacro.name == cmd.args[0], EmbedMacro.server == serverid)
            macro.name = cmd.args[1]
            macro.save()
            await cmd.answer('$[macros-renamed]')
        except EmbedMacro.DoesNotExist:
            await cmd.answer('$[macros-not-exists]', locales={'macro_name': cmd.args[0]})


class MacroSetColour(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'setcolour'
        self.aliases = ['setcolor']
        self.help = '$[macros-setcolour-help]'
        self.format = '$[macros-setcolour-format]'
        self.category = categories.STAFF

    async def handle(self, cmd):
        if not cmd.is_pm and not cmd.owner:
            return

        if cmd.is_pm and not cmd.bot_owner:
            return

        if len(cmd.args) < 1:
            await cmd.answer('$[format]: $[macros-setcolour-format] $[macros-setcolour-format-ext]', locales={
                'colours_list': ', '.join(colour_list)
            })
            return

        colour = Colour.default()
        if len(cmd.args) > 1:
            colour = get_colour(' '.join(cmd.args[1:]))
            if colour is None:
                await cmd.answer('$[macros-invalid-colour]')
                return

        name = cmd.args[0].replace('\\', '')
        guild = 'global' if cmd.is_pm else cmd.message.guild.id
        try:
            macro = EmbedMacro.get(name=name, server=guild)
            macro.embed_color = colour.value
            macro.save()
            await cmd.answer('$[macros-colour-updated]', locales={'macro_name': name})
        except EmbedMacro.DoesNotExist:
            await cmd.answer('$[macros-not-exists]', locales={'macro_name': name})


class MacroList(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'list'
        self.help = '$[macros-list-help]'
        self.rx_mention = re.compile('^<@!?[0-9]+>$')
        self.category = categories.UTILITY

    async def handle(self, cmd):
        await cmd.typing()
        namelist = []

        if cmd.is_pm:
            items = EmbedMacro.select().where(EmbedMacro.server == 'global')
        else:
            items = EmbedMacro.select().where(
                EmbedMacro.server << [cmd.message.guild.id, 'global'])

        for item in items:
            if re.match(self.rx_mention, item.name):
                name = item.name.replace('!', '')
                member_id = name[2:-1]
                member = cmd.member_by_id(member_id)
                name = '*\\@{}*'.format('<@{}>'.format(member_id) if member is None else member.display_name)
            else:
                name = item.name

            if name not in namelist:
                namelist.append(name)

        namelist.sort()
        n_items = len(namelist)
        if n_items == 0:
            await cmd.answer('$[macros-none-found]')
            return

        resp = ['$[macros-list]', '$[macros-list-singular]'][n_items == 1]
        for i, name in enumerate(namelist):
            to_add = (' ' if i == 0 else ', ') + name

            if len(resp + to_add) > 1997:
                await cmd.answer(resp, locales={'macros_count': n_items})
                resp = name
            else:
                resp += to_add

        if resp != '':
            await cmd.answer(resp.strip(), locales={'macros_count': n_items})


class MacroUse(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.swhandler = ['$PX ', '$PX', '¡']
        self.swhandler_break = True

    async def handle(self, cmd):
        # Update the last user who used the macro
        if self.bot.last_author is None or not cmd.self:
            self.bot.last_author = cmd.author.id

        # Get macro arguments
        pfx = self.bot.config['command_prefix']
        if cmd.message.content.startswith(pfx + ' '):
            macro_name = cmd.args[0]
            macro_args = (' '.join(cmd.args[1:])).split('|')
        else:
            args = cmd.message.content[1:].split(' ')
            macro_name = args[0]
            macro_args = (' '.join(args[1:])).split('|')

        if len(macro_args) == 1 and macro_args[0] == '':
            macro_args = []

        # Use an embed macro, if it exists
        try:
            guild_id = 'global' if cmd.is_pm else cmd.message.guild.id
            macro = EmbedMacro.get(EmbedMacro.name == macro_name, EmbedMacro.server << [guild_id, 'global'])
            macro.used_count += 1
            macro.save()

            if macro.image_url is None and macro.title is None:
                await cmd.answer(safe_format(macro.description, macro_args))
            else:
                embed = Embed()
                if macro.image_url != '':
                    embed.set_image(url=macro.image_url)
                if macro.title != '':
                    embed.title = safe_format(macro.title, macro_args)
                if macro.description != '':
                    embed.description = safe_format(macro.description, macro_args)

                embed.colour = macro.embed_color
                await cmd.answer(embed=embed)
        except EmbedMacro.DoesNotExist:
            pass


class MacroSearch(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'macrosearch'
        self.aliases = ['macrofind']
        self.help = '$[macro-search-help]'
        self.allow_pm = False
        self.category = categories.UTILITY

    async def handle(self, cmd):
        if cmd.argc < 1:
            await cmd.answer('$[format]: $[macro-search-format]')
            return

        if len(cmd.args[0]) < 2:
            await cmd.answer('$[macro-search-err-len]')
            return

        result = EmbedMacro.select().where(
            EmbedMacro.server == cmd.guild.id and EmbedMacro.name.contains(cmd.args[0])
        ).limit(21)

        n_results = result.count()
        names = ', '.join([m.name for m in list(result)[:20]])

        if n_results > 20:
            await cmd.answer('$[macro-search-result-more]', locales={'results': names})
        elif n_results == 1:
            await cmd.answer('$[macro-search-result-single]', locales={'results': names})
        else:
            await cmd.answer('$[macro-search-result]', locales={
                'num_results': n_results, 'results': names
            })


class MacroRank(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'macrorank'
        self.help = '$[macros-rank-help]'
        self.allow_pm = False
        self.category = categories.UTILITY

    async def handle(self, cmd):
        sortage = 'asc' if cmd.argc == 1 and cmd.args[0] in ['inv', 'inverse'] else 'desc'
        result = EmbedMacro.select().where(EmbedMacro.server == cmd.guild.id).order_by(
            getattr(EmbedMacro.used_count, sortage)()).limit(10)

        if len(result) == 0:
            await cmd.answer('$[macros-none-found]')
            return

        result = ['- {} ({}, $[macros-rank-created]: {})'.format(
            r.name, r.used_count, format_date(r.created)) for r in result]

        await cmd.answer('```{}```'.format('\n'.join(result)))


def safe_format(strp, args):
    """
    Adds placeholders to a macro that had not enough arguments passed
    :param strp: The macro string
    :param args: Macro parameters
    :return: The formatted strings
    """

    # Find numeric placeholders
    t = [int(i) for i in re.findall(r"{(\w+)}", strp) if is_int(i)]

    if len(t) > 0:
        t = max(t) + 1
        if len(args) < t:
            # Add placeholders to the arguments list
            args += [('{' + str(j) + '}') for j in range(len(args), t - len(args) + 1)]

    # Format the string with the new arguments list
    return strp.format(*args)
