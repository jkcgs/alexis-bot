import datetime
import time

import discord
import re
from discord import Embed, Colour

from bot.regex import pat_tag, pat_usertag, pat_channel, pat_emoji, pat_colour, pat_delta_each, pat_invite

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


def auto_int(val):
    if isinstance(val, int):
        return val

    try:
        return int(val)
    except ValueError:
        return val


def compare_ids(val1, val2):
    return auto_int(val1) == auto_int(val2)


def get_guild_role(guild: discord.Guild, role, case_sensitive=True):
    """
    Creates an instance of a guild role
    :param guild: The discord.Guild instance in where the lookup will be made
    :param role: The name or ID of the role
    :param case_sensitive: Implies if the lookup will be case sensitive
    :return: The role instance, or None if it was not found
    """

    for role_ins in guild.roles:
        if (not case_sensitive and role_ins.name.lower() == role.lower()) \
                or role_ins.name == role \
                or compare_ids(role_ins.id, role):
            return role_ins

    return None


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
        return {'type': 'channel', 'id': int(text[2:-1])}

    emoji = pat_emoji.match(text)
    if emoji is not None:
        return {'type': 'emoji', 'name': emoji.group(2), 'animated': text.startswith('<a'), 'id': int(emoji.group(3))}

    user = pat_usertag.match(text)
    if user is not None:
        return {'type': 'user', 'id': int(user.group(1)), 'with_nick': text.startswith('<@!')}
    
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


def md_filter(text):
    """
    Filters Markown syntax with backslashes
    :param text:
    :return:
    """
    replacements = ['||', '*', '_']

    if text is not None:
        for o in replacements:
            text = text.replace(o, '\\' + o)

    return text


def message_link(message):
    return 'https://discordapp.com/channels/{}/{}/{}'.format(
        message.guild.id if message.guild else '@me',
        message.channel.id,
        message.id
    )


def lazy_property(fn):
    """
    Decorator that makes a property lazy-evaluated.
    Retrieved from: https://stevenloria.com/lazy-properties/ (2019-05-05)
    """
    attr_name = '_lazy_' + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazy_property
