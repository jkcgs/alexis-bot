import random
import re

import discord
import peewee

from alexis import Command
from discord import Embed

from alexis.base.database import BaseModel


class UserCmd(Command):
    rx_channel = re.compile('^<#[0-9]+>$')
    chan_config_name = 'join_send_channel'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'user'
        self.aliases = [bot.config['command_prefix'] + 'user']
        self.help = 'Entrega información sobre un usuario'
        self.db_models = [UserNote]

    async def handle(self, message, cmd):
        if cmd.argc >= 1 and cmd.args[0] == 'channel' and not cmd.is_pm and cmd.owner:
            chan = message.channel.mention if cmd.argc == 1 else cmd.args[1]
            await UserCmd._setchannel_handler(cmd, chan)
            return

        if cmd.argc == 0:
            user = cmd.author
        else:
            user = await cmd.get_user(cmd.args[0], member_only=True)
            if user is None:
                await cmd.answer('usuario no encontrado')
                return

        with_notes = cmd.cmdname == self.aliases[0] and cmd.owner
        embed = UserCmd.gen_embed(user, with_notes)
        await cmd.answer('acerca de **{}**'.format(user.id), embed=embed)

    async def on_member_join(self, member):
        cfg = self.config_mgr(member.server.id)
        channel = cfg.get(UserCmd.chan_config_name, '')
        if channel == '':
            return

        channel = member.server.get_channel(channel)
        if channel is None:
            channel = discord.Object(id=channel)

        await self.bot.send_message(channel, 'Nuevo usuario! <@{mid}> ID: **{mid}**'.format(mid=member.id),
                                    embed=UserCmd.gen_embed(member))

    async def on_member_remove(self, member):
        cfg = self.config_mgr(member.server.id)
        channel = cfg.get(UserCmd.chan_config_name, '')
        if channel == '':
            return

        channel = member.server.get_channel(channel)
        if channel is None:
            channel = discord.Object(id=channel)

        await self.bot.send_message(channel, 'El usuario <@{mid}> ({mid}) dejó el servidor.'.format(mid=member.id))

    @staticmethod
    def get_note(member):
        if not isinstance(member, discord.Member):
            raise RuntimeError('member argument can only be a discord.Member')

        xd, _ = UserNote.get_or_create(serverid=member.server.id, userid=member.id)
        return xd.note

    @staticmethod
    def set_note(member, note):
        if not isinstance(member, discord.Member):
            raise RuntimeError('member argument can only be a discord.Member')

        xd, _ = UserNote.get_or_create(serverid=member.server.id, userid=member.id)
        xd.note = note
        xd.save()

    @staticmethod
    async def _setchannel_handler(cmd, value):
        if value != 'off' and not UserCmd.rx_channel.match(value):
            await cmd.answer('por favor ingresa un canal u "off" como valor')
            return

        if value == 'off':
            value = ''

        cmd.config.set(UserCmd.chan_config_name, value[2:-1])

        if value == '':
            await cmd.answer('información de usuarios desactivada')
        else:
            await cmd.answer('canal de información de usuarios actualizado a {}'.format(value))

    @staticmethod
    def gen_embed(member, note=False):
        embed = Embed()
        embed.add_field(name='Nombre', value=str(member))
        embed.add_field(name='Nick', value=member.nick if member.nick is not None else 'Ninguno :c')
        embed.add_field(name='Usuario creado el', value=UserCmd.parsedate(member.created_at))
        embed.add_field(name='Se unió al server el', value=UserCmd.parsedate(member.joined_at))

        if member.avatar_url != '':
            embed.set_thumbnail(url=member.avatar_url)
        else:
            embed.set_thumbnail(url=member.default_avatar_url)

        if note and isinstance(member, discord.Member):
            n = UserCmd.get_note(member)
            embed.add_field(name='Notas:', value=n if n != '' else '(sin notas)')

        return embed

    @staticmethod
    def parsedate(the_date):
        return the_date.strftime('%d de %B de %Y, %H:%M:%S')


class UserNoteCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'usernote'
        self.help = 'Define una nota para el usuario'
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, message, cmd):
        if cmd.argc < 1:
            return

        member = await cmd.get_user(cmd.args[0], member_only=True)
        if member is None:
            await cmd.answer('usuario no encontrado')
            return

        UserCmd.set_note(member, ' '.join(cmd.args[1:]))
        await cmd.answer(
            random.choice(['ok', 'ya', 'bueno', 'ta bn eso', 'xd', 'sip bn dixo', ':ok_hand:', ':thumbs_up']))


class UserNote(BaseModel):
    userid = peewee.TextField()
    serverid = peewee.TextField()
    note = peewee.TextField(default='')
