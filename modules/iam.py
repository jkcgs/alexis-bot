import discord

from bot import Command
from bot.utils import member_has_role, get_server_role

cfg_roles = 'iam_roles'


class IAm(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'iam'
        self.help = 'Permite asignarte un rol'
        self.allow_pm = False
        self.user_delay = 60
        self.default_config = {
            'iam_roles_limit': 20
        }

    async def handle(self, cmd):
        if not self.can_manage_roles(cmd.server):
            await cmd.answer('comando deshabilitado, no es posible manejar roles en este servidor')
            return

        roles = cmd.config.get_list(cfg_roles)

        if cmd.argc == 0:
            if len(roles) == 0:
                await cmd.answer('no hay roles disponibles')
                return False
            else:
                # Convertir lista de IDs de roles a nombres, filtrar roles no disponibles
                roles = [get_server_role(cmd.server, r) for r in roles]
                roles = [r.name for r in roles if r is not None]
                await cmd.answer('roles disponibles: ' + (', '.join(roles)))
                return False

        role = get_server_role(cmd.server, cmd.text)
        if role is None or role.id not in roles:
            await cmd.answer('ese rol no está disponible')
            return False

        if member_has_role(cmd.author, role):
            await cmd.answer('ya tienes ese rol')
            return False

        if role >= cmd.server.me.top_role:
            await cmd.answer('no me es posible asignar este rol')
            return False

        try:
            await self.bot.add_roles(cmd.author, role)
            await cmd.answer('ahora tienes el rol **{}**!'.format(role.name))
        except discord.Forbidden:
            await cmd.answer('no pude asignar el rol!')
            return False
        except Exception as e:
            self.log.exception(e)
            raise e


class IAmNot(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'iamnot'
        self.help = 'Quita un rol asignado con $PXiam'
        self.allow_pm = False
        self.user_delay = 10

    async def handle(self, cmd):
        if cmd.argc == 0:
            await cmd.answer('formato: $CMD <rol>')
            return

        roles = cmd.config.get_list(cfg_roles)
        role = get_server_role(cmd.server, cmd.text)

        if role is None:
            await cmd.answer('rol no disponible')
            return

        if role.id not in roles:
            if member_has_role(cmd.author, role):
                await cmd.answer('ese rol no es autogestionable')
            else:
                await cmd.answer('rol no disponible')

            return

        if role >= cmd.server.me.top_role:
            await cmd.answer('no puedo gestionar este rol')
            return

        try:
            await self.bot.remove_roles(cmd.author, role)
            await cmd.answer('rol **{}** quitado'.format(role.name))
        except discord.Forbidden:
            await cmd.answer('no te pude quitar el rol!')


class IAmRoles(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'iamroles'
        self.help = 'Gestión de roles del comando $PXiam'
        self.allow_pm = False
        self.owner_only = True

    async def handle(self, cmd):
        if not self.can_manage_roles(cmd.server):
            await cmd.answer('comando deshabilitado, no es posible manejar roles en este servidor')
            return

        roles = cmd.config.get_list(cfg_roles)
        limit = self.bot.config['iam_roles_limit']

        if cmd.argc == 0:
            if len(roles) == 0:
                await cmd.answer('no hay roles asignados al comando `$PXiam`')
                return
            else:
                # Convertir lista de IDs de roles a su nombre, mostrar "ND:(id)" si no está disponible.
                roles = [get_server_role(cmd.server, r) or r for r in roles]
                roles = [(r.name if isinstance(r, discord.Role) else 'ND:' + r) for r in roles]
                await cmd.answer('roles disponibles: ' + (', '.join(roles)))
                return

        # shorthands: agrega un argumento al comando y elimina los símbolos
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

        if cmd.argc < 2:
            await cmd.answer('formato: `add|remove <rol>` ó `+|-<role>`')
            return

        if cmd.args[0] == 'add':
            if len(roles) > limit:
                await cmd.answer('sólo es posible agregar {} roles'.format(limit))
                return

            role = get_server_role(cmd.server, ' '.join(cmd.args[1:]))
            if role is None:
                await cmd.answer('rol no existente')
                return

            if role >= cmd.server.me.top_role:
                await cmd.answer('este rol es igual o superior en jerarquía al que mayor que tengo asignado y por lo '
                                 'tanto no puedo asignarlo')
                return

            if role >= cmd.author.top_role:
                await cmd.answer('no puedes agregar un rol que es igual o superior en jerarquía a tu mayor rol '
                                 'asignado')
                return

            cmd.config.add(cfg_roles, role.id)
            await cmd.answer('rol agregado!')
            return
        elif cmd.args[0] == 'remove':
            if len(roles) == 0:
                await cmd.answer('no hay roles por quitar')
                return

            role_raw = ' '.join(cmd.args[1:])
            role = get_server_role(cmd.server, ' '.join(cmd.args[1:]))
            if role is None:
                if role_raw in roles:
                    role_id = role_raw
                    role_name = 'ND:' + role_raw
                else:
                    await cmd.answer('ese rol no ha sido agregado')
                    return
            else:
                role_id = role.id
                role_name = role.name

            cmd.config.remove(cfg_roles, role_id)
            await cmd.answer('rol **{}** quitado de $PXiam'.format(role_name))
        else:
            await cmd.answer('wtf')
