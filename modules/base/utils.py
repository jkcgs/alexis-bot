from discord import Embed

from modules.base.database import ServerConfigMgrSingle


def is_owner(bot, member, server):
    if member.id in bot.config['bot_owners']:
        return True

    if server is None:
        return False

    cfg = ServerConfigMgrSingle(bot.sv_config, server.id)

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
