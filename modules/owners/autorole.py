from bot import Command
from bot.utils import get_server_role


class AutoRole(Command):
    __version__ = '0.0.1'
    __author__ = 'makzk'
    cfg_name = 'autoroles_ids'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'autorole'
        self.aliases = ['autorol']
        self.help = 'Da un rol a todos los usuarios nuevos y existentes'
        self.owner_only = True

    async def handle(self, cmd):
        if not self.can_manage_roles(cmd.server):
            await cmd.answer('comando deshabilitado, no es posible manejar roles en este servidor')
            return

        roles = [get_server_role(cmd.server, r) for r in cmd.config.get_list(AutoRole.cfg_name)]
        roles = [r for r in roles if r is not None]

        if cmd.argc == 0:
            cmd.args.append('list')

        if cmd.args[0] in ['add', 'set', 'remove'] and cmd.argc < 2:
            await cmd.answer('formato: $CMD (add|set|remove|auto) (rol,id)')
            return

        if cmd.args[0] == 'list':
            roles_names = [r.name for r in roles]
            if len(roles_names) == 1:
                await cmd.answer('el rol automáticamente asignado es: ' + roles_names[0])
            elif len(roles_names) > 1:
                await cmd.answer('roles automáticamente asignados: ' + (', '.join(roles_names)))
            else:
                await cmd.answer('no hay ningún rol asignado automáticamente')
        elif cmd.args[0] == 'add':
            role = get_server_role(cmd.server, ' '.join(cmd.args[1:]))
            if role is None:
                await cmd.answer('rol no encontrado')
            elif role.id in [r.id for r in roles]:
                await cmd.answer('ese rol ya está agregado')
            elif role >= cmd.server.me.top_role:
                await cmd.answer('no me es posible asignar este rol y por lo tanto no lo puedo agregar')
            else:
                cmd.config.add(AutoRole.cfg_name, role.id)
                await cmd.answer('rol agregado')
        elif cmd.args[0] == 'set':
            role = get_server_role(cmd.server, ' '.join(cmd.args[1:]))
            if role is None:
                await cmd.answer('rol no encontrado')
            elif role.id in [r.id for r in roles]:
                await cmd.answer('ese rol ya está asignado')
            elif role >= cmd.server.me.top_role:
                await cmd.answer('no me es posible asignar este rol y por lo tanto no lo puedo agregar')
            else:
                cmd.config.set_list(AutoRole.cfg_name, [role.id])
                await cmd.answer('rol asignado')
        elif cmd.args[0] == 'remove':
            role = get_server_role(cmd.server, ' '.join(cmd.args[1:]))
            if role is None:
                role = ' '.join(cmd.args[1:])
                if role not in cmd.config.get_list(AutoRole.cfg_name):
                    await cmd.answer('ese rol no está asignado')
                else:
                    cmd.config.remove(AutoRole.cfg_name, role)
                    await cmd.answer('rol eliminado')
            else:
                if role.id not in [r.id for r in roles]:
                    await cmd.answer('ese rol no está asignado')
                else:
                    cmd.config.remove(AutoRole.cfg_name, role.id)
                    await cmd.answer('rol eliminado')
        elif cmd.args[0] == 'auto':
            await cmd.answer('wip')

    async def on_member_join(self, member):
        cfg = self.config_mgr(member.server.id)
        roles = [get_server_role(member.server, r) for r in cfg.config.get_list(AutoRole.cfg_name)]
        roles = [r for r in roles if r is not None]

        if len(roles) == 0:
            return

        await self.bot.add_roles(member, roles)
