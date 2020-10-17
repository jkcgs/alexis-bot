from bot import Command, categories
from bot.utils import get_guild_role, auto_int


class OwnerRoles(Command):
    __author__ = 'makzk'
    __version__ = '1.1.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ownerrole'
        self.help = '$[owr-help]'
        self.format = '$[owr-format]'
        self.owner_only = True
        self.category = categories.STAFF

    async def handle(self, cmd):
        if cmd.argc < 1:
            return await cmd.send_usage()

        await cmd.typing()
        default_role = self.bot.config['owner_role']
        owner_roles = cmd.config.get_list('owner_roles', [default_role] if default_role else [])

        if cmd.args[0] in ['set', 'add', 'remove']:
            if cmd.argc < 2:
                return await cmd.send_usage()

            cmd_role = ' '.join(cmd.args[1:])
            role = get_guild_role(cmd.message.guild, auto_int(cmd_role))
            if role is None and cmd_role not in owner_roles:
                await cmd.answer('$[owr-role-not-found]')
                return

            if cmd.args[0] == 'set':
                if role is None:  # doble check
                    await cmd.answer('$[owr-role-not-found]')
                    return

                cmd.config.set_list('owner_roles', [str(role.id)])
                await cmd.answer('$[owr-set]', locales={'role_name': role.name})
            elif cmd.args[0] == 'add':
                if str(role.id) in owner_roles:
                    await cmd.answer('$[owr-already-owner]')
                    return

                cmd.config.set_list('owner_roles', owner_roles + [str(role.id)])
                await cmd.answer('$[owr-added]', locales={'role_name': role.name})
            elif cmd.args[0] == 'remove':
                if str(role.id) not in owner_roles:
                    await cmd.answer('$[owr-not-owner]')
                    return

                owner_roles.remove(str(role.id))
                cmd.config.set_list('owner_roles', owner_roles)
                await cmd.answer('$[owr-removed]', locales={'role_name': role.name})
        elif cmd.args[0] == 'list':
            msg = '$[owr-title] '
            msg_list = []
            for roleid in owner_roles:
                srole = get_guild_role(cmd.message.guild, roleid)
                if srole is not None:
                    msg_list.append(srole.name)
                else:
                    member = cmd.message.guild.get_member(roleid)
                    if member is not None:
                        msg_list.append('$[owr-usr]:' + member.display_name)
                    else:
                        msg_list.append('id:' + roleid)
            await cmd.answer(msg + ', '.join(msg_list))
        else:
            await cmd.answer('$[owr-format]')
