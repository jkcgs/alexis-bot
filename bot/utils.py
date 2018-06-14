import datetime
import time

import discord
import re
from os import path
from discord import Embed, Colour

from bot.libs.configuration import ServerConfiguration


pat_tag = re.compile('^<(@!?|#|a?:([a-zA-Z0-9\-_]+):)(\d{10,19})>$')
pat_usertag = re.compile('^<@!?(\d{10,19})>$')
pat_channel = re.compile('^<#(\d{10,19})>$')
pat_subreddit = re.compile('^[a-zA-Z0-9_\-]{2,25}$')
pat_emoji = re.compile('<a?(:([a-zA-Z0-9\-_]+):)([0-9]+)>')
pat_normal_emoji = re.compile('^:[a-zA-Z\-_]+:$')
pat_snowflake = re.compile('^\d{10,19}$')
pat_colour = re.compile('^#?[0-9a-fA-F]{6}$')
pat_delta = re.compile('^([0-9]+[smhd])+$')
pat_delta_each = re.compile('([0-9]+[smhd])+')

colour_list = ['default', 'teal', 'dark_teal', 'green', 'dark_green', 'blue', 'dark_blue', 'purple',
               'dark_purple', 'gold', 'dark_gold', 'orange', 'dark_orange', 'red', 'dark_red',
               'lighter_grey', 'dark_grey', 'light_grey', 'darker_grey']


def is_int(val):
    try:
        int(val)
        return True
    except (IndexError, ValueError):
        return False


def is_float(val):
    try:
        float(val)
        return True
    except (IndexError, ValueError):
        return False


def is_owner(bot, member, server):
    if server is None or not isinstance(member, discord.Member):
        return False

    if member.server_permissions.administrator:
        return True

    cfg = ServerConfiguration(bot.sv_config, server.id)

    owner_roles = cfg.get('owner_roles', bot.config['owner_role'])
    if owner_roles == '':
        owner_roles = []
    else:
        owner_roles = owner_roles.split('\n')

    for role in member.roles:
        if role.id in owner_roles \
                or role.name in owner_roles \
                or member.id in owner_roles:
            return True

    return False


def get_server_role(server, role):
    """
    Obtiene la instancia de un rol de un servidor
    :param server: La instancia de servidor en la que se buscará
    :param role: El nombre o ID del rol
    :return: La instancia del rol, o None si no ha sido encontrado
    """
    if not isinstance(server, discord.Server):
        raise RuntimeError('"server" argument must be a discord.Server instance')

    for role_ins in server.roles:
        if role_ins.name == role or role_ins.id == role:
            return role_ins

    return None


def member_has_role(member, role):
    """
    Verifica si un miembro dado tiene un rol
    :param member: El miembro de un servidor
    :param role: El nombre, ID del rol o el rol
    :return:
    """
    if not isinstance(member, discord.Member):
        raise RuntimeError('"member" argument must be a discord.Member instance')

    for member_role in member.roles:
        if isinstance(role, discord.Role) and member_role == role:
            return True
        if member_role.name == role or member_role.id == role:
            return True

    return False


def img_embed(url, title=''):
    embed = Embed()
    embed.set_image(url=url)
    if title != '':
        embed.title = title
    return embed


def text_cut(text, limit, cutter='…'):
    """
    Corta un texto y agrega un texto al final en caso de que el texto sea mayor que el tamaño límite
    :param text: El texto a cortar
    :param limit: El límite de texto
    :param cutter: El texto que se colocará al final en caso de ser cortado
    :return: El texto cortado, si corresponde, o el texto completo, si no supera el límite.
    """
    if len(text) > limit:
        return text[:limit-len(cutter)-1] + cutter
    else:
        return text


def split_list(listcont, limit, glue='\n'):
    """
    Separa una lista de items en listas más pequeñas para poder ser enviada por partes en un mensaje
    :param listcont: La lista completa de items
    :param limit: El límite de carácteres
    :param glue: El string que unirá cada elemento de la lista
    :return: Una lista de listas separadas según los parámetros entregados
    """
    chunks = []
    chunk = []
    for item in listcont:
        if len(glue.join(chunk + [item])) > limit:
            chunks.append(list(chunk))
            chunk = [item]
        else:
            chunk.append(item)

    if len(chunk) > 0:
        chunks.append(chunk)

    return chunks


def parse_tag(text):
    if not pat_tag.match(text):
        return None

    if pat_channel.match(text):
        return {'type': 'channel', 'id': text[2:-1]}

    emoji = pat_emoji.match(text)
    if emoji is not None:
        return {'type': 'emoji', 'name': emoji.group(2), 'animated': text.startswith('<a'), 'id': emoji.group(3)}

    user = pat_usertag.match(text)
    if user is not None:
        return {'type': 'user', 'id': user.group(0), 'with_nick': text.startswith('<@!')}
    
    return None


def unserialize_avail(avails):
    return '|'.join([v + k for k, v in avails.items()])


def serialize_avail(avails):
    return {c[1:]: c[0] for c in avails.split('|') if c != ''}


def deltatime_to_str(deltatime):
    result = []
    if deltatime.days > 0:
        result.append(str(deltatime.days) + ' día{}'.format('' if deltatime.days == 1 else 's'))
    m, s = divmod(deltatime.seconds, 60)
    h, m = divmod(m, 60)

    if h > 0:
        result.append(str(h) + ' hora{}'.format('' if h == 1 else 's'))
    if m > 0:
        result.append(str(m) + ' minuto{}'.format('' if m == 1 else 's'))
    if s > 0:
        result.append(str(s) + ' segundo{}'.format('' if s == 1 else 's'))

    if len(result) == 0:
        result = ['ahora']

    return ', '.join(result)


def timediff_parse(timediff):
    timediff = timediff.lower()
    ds = {'s': 0, 'm': 0, 'h': 0, 'd': 0}
    times = pat_delta_each.findall(timediff)

    for t in times:
        if t[-1] not in 'smhd':
            t += 'm'

        ds[t[-1]] += int(t[:-1])

    return datetime.timedelta(seconds=ds['s'], minutes=ds['m'], hours=ds['h'], days=ds['d'])


def format_date(date):
    offset = time.strftime('%Z')
    if len(offset) > 5:
        offset = time.strftime('%z')

    return date.strftime('%Y-%m-%d %H:%M:%S ') + offset


def destination_repr(destination):
    if getattr(destination, 'server', None) is None:
        return '{} (ID: {})'.format(str(destination), destination.id)
    else:
        return '{}#{} (IDS {}#{})'.format(destination.server, str(destination), destination.id,
                                          destination.server.id)


def replace_everywhere(content, search, replace=None):
    if isinstance(search, dict):
        for k, v in search.items():
            content = replace_everywhere(content, k, str(v))
        return content

    replace = str(replace)
    if isinstance(content, str):
        content = content.replace(search, replace)
    if isinstance(content, Embed):
        if content.title != Embed.Empty:
            content.title = content.title.replace(search, replace)
        if content.description != Embed.Empty:
            content.description = content.description.replace(search, replace)
        if content.footer.text != Embed.Empty:
            content.set_footer(text=content.footer.text.replace(search, replace), icon_url=content.footer.icon_url)

        for idx, field in enumerate(content.fields):
            content.set_field_at(idx, name=field.name.replace(search, replace),
                                 value=field.value.replace(search, replace), inline=field.inline)
    elif content is None:
        return None
    else:
        return str(content).replace(search, replace)

    return content


def get_bot_root():
    return path.abspath(path.join(path.dirname(__file__), '..'))


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


def str_to_embed(txt):
    if txt == '':
        raise RuntimeError('Invalid text to create an embed')

    subargs = txt.split('|')
    embed = Embed()

    if len(subargs) > 0 and subargs[0].strip() != '':
        embed.title = subargs[0].strip()

    if len(subargs) > 1 and subargs[1].strip() != '':
        embed.description = subargs[1].strip()

    if len(subargs) > 2 and subargs[2].strip() != '':
        embed.set_image(url=subargs[2].strip())

    if len(subargs) > 3 and subargs[3].strip() != '':
        embed_colour = get_colour(subargs[3].strip())
        if embed_colour is not None:
            embed.colour = embed_colour

    if embed.title == '' and embed.description == '' and embed.image['url'] == '':
        return None

    return embed


def get_prefix(bot, serverid=None):
    if serverid is None:
        return bot.config['command_prefix']
    else:
        svconfig = ServerConfiguration(bot.sv_config, serverid)
        return svconfig.get('command_prefix', bot.config['command_prefix'])


def no_tags(txt, bot=None, users=True, channels=True, emojis=True):
    if isinstance(txt, discord.Message):
        txt = txt.content

    if users:
        for m in pat_usertag.finditer(txt):
            if bot is None:
                txt = txt.replace(m.group(0), m.group(1))
            else:
                user = bot.get_user_info(m.group(1))
                txt.replace(m.group(0), user.display_name if user is not None else m.group(1))

    if channels:
        for m in pat_channel.finditer(txt):
            txt = txt.replace(m.group(0), m.group(1))

    if emojis:
        for m in pat_emoji.finditer(txt):
            txt = txt.replace(m.group(0), m.group(1))

    return txt
