import asyncio

from bot import Command
from bot.utils import get_server_role


class AutoRole(Command):
    __version__ = '1.0.1'
    __author__ = 'makzk'
    cfg_name = 'autoroles_ids'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'autorole'
        self.aliases = ['autorol']
        self.help = 'Da un rol a todos los usuarios nuevos y existentes'
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, cmd):
        if not self.can_manage_roles(cmd.server):
            await cmd.answer('comando deshabilitado, no es posible manejar roles en este servidor')
            return

        roles = [get_server_role(cmd.server, r) for r in cmd.config.get_list(AutoRole.cfg_name)]
        roles = [r for r in roles if r is not None]

        if cmd.argc == 0:
            cmd.args.append('list')

        if cmd.args[0] in ['add', 'set', 'remove'] and cmd.argc < 2:
            await cmd.answer('formato: $CMD (add|set|remove|give) (rol,id)')
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
        elif cmd.args[0] == 'give':
            if len(roles) == 0:
                await cmd.answer('no hay roles para dar automáticamente')
                return

            msg = await cmd.answer('asignando roles...')

            total = len(cmd.server.members)
            loop = asyncio.get_event_loop()
            i = 0

            async def upd():
                await self.bot.edit_message(msg, '{}, asignando roles... {}/{}'.format(cmd.author_name, i, total))

                if i < total:
                    await asyncio.sleep(3)
                    loop.create_task(upd())

            loop.create_task(upd())

            for member in list(cmd.server.members):
                await self.give_roles(member)
                i += 1

            await self.bot.edit_message(msg, '{}, asignando roles... listo!'.format(cmd.author_name))
        elif cmd.args[0] == 'take':
            if len(roles) == 0:
                await cmd.answer('no hay roles para asignados automáticamente')
                return

            msg = await cmd.answer('quitando roles...')

            total = len(cmd.server.members)
            loop = asyncio.get_event_loop()
            i = 0

            async def upd():
                await self.bot.edit_message(msg, '{}, quitando roles... {}/{}'.format(cmd.author_name, i, total))

                if i < total:
                    await asyncio.sleep(3)
                    loop.create_task(upd())

            loop.create_task(upd())

            for member in list(cmd.server.members):
                await self.take_roles(member)
                i += 1

            await self.bot.edit_message(msg, '{}, quitando roles... listo!'.format(cmd.author_name))
        else:
            await cmd.answer('formato: $CMD (add|set|remove|give) (rol,id)')

    async def on_member_join(self, member):
        await self.give_roles(member)

    def get_roles(self, server):
        cfg = self.config_mgr(server.id)
        roles = [get_server_role(server, r) for r in cfg.get_list(AutoRole.cfg_name)]
        return [r for r in roles if r is not None]

    async def give_roles(self, member):
        roles = self.get_roles(member.server)

        if len(roles) == 0:
            self.log.debug('no autoroles in this server')
            return

        # self.log.debug('giving role(s) %s to %s', [r.name for r in roles], member)
        await self.bot.add_roles(member, *roles)

    async def take_roles(self, member):
        roles = self.get_roles(member.server)

        if len(roles) == 0:
            self.log.debug('no autoroles in this server')
            return

        # self.log.debug('taking role(s) %s from %s', [r.name for r in roles], member)
        await self.bot.remove_roles(member, *roles)
