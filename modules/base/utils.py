from discord import Embed


def is_owner(bot, member, server):
    if member.id in bot.config['bot_owners']:
        return True

    if server is None:
        return False

    if member.id in bot.config['owners']:
        return True

    for role in member.roles:
        owner_role = server.id + "@" + role.id
        if owner_role in bot.config['owners']:
            return True

    return False


def get_server_role(server, role_name):
    for role in server.roles:
        if role.name == role_name:
            return role
    return None


def img_embed(url, title=''):
    embed = Embed()
    embed.set_image(url=url)
    if title != '':
        embed.title = title
    return embed


def unserialize_avail(avails):
    s = ''
    for k, v in avails.items():
        s += v + k

    return s
