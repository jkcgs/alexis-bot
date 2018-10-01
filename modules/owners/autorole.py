import asyncio

from bot import Command, categories
from bot.utils import get_server_role


class AutoRole(Command):
    __version__ = '1.0.1'
    __author__ = 'makzk'
    cfg_name = 'autoroles_ids'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'autorole'
        self.aliases = ['autorol']
        self.help = '$[autorole-help]'
        self.format = '$[autorole-format]'
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.STAFF

    async def handle(self, cmd):
        if not self.can_manage_roles(cmd.server):
            await cmd.answer('$[autorole-error-cant]')
            return

        roles = [get_server_role(cmd.server, r) for r in cmd.config.get_list(AutoRole.cfg_name)]
        roles = [r for r in roles if r is not None]

        if cmd.argc == 0:
            cmd.args.append('list')

        if cmd.args[0] in ['add', 'set', 'remove'] and cmd.argc < 2:
            await cmd.answer('$[format]: $[autorole-format]')
            return

        if cmd.args[0] == 'list':
            roles_names = [r.name for r in roles]
            if len(roles_names) == 1:
                await cmd.answer('$[autorole-list-single]', locales={'role': roles_names[0]})
            elif len(roles_names) > 1:
                await cmd.answer('$[autorole-list]', locales={'roles': ', '.join(roles_names)})
            else:
                await cmd.answer('$[autorole-list-none]')
        elif cmd.args[0] == 'add':
            role = get_server_role(cmd.server, ' '.join(cmd.args[1:]))
            if role is None:
                await cmd.answer('$[autorole-not-found]')
            elif role.id in [r.id for r in roles]:
                await cmd.answer('$[autorole-already-added]')
            elif role >= cmd.server.me.top_role:
                await cmd.answer('$[autorole-cant-assign]')
            else:
                cmd.config.add(AutoRole.cfg_name, role.id)
                await cmd.answer('$[autorole-added]')
        elif cmd.args[0] == 'set':
            role = get_server_role(cmd.server, ' '.join(cmd.args[1:]))
            if role is None:
                await cmd.answer('$[autorole-not-found]')
            elif role.id in [r.id for r in roles]:
                await cmd.answer('$[autorole-already-added]')
            elif role >= cmd.server.me.top_role:
                await cmd.answer('$[autorole-cant-assign]')
            else:
                cmd.config.set_list(AutoRole.cfg_name, [role.id])
                await cmd.answer('$[autorole-added]')
        elif cmd.args[0] == 'remove':
            role = get_server_role(cmd.server, ' '.join(cmd.args[1:]))
            if role is None:
                role = ' '.join(cmd.args[1:])
                if role not in cmd.config.get_list(AutoRole.cfg_name):
                    await cmd.answer('$[autorole-not-assigned]')
                else:
                    cmd.config.remove(AutoRole.cfg_name, role)
                    await cmd.answer('$[autorole-removed]')
            else:
                if role.id not in [r.id for r in roles]:
                    await cmd.answer('$[autorole-not-assigned]')
                else:
                    cmd.config.remove(AutoRole.cfg_name, role.id)
                    await cmd.answer('$[autorole-removed]')
        elif cmd.args[0] == 'give':
            if len(roles) == 0:
                await cmd.answer('$[autorole-none-available]')
                return

            msg = await cmd.answer('$[autorole-assigning]')

            total = len(cmd.server.members)
            loop = asyncio.get_event_loop()
            i = 0

            async def upd():
                await self.bot.edit_message(msg, '$[autorole-assigning] {}/{}'.format(i, total))

                if i < total:
                    await asyncio.sleep(3)
                    loop.create_task(upd())

            loop.create_task(upd())

            for member in list(cmd.server.members):
                await self.give_roles(member)
                i += 1

            await self.bot.edit_message(msg, '$[autorole-assigning] $[autorole-ready]')
        elif cmd.args[0] == 'take':
            if len(roles) == 0:
                await cmd.answer('$[autorole-none-available]')
                return

            msg = await cmd.answer('$[autorole-removing]')

            total = len(cmd.server.members)
            loop = asyncio.get_event_loop()
            i = 0

            async def upd():
                await self.bot.edit_message(msg, '$[autorole-removing] {}/{}'.format(i, total))

                if i < total:
                    await asyncio.sleep(3)
                    loop.create_task(upd())

            loop.create_task(upd())

            for member in list(cmd.server.members):
                await self.take_roles(member)
                i += 1

            await self.bot.edit_message(msg, '$[autorole-removing] $[autorole-ready]')
        else:
            await cmd.answer('$[format]: $[autorole-format]')

    async def on_member_join(self, member):
        await self.give_roles(member)

    def get_roles(self, server):
        cfg = self.config_mgr(server.id)
        roles = [get_server_role(server, r) for r in cfg.get_list(AutoRole.cfg_name)]
        return [r for r in roles if r is not None]

    async def give_roles(self, member):
        roles = self.get_roles(member.server)

        if len(roles) == 0:
            return

        await self.bot.add_roles(member, *roles)

    async def take_roles(self, member):
        roles = self.get_roles(member.server)

        if len(roles) == 0:
            return

        await self.bot.remove_roles(member, *roles)
