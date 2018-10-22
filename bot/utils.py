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
pat_invite = re.compile('(?:https?://)?(discord(?:app\.com/invite|.gg)/[a-zA-Z0-9]+)')

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


def get_server_role(server, role, case_sensitive=True):
    """
    Creates an instance of a server role
    :param server: The discord.Server instance in where the lookup will be made
    :param role: The name or ID of the role
    :param case_sensitive: Implies if the lookup will be case sensitive
    :return: The role instance, or None if it was not found
    """
    if not isinstance(server, discord.Server):
        raise RuntimeError('"server" argument must be a discord.Server instance')

    for role_ins in server.roles:
        if (not case_sensitive and role_ins.name.lower() == role.lower()) \
                or role_ins.name == role or role_ins.id == role:
            return role_ins

    return None


def member_has_role(member, role):
    """
    Verifies if a guild member has a role
    :param member: The guild member, discord.Member instance
    :param role: The name, ID or instanced (discord.Role) role
    :return: A boolean value, given the result of the operation
    """
    if not isinstance(member, discord.Member):
        raise RuntimeError('"member" argument must be a discord.Member instance')

    for member_role in member.roles:
        if isinstance(role, discord.Role) and member_role == role:
            return True
        if member_role.name == role or member_role.id == role:
            return True

    return False


def img_embed(url, title='', description='', footer=''):
    embed = Embed()
    embed.set_image(url=url)

    if title:
        embed.title = title

    if description:
        embed.description = description

    if footer:
        embed.set_footer(text=footer)

    return embed


def text_cut(text, limit, cutter='…'):
    """
    Text ellipsis
    :param text: The text to be cutted
    :param limit: The text limit (the ellipsis character(s) are counted in this limit)
    :param cutter: The suffix to add at the end of the cutted text.
    :return: The cutted text, or the full text if it's shorter than the given limit.
    """
    if len(text) > limit:
        return text[:limit-len(cutter)-1] + cutter
    else:
        return text


def split_list(listcont, limit, glue='\n'):
    """
    Splits a list of items in chunks to be sent in messages
    :param listcont: The item list
    :param limit: The character limit
    :param glue: The string that will join every list item
    :return: A list of strings with the items joined given the glue parameter
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
    """
    Creates a dict object with parameters, given a Discord tag (users, channels, custom emojis).
    :param text: The tag text
    :return: The dict object with items, all of them will have the 'type' property (possible values: channel,
    emoji and user). Values for channel: id. Values for emoji: name, animated (bool), id. Values for user:
    id, with_nick (bool).
    """
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
    """
    Creates a relative string from a deltatime object. For example, "1 day, 3 hours".
    :param deltatime: The deltatime object.
    :return: The generated string from the deltatime.
    """
    result = []
    if deltatime.days > 0:
        result.append(str(deltatime.days) + ' $[day{}]'.format('' if deltatime.days == 1 else 's'))
    m, s = divmod(deltatime.seconds, 60)
    h, m = divmod(m, 60)

    if h > 0:
        result.append(str(h) + ' $[hour{}]'.format('' if h == 1 else 's'))
    if m > 0:
        result.append(str(m) + ' $[minute{}]'.format('' if m == 1 else 's'))
    if s > 0:
        result.append(str(s) + ' $[second{}]'.format('' if s == 1 else 's'))

    if len(result) == 0:
        result = ['$[now]']

    return ', '.join(result)


def deltatime_to_str_short(deltatime):
    """
    Creates a relative string from a deltatime object. For example, "1d3h", for 1 day and 3 hours.
    :param deltatime: The deltatime object.
    :return: The generated string from the deltatime.
    """
    result = []
    if deltatime.days > 0:
        result.append(str(deltatime.days) + 'd')
    m, s = divmod(deltatime.seconds, 60)
    h, m = divmod(m, 60)

    if h > 0:
        result.append(str(h) + 'h')
    if m > 0:
        result.append(str(m) + 'm')
    if s > 0:
        result.append(str(s) + 's')

    if len(result) == 0:
        result = ['$[now]']

    return ''.join(result)


def deltatime_to_time(deltatime):
    """
    Creates a time string from a deltatime object. For example, "1d 3:30:01", for 1 day and 3 hours.
    :param deltatime: The deltatime object.
    :return: The generated string from the deltatime.
    """
    result = []
    if deltatime.days > 0:
        result.append(str(deltatime.days) + 'd ')
    m, s = divmod(deltatime.seconds, 60)
    h, m = divmod(m, 60)

    result.append(str(h).zfill(2))
    result.append(':' + str(m).zfill(2))
    result.append(':' + str(s).zfill(2))

    return ''.join(result)


def timediff_parse(timediff):
    """
    Creates a deltatime from a deltatime_to_str_short format result. For example, "1d3h" creates a 1 day and 3 hours
    deltatime object. Time items can be repeated and don't need to be in a specific order.
    :param timediff: The timediff string.
    :return: The resulting deltatime object.
    """
    timediff = timediff.lower()
    ds = {'s': 0, 'm': 0, 'h': 0, 'd': 0}
    times = pat_delta_each.findall(timediff)

    for t in times:
        if t[-1] not in 'smhd':
            t += 'm'

        ds[t[-1]] += int(t[:-1])

    return datetime.timedelta(seconds=ds['s'], minutes=ds['m'], hours=ds['h'], days=ds['d'])


def format_date(date):
    """
    Creates a date string given a date object, in the format YYYY-mm-dd HH:MM:SS [offset].
    The offset will normally be in the -NNNN format (e.g., -0300).
    :param date: The date object
    :return: The generated string for the date object.
    """
    offset = time.strftime('%Z')
    if len(offset) > 5:
        offset = time.strftime('%z')

    return date.strftime('%Y-%m-%d %H:%M:%S ') + offset


def destination_repr(destination):
    """
    Creates a string based on a message destination (e.g., a guild, a user).
    :param destination: The destination object
    :return: The generated string.
    """
    if getattr(destination, 'server', None) is None:
        return '{} (ID: {})'.format(str(destination), destination.id)
    else:
        return '{}#{} (IDS {}#{})'.format(destination.server, str(destination), destination.id,
                                          destination.server.id)


def replace_everywhere(content, search, replace=None):
    """
    Replaces a string everywhere in a string or a discord.Embed instance (i.e., title, description, fields, footer)
    :param content: The string or discord.Embed instance. If none of them, it will be str()'d.
    :param search: The string to search.
    :param replace: The string to replace matches.
    :return: If a discord.Embed instance is given, it will modify its attributes, so it's not necessary to recover this
    method's result. In any case, it will return the modified content parameter.
    """
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
    """
    Generates the absolute bot path in the system.
    :return: A string containing the absolute bot path in the system.
    """
    return path.abspath(path.join(path.dirname(__file__), '..'))


def get_colour(value):
    """
    Creates a discord.Colour instance given a colour string.
    :param value: A #RRGGBB string colour or a discord.Colour.embed_colour name.
    :return: A discord.Colour instance.
    """
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
    """
    Given a string in a certain format, creates a discord.Embed instance.
    :param (str) txt: The string in the format: `title | description | image_url | embed_colour`.
    To omit a parameter, add another pipe, or don't append it. For example, `title | | image_url`.
    At least the title, description or the image url must be passed.
    :return: A discord.Embed instance.
    """
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
    """
    Looks up for the command prefix for a guild.
    :param bot: The bot instance.
    :param serverid: The guild ID string.
    :return: The command prefix. If the serverid parameter is none, the default prefix will be returned.
    """
    if serverid is None:
        return bot.config['command_prefix']
    else:
        svconfig = ServerConfiguration(bot.sv_config, serverid)
        return svconfig.get('command_prefix', bot.config['command_prefix'])


def no_tags(txt, bot=None, users=True, channels=True, emojis=True):
    """
    Removes all the tags from a string, and replaces them with a verbose string that doesn't trigger tags.
    :param txt: The string to format.
    :param bot: The bot instance. If none, it won't be able to get server member nicks.
    :param users: A boolean to determine if users will be processed. Only the user ID will be left.
    :param channels: A boolean to determine if channels will be processed. Only the channel ID will be left.
    :param emojis: A boolean to determine if emojis will be processed. Only the emoji name will be left.
    :return: The formatted string.
    """
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


def invite_filter(text):
    """
    Filters any Discord invitation link found on a string
    :param text: The text to filter
    :return: The filtered text
    """
    for match in pat_invite.finditer(text):
        text = text.replace(match.group(0), '$[invite-filtered]')

    return text
