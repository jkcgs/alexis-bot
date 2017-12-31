import re
from datetime import datetime

import peewee
from discord import Embed, Colour

from alexis import Command
from alexis.base.database import BaseModel

pat_colour = re.compile('^#?[0-9a-fA-F]{6}$')
colour_list = ['default', 'teal', 'dark_teal', 'green', 'dark_green', 'blue', 'dark_blue', 'purple',
               'dark_purple', 'gold', 'dark_gold', 'orange', 'dark_orange', 'red', 'dark_red',
               'lighter_grey', 'dark_grey', 'light_grey', 'darker_grey']


def get_colour(value):
    if re.match(pat_colour, value):
        if value.startswith("#"):
            value = value[1:]
        return Colour(int(value, 16))
    else:
        embed_colour = value.lower().replace(' ', '_')
        if embed_colour in colour_list:
            return getattr(Colour, embed_colour)()
        else:
            return None


class MacroSet(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'set'
        self.help = 'Define un embed macro'
        self.owner_only = True
        self.db_models = [EmbedMacro]

    async def handle(self, message, cmd):
        argc_req = 1 if len(message.attachments) > 0 else 2
        if len(cmd.args) < argc_req:
            await cmd.answer('Formato: $PX$NM <nombre> <valor> (para macros sólo texto),\n'
                             '$PX$NM <nombre> [url_imagen]|[título]|[descripción]|[color_embed] (para macros embed)\n'
                             'Para los macros embed, el primer parámetro es ignorado si se envía una imagen adjunta '
                             'al comando.')
            return

        name = cmd.args[0]
        subargs = ' '.join(cmd.args[1:]).split('|')

        image_url = ''
        title = ''
        description = ''
        embed_colour = Colour.default()

        if len(subargs) == 1 and subargs[0] != '':
            image_url = None
            title = None
            description = ' '.join(cmd.args[1:])
        else:
            if len(message.attachments) > 0:
                for atata in message.attachments:
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

                self.log.debug('colour: %s %s', embed_colour, embed_colour.value)
            else:
                self.log.debug('no subargs>3, %s %s', len(subargs), str(subargs))

            if image_url == '' and title == '' and description == '':
                await cmd.answer('al menos la imagen, el titulo o la descripción deben ser ingresados')
                return

        server_id = 'global' if cmd.is_pm else message.server.id
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
        self.owner_only = True

    async def handle(self, message, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('Formato: $PX$NM <nombre>')
            return

        name = cmd.args[0].replace('\\', '')
        server_id = 'global' if cmd.is_pm else message.server.id
        try:
            EmbedMacro.get(name=name, server=server_id)
            q = EmbedMacro.delete().where(EmbedMacro.name == name, EmbedMacro.server == server_id)
            q.execute()
            await cmd.answer('macro **{}** eliminado'.format(name))
        except EmbedMacro.DoesNotExist:
            await cmd.answer('el macro **{}** no existe'.format(name))
            pass


class MacroSetColour(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'setcolour'
        self.aliases = ['setcolor']
        self.help = 'Actualiza el color de un macro embed'
        self.owner_only = True

    async def handle(self, message, cmd):
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
        server_id = 'global' if cmd.is_pm else message.server.id
        try:
            macro = EmbedMacro.get(name=name, server=server_id)
            macro.embed_color = colour.value
            macro.save()
            await cmd.answer('color de macro **{}** actualizado'.format(name))
        except EmbedMacro.DoesNotExist:
            await cmd.answer('el macro **{}** no existe'.format(name))
            pass


class MacroList(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'list'
        self.help = 'Muestra una lista de los nombres de los macros guardados'
        self.rx_mention = re.compile('^<@!?[0-9]+>$')
        self.allow_pm = False

    async def handle(self, message, cmd):
        await cmd.typing()
        namelist = []

        items = EmbedMacro.select().where(EmbedMacro.server == message.server.id)
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
        resp = 'hay {} macro{}:'.format(len(namelist), '' if len(namelist) == 1 else 's')
        for i, name in enumerate(namelist):
            if len(resp + ', ' + name) > 2000:
                await cmd.answer(resp)
                resp = name
            else:
                resp += (' ' if i == 0 else ', ') + name

        if resp != '':
            await cmd.answer(resp.strip())


"""
class MacroSuperList(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = bot.config['command_prefix'] + 'list'
        self.help = 'Muestra una lista completa de los macros con sus valores'
        self.owner_only = True
        self.rx_mention = re.compile('^<@!?[0-9]+>$')
        self.rx_blob = re.compile('^<:[a-zA-Z\-_]+:[0-9]+>$')

    async def handle(self, message, cmd):
        memelist = []
        for item in Meme.select().iterator():
            if re.match(self.rx_mention, item.name):
                name = item.name.replace('!', '')
                member_id = name[2:-1]
                member = cmd.member_by_id(member_id)
                name = '@' + member.display_name
            elif re.match(self.rx_blob, item.name):
                name = ':{}:'.format(item.name.split(':')[1])
            else:
                name = item.name
            memelist.append("- {}: {}".format(name, item.content))

        num_memes = len(memelist)
        if num_memes == 0:
            await cmd.answer('no hay macros disponibles')
            return

        resp = 'hay {} {}:'.format(num_memes, ['macros', 'macro'][int(num_memes == 1)])
        await cmd.answer(resp)

        # Separar lista de memes en mensajes con menos de 2000 carácteres
        resp_list = ''
        for meme in memelist:
            if len('```{}\n{}```'.format(resp_list, meme)) > 2000:
                await cmd.answer('```{}```'.format(resp_list))
                resp_list = ''
            else:
                resp_list = '{}\n{}'.format(resp_list, meme)

        # Enviar lista restante
        if resp_list != '':
            await cmd.answer('```{}```'.format(resp_list))
"""


class MacroUse(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.swhandler = ['$PX ', '$PX', '¡']
        self.swhandler_break = True

    async def handle(self, message, cmd):
        # Actualizar el id de la última persona que usó el comando, omitiendo al mismo bot
        if self.bot.last_author is None or not cmd.own:
            self.bot.last_author = message.author.id

        pfx = self.bot.config['command_prefix']
        macro_name = cmd.args[0] if message.content.startswith(pfx + ' ') else message.content[1:].split(' ')[0]

        # Usar un macro embed si existe
        try:
            server_id = 'global' if cmd.is_pm else message.server.id
            macro = EmbedMacro.get(EmbedMacro.name == macro_name, EmbedMacro.server == server_id)
            macro.used_count += 1
            macro.save()

            if macro.image_url is None and macro.title is None:
                await cmd.answer(macro.description)
            else:
                embed = Embed()
                if macro.image_url != '':
                    embed.set_image(url=macro.image_url)
                if macro.title != '':
                    embed.title = macro.title
                if macro.description != '':
                    embed.description = macro.description

                embed.colour = macro.embed_color
                await cmd.answer(embed=embed)
        except EmbedMacro.DoesNotExist:
            pass


class EmbedMacro(BaseModel):
    name = peewee.TextField()
    server = peewee.TextField()
    image_url = peewee.TextField(null=True)
    title = peewee.TextField(null=True)
    description = peewee.TextField(null=True)
    embed_color = peewee.IntegerField(default=Colour.default().value)
    created = peewee.DateTimeField(default=datetime.now)
    used_count = peewee.IntegerField(default=0, null=False)
