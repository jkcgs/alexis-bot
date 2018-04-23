import re
from datetime import datetime

import peewee
from discord import Embed, Colour

from bot import Command
from bot.utils import is_int, get_colour, format_date
from bot.libs.configuration import BaseModel


class MacroSet(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'set'
        self.help = 'Define un embed macro'
        self.db_models = [EmbedMacro]

    async def handle(self, cmd):
        if not cmd.is_pm and not cmd.owner:
            return

        if cmd.is_pm and not cmd.bot_owner:
            return

        argc_req = 1 if len(cmd.message.attachments) > 0 else 2
        if len(cmd.args) < argc_req:
            await cmd.answer('formato: $PX$NM <nombre> <valor> (para macros sólo texto),\n'
                             '$PX$NM <nombre> [url_imagen]|[título]|[descripción]|[color_embed] (para macros embed)\n'
                             'Para los macros embed, el primer parámetro es ignorado si se envía una imagen adjunta '
                             'al comando. Para agregar un macro embed sólo con url, agrega un pipe (|) al final. '
                             'Ejemplo: `$PX$NM <nombre> <url> |`')
            return

        name = cmd.args[0]
        subargs = ' '.join(cmd.args[1:]).split('|')

        image_url = ''
        title = ''
        description = ''
        embed_colour = Colour.default()

        if name in self.bot.manager:
            await cmd.answer('no se puede crear un macro con el nombre de un comando')
            return

        if len(name) > 100:
            await cmd.answer('el nombre del macro puede tener hasta 100 carácteres')
            return

        if len(subargs) == 1 and subargs[0] != '':
            image_url = None
            title = None
            description = ' '.join(cmd.args[1:])
        else:
            if len(cmd.message.attachments) > 0:
                for atata in cmd.message.attachments:
                    if atata['url'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        subargs[0] = atata['url']
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
                    await cmd.answer('Color inválido')
                    return

            if image_url == '' and title == '' and description == '':
                await cmd.answer('al menos la imagen, el titulo o la descripción deben ser ingresados')
                return

        server_id = 'global' if cmd.is_pm else cmd.message.server.id
        macro, created = EmbedMacro.get_or_create(name=name, server=server_id)
        macro.image_url = image_url
        macro.title = title
        macro.description = description
        macro.embed_color = embed_colour.value
        macro.save()

        if created:
            await cmd.answer('macro **{}** creado'.format(name))
        else:
            await cmd.answer('macro **{}** actualizado'.format(name))


class MacroUnset(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'unset'
        self.help = 'Elimina un macro'

    async def handle(self, cmd):
        if not cmd.is_pm and not cmd.owner:
            return

        if cmd.is_pm and not cmd.bot_owner:
            return

        if len(cmd.args) < 1:
            await cmd.answer('formato: $PX$NM <nombre>')
            return

        name = cmd.args[0].replace('\\', '')
        server_id = 'global' if cmd.is_pm else cmd.message.server.id
        try:
            EmbedMacro.get(name=name, server=server_id)
            q = EmbedMacro.delete().where(EmbedMacro.name == name, EmbedMacro.server == server_id)
            q.execute()
            await cmd.answer('macro **{}** eliminado'.format(name))
        except EmbedMacro.DoesNotExist:
            await cmd.answer('el macro **{}** no existe'.format(name))


class MacroRename(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'rename'
        self.help = 'Renombra un macro'

    async def handle(self, cmd):
        if not cmd.is_pm and not cmd.owner:
            return

        if cmd.is_pm and not cmd.bot_owner:
            return

        if cmd.argc != 2:
            await cmd.answer('formato: $PX$NM <nombre> <nuevo_nombre>')
            return

        if cmd.args[1] in self.bot.manager:
            await cmd.answer('no se puede nombrar un macro con el nombre de un comando')
            return

        if len(cmd.args[1]) > 100:
            await cmd.answer('el nombre del macro no puede tener más de 100 carácteres')

        serverid = 'global' if cmd.is_pm else cmd.message.server.id
        try:
            other = EmbedMacro.select().where(EmbedMacro.name == cmd.args[1], EmbedMacro.server == serverid)
            if other.count() > 0:
                await cmd.answer('ya existe un macro con el nuevo nombre')
                return

            macro = EmbedMacro.get(EmbedMacro.name == cmd.args[0], EmbedMacro.server == serverid)
            macro.name = cmd.args[1]
            macro.save()
            await cmd.answer('macro renombrado')
        except EmbedMacro.DoesNotExist:
            await cmd.answer('ese macro no existe')


class MacroSetColour(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'setcolour'
        self.aliases = ['setcolor']
        self.help = 'Actualiza el color de un macro embed'

    async def handle(self, cmd):
        if not cmd.is_pm and not cmd.owner:
            return

        if cmd.is_pm and not cmd.bot_owner:
            return

        if len(cmd.args) < 1:
            await cmd.answer('formato: $PX$NM <nombre> <color=default>')
            return

        colour = Colour.default()
        if len(cmd.args) > 1:
            colour = get_colour(' '.join(cmd.args[1:]))
            if colour is None:
                await cmd.answer('color inválido')
                return

        name = cmd.args[0].replace('\\', '')
        server_id = 'global' if cmd.is_pm else cmd.message.server.id
        try:
            macro = EmbedMacro.get(name=name, server=server_id)
            macro.embed_color = colour.value
            macro.save()
            await cmd.answer('color de macro **{}** actualizado'.format(name))
        except EmbedMacro.DoesNotExist:
            await cmd.answer('el macro **{}** no existe'.format(name))


class MacroList(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'list'
        self.help = 'Muestra una lista de los nombres de los macros guardados'
        self.rx_mention = re.compile('^<@!?[0-9]+>$')

    async def handle(self, cmd):
        await cmd.typing()
        namelist = []

        if cmd.is_pm:
            items = EmbedMacro.select().where(EmbedMacro.server == 'global')
        else:
            items = EmbedMacro.select().where(
                EmbedMacro.server << [cmd.message.server.id, 'global'])

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
        resp = '{}, hay {} macro{}:'.format(cmd.author_name, n_items, ['s', ''][int(n_items == 1)])
        for i, name in enumerate(namelist):
            to_add = (' ' if i == 0 else ', ') + name

            if len(resp + to_add) > 2000:
                await cmd.answer(resp, withname=False)
                resp = name
            else:
                resp += to_add

        if resp != '':
            await cmd.answer(resp.strip(), withname=False)


class MacroUse(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.swhandler = ['$PX ', '$PX', '¡']
        self.swhandler_break = True

    async def handle(self, cmd):
        # Actualizar el id de la última persona que usó el comando, omitiendo al mismo bot
        if self.bot.last_author is None or not cmd.self:
            self.bot.last_author = cmd.author.id

        # Obtener los argumentos del macro
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

        # Usar un macro embed si existe
        try:
            server_id = 'global' if cmd.is_pm else cmd.message.server.id
            macro = EmbedMacro.get(EmbedMacro.name == macro_name, EmbedMacro.server << [server_id, 'global'])
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


class MacroRank(Command):
    __version__ = '1.0.0'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'macrorank'
        self.help = 'Muestra un ranking de los macros usados en el servidor actual'
        self.allow_pm = False

    async def handle(self, cmd):
        sortage = 'asc' if cmd.argc == 1 and cmd.args[0] in ['inv', 'inverse'] else 'desc'
        result = EmbedMacro.select().where(EmbedMacro.server == cmd.server.id).order_by(
            getattr(EmbedMacro.used_count, sortage)()).limit(10)

        if len(result) == 0:
            await cmd.answer('no se encontraron macros')
            return

        result = ['- {} ({}, creado: {})'.format(r.name, r.used_count, format_date(r.created)) for r in result]

        await cmd.answer('```{}```'.format('\n'.join(result)))


def safe_format(strp, args):
    """
    Agrega placeholders a un macro que tiene placeholders, pero que no se le pasaron los suficientes
    :param strp: El string del macro
    :param args: Los parámetros del macro
    :return: El string formateado según los argumentos
    """

    # Encontrar los placeholders numéricos
    t = [int(i) for i in re.findall(r"{(\w+)}", strp) if is_int(i)]

    if len(t) > 0:
        t = max(t) + 1
        if len(args) < t:
            # Agregar los placeholders a la lista de argumentos
            args += [('{' + str(j) + '}') for j in range(len(args), t - len(args) + 1)]

        print('result:', args)

    # Formatear el string según la nueva lista de argumentos
    return strp.format(*args)


class EmbedMacro(BaseModel):
    name = peewee.TextField()
    server = peewee.TextField()
    image_url = peewee.TextField(null=True)
    title = peewee.TextField(null=True)
    description = peewee.TextField(null=True)
    embed_color = peewee.IntegerField(default=Colour.default().value)
    created = peewee.DateTimeField(default=datetime.now)
    used_count = peewee.IntegerField(default=0, null=False)
