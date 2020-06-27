import discord

from bot import Command, categories
from bot.utils import get_guild_role

cfg_roles = 'iam_roles'
cfg_roles_locked = 'iam_roles_locked'


class IAm(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'iam'
        self.help = '$[iam-help]'
        self.allow_pm = False
        self.user_delay = 60
        self.category = categories.UTILITY
        self.default_config = {
            'iam_roles_limit': 50
        }

    async def handle(self, cmd):
        if not cmd.can_manage_roles():
            await cmd.answer('$[iam-no-permission]')
            return

        member = cmd.author
        roles = cmd.config.get_list(cfg_roles)

        if cmd.argc == 0:
            if len(roles) == 0:
                await cmd.answer('$[iam-no-roles]')
                return False
            else:
                # Convert roles ID list to names, filter not available roles
                roles = [get_guild_role(cmd.guild, r) for r in roles]
                roles = [r.name for r in roles if r is not None]
                await cmd.answer('$[iam-roles-list]', locales={'roles': ', '.join(roles)})
                return False

        role = get_guild_role(cmd.guild, cmd.text, False)
        if role is None or str(role.id) not in roles:
            await cmd.answer('$[iam-role-not-available]')
            return False

        if role in member.roles:
            await cmd.answer('$[iam-already-has-role]')
            return False

        if role >= cmd.guild.me.top_role:
            await cmd.answer('$[iam-disallowed-role]')
            return False

        try:
            await member.add_roles(role)
            await cmd.answer('$[iam-role-given]', locales={'role': role.name})
        except discord.Forbidden:
            await cmd.answer('$[iam-forbidden-exception]')
            return False
        except Exception as e:
            self.log.exception(e)
            raise e


class IAmNot(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'iamnot'
        self.help = '$[iamnot-help]'
        self.format = '$[iamnot-format]'
        self.allow_pm = False
        self.user_delay = 10
        self.category = categories.UTILITY

    async def handle(self, cmd):
        if cmd.argc == 0:
            await cmd.answer('$[format]: $[iamnot-format]')
            return

        member = cmd.author
        roles = cmd.config.get_list(cfg_roles)
        role = get_guild_role(cmd.guild, cmd.text, False)

        if role is None:
            await cmd.answer('$[iamroles-not-found]')
            return

        if str(role.id) not in roles:
            if role in member.roles:
                await cmd.answer('$[iam-not-self-managed]')
            else:
                await cmd.answer('$[iam-role-not-available]')
            return

        if role >= cmd.guild.me.top_role:
            await cmd.answer('$[iam-disallowed-role]')
            return

        roles_locked = cmd.config.get_list(cfg_roles_locked)
        if str(role.id) in roles_locked:
            await cmd.answer('$[iamnot-cant-remove]')
            return

        try:
            await member.remove_roles(role)
            await cmd.answer('$[iamnot-removed-role]', locales={'role': role.name})
        except discord.Forbidden:
            await cmd.answer('$[iamnot-forbidden-exception]')


class IAmRoles(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'iamroles'
        self.help = '$[iamroles-help]'
        self.format = '$[iamroles-format]'
        self.allow_pm = False
        self.owner_only = True
        self.category = categories.STAFF

    async def handle(self, cmd):
        if not cmd.can_manage_roles():
            await cmd.answer('$[iam-no-permission]')
            return

        roles = cmd.config.get_list(cfg_roles)
        roles_locked = cmd.config.get_list(cfg_roles_locked)
        limit = self.bot.config['iam_roles_limit']

        if cmd.argc == 0:
            if len(roles) == 0:
                await cmd.answer('$[iam-no-roles]')
                return
            else:
                # Convert roles ID list to their name, show "ND:(id)" if it's not available.
                roles = [get_guild_role(cmd.guild, r) or r for r in roles]
                roles = [(r.name if isinstance(r, discord.Role) else 'ND:' + r) for r in roles]
                await cmd.answer('$[iam-roles-list]', locales={'roles': ', '.join(roles)})
                return

        # shorthands: using + and - to add and remove roles
        if cmd.text.startswith('+'):
            cmd.argc += 1
            cmd.args.insert(0, 'add')
            cmd.args[1] = cmd.args[1][1:]
            cmd.text = 'add ' + cmd.text[1:]
        if cmd.text.startswith('-'):
            cmd.argc += 1
            cmd.args.insert(0, 'remove')
            cmd.args[1] = cmd.args[1][1:]
            cmd.text = 'remove ' + cmd.text[1:]
        if cmd.text.startswith('!'):
            cmd.argc += 1
            cmd.args.insert(0, 'lock')
            cmd.args[1] = cmd.args[1][1:]
            cmd.text = 'lock ' + cmd.text[1:]
        if cmd.text.startswith('?'):
            cmd.argc += 1
            cmd.args.insert(0, 'unlock')
            cmd.args[1] = cmd.args[1][1:]
            cmd.text = 'unlock ' + cmd.text[1:]

        if cmd.argc < 2:
            await cmd.answer('$[format]: $[iamroles-format]')
            return

        if cmd.args[0] == 'add':
            if len(roles) > limit:
                await cmd.answer('$[iamroles-limit-error]', locales={'limit': limit})
                return

            role = get_guild_role(cmd.guild, ' '.join(cmd.args[1:]))
            if role is None:
                await cmd.answer('$[iamroles-not-found]')
                return

            if role >= cmd.guild.me.top_role:
                await cmd.answer('$[iamroles-bot-superior-role]')
                return

            if role >= cmd.author.top_role:
                await cmd.answer('$[iamroles-author-superior-role]')
                return

            if str(role.id) in cmd.config.get_list(cfg_roles):
                await cmd.answer('$[iamroles-already-added]')
                return

            cmd.config.add(cfg_roles, role.id)
            await cmd.answer('$[iamroles-added]')
            return
        elif cmd.args[0] == 'remove':
            if len(roles) == 0:
                await cmd.answer('$[iamroles-no-removable-roles]')
                return

            role_raw = ' '.join(cmd.args[1:])
            role = get_guild_role(cmd.guild, ' '.join(cmd.args[1:]))
            if role is None:
                if role_raw in roles:
                    role_id = role_raw
                    role_name = 'ND:' + role_raw
                else:
                    await cmd.answer('$[iamroles-not-added]')
                    return
            else:
                role_id = role.id
                role_name = role.name

            cmd.config.remove(cfg_roles, role_id)
            await cmd.answer('$[iamroles-removed]', locales={'role': role_name})
        elif cmd.args[0] == 'lock':
            if cmd.argc < 2:
                await cmd.answer('$[format]: $[iamroles-lock-format]')
                return

            if len(roles) == 0:
                await cmd.answer('$[iamroles-lock-none]')
                return

            role_raw = ' '.join(cmd.args[1:])
            role = get_guild_role(cmd.guild, ' '.join(cmd.args[1:]))
            role_id = role_raw if role is None or role_raw in roles else role.id

            if role_id not in roles:
                await cmd.answer('$[iamroles-not-added]')
                return

            if role_id in roles_locked:
                await cmd.answer('$[iamroles-lock-already]')
                return

            cmd.config.add(cfg_roles_locked, role_id)
            await cmd.answer('$[iamroles-lock-locked]')

        elif cmd.args[0] == 'unlock':
            if cmd.argc < 2:
                await cmd.answer('$[format]: $[iamroles-unlock-format]')
                return

            if len(roles_locked) == 0:
                await cmd.answer('$[iamroles-unlock-none]')
                return

            role_raw = ' '.join(cmd.args[1:])
            role = get_guild_role(cmd.guild, ' '.join(cmd.args[1:]))
            role_id = role_raw if role is None or role_raw in roles else role.id

            if role_id not in roles_locked:
                await cmd.answer('$[iamroles-not-added]')
                return

            if role_id not in roles_locked:
                await cmd.answer('$[iamroles-unlock-not-locked]')
                return

            cmd.config.remove(cfg_roles_locked, role_id)
            await cmd.answer('$[iamroles-unlock-unlocked]')

        else:
            await cmd.answer('$[iamroles-no-subcommand]')
