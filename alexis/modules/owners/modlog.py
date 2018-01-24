import random
import re
from datetime import datetime

import discord
import peewee

from alexis import Command, Alexis, MessageCmd
from discord import Embed

from alexis.database import BaseModel
from alexis.logger import log


class ModLog(Command):
    rx_channel = re.compile('^<#[0-9]+>$')
    chan_config_name = 'join_send_channel'

    def __init__(self, bot):
        super().__init__(bot)

    async def on_member_join(self, member):
        await ModLog.send_modlog(
            self.bot, member.server.id,
            'Nuevo usuario! <@{mid}> ID: **{mid}**'.format(mid=member.id),
            embed=ModLog.gen_embed(member, more=True))

    async def on_member_remove(self, member):
        await ModLog.send_modlog(
            self.bot, member.server.id,
            'El usuario <@{mid}> ("{name}", {mid}) dejó el servidor.'.format(mid=member.id, name=str(member)))

    async def on_message_delete(self, message):
        if message.channel.server is None:
            return

        footer = 'Enviado: ' + ModLog.parsedate(message.timestamp)
        if message.edited_timestamp is not None:
            footer += ', editado: ' + ModLog.parsedate(message.edited_timestamp)

        embed = Embed(description=message.content)
        embed.set_footer(text=footer)
        await ModLog.send_modlog(
            self.bot, message.channel.server.id,
            'Se ha borrado un mensaje de {} en el canal {}'.format(message.author.mention, message.channel.mention),
            embed=embed
        )

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
    def get_names(userid):
        xd = UserNameReg.select().where(UserNameReg.userid == userid).order_by(UserNameReg.timestamp.desc()).limit(10)
        return [u.name for u in xd]

    @staticmethod
    async def send_modlog(bot, serverid='', message='', embed=None):
        if isinstance(bot, MessageCmd):
            serverid = bot.message.channel.id
            bot = bot.bot
        elif not isinstance(bot, Alexis):
            raise RuntimeError('bot must be an Alexis or MessageCmd instance')

        if (message is None or message == '') and embed is None:
            raise RuntimeError('message or embed arguments are required')

        if embed is not None and not isinstance(embed, Embed):
            raise RuntimeError('embed must be a discord.Embed instance')

        chanid = bot.sv_config.get(serverid, ModLog.chan_config_name)
        if chanid == '':
            return

        chan = bot.get_channel(chanid)
        if chan is None:
            log.debug('canal no encontrado (svid %s chanid %s)', serverid, chanid)
            return

        await bot.send_message(chan, message, embed=embed)

    @staticmethod
    def gen_embed(member, more=False):
        embed = Embed()
        embed.add_field(name='Nombre', value=str(member))
        embed.add_field(name='Nick', value=member.nick if member.nick is not None else 'Ninguno :c')
        embed.add_field(name='Usuario creado el', value=ModLog.parsedate(member.created_at))
        embed.add_field(name='Se unió al server el', value=ModLog.parsedate(member.joined_at))

        if member.avatar_url != '':
            embed.set_thumbnail(url=member.avatar_url)
        else:
            embed.set_thumbnail(url=member.default_avatar_url)

        if more and isinstance(member, discord.Member):
            n = ModLog.get_note(member)
            names = ModLog.get_names(member.id)
            if len(names) == 0:
                names = [member.name]

            embed.add_field(name='Notas', value=n if n != '' else '(sin notas)')
            embed.add_field(name='Nombres ', value=', '.join(names))

        return embed

    @staticmethod
    def parsedate(the_date):
        return the_date.strftime('%Y-%m-%d %H:%M:%S')


class UserCommand(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'user'
        self.aliases = [bot.config['command_prefix'] + 'user']
        self.help = 'Entrega información sobre un usuario'

    async def handle(self, cmd):
        if cmd.cmdname == self.aliases[0] and not cmd.owner:
            return

        if cmd.argc == 0:
            user = cmd.author
        else:
            user = await cmd.get_user(cmd.text, member_only=True)
            if user is None:
                await cmd.answer('usuario no encontrado')
                return

        with_notes = cmd.cmdname == self.aliases[0] and cmd.owner
        embed = ModLog.gen_embed(user, with_notes)
        await cmd.answer('acerca de **{}**'.format(user.id), embed=embed)


class ModLogChannel(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'logchannel'
        self.help = 'Determina el canal de registros de moderación'
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, cmd):
        if cmd.argc != 1:
            await cmd.answer('formato: $PX$NM <#canal>')
            return

        chan = cmd.args[0]
        if chan != 'off' and not ModLog.rx_channel.match(chan):
            await cmd.answer('por favor ingresa un canal u "off" como valor')
            return

        value = '' if chan == 'off' else chan[2:-1]
        cmd.config.set(ModLog.chan_config_name, value)

        if chan == '':
            await cmd.answer('información de usuarios desactivada')
        else:
            await cmd.answer('canal de información de usuarios actualizado a <#{}>'.format(value))


class UserNoteCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'usernote'
        self.help = 'Define una nota para el usuario'
        self.db_models = [UserNote]
        self.owner_only = True
        self.allow_pm = False

    async def handle(self, cmd):
        if cmd.argc < 1:
            return

        member = await cmd.get_user(cmd.args[0], member_only=True)
        if member is None:
            await cmd.answer('usuario no encontrado')
            return

        note = ' '.join(cmd.args[1:])
        if len(note) > 1000:
            await cmd.answer('nooo, len(note) <= 1000')
            return

        ModLog.set_note(member, ' '.join(cmd.args[1:]))
        await cmd.answer(
            random.choice(['ok', 'ya', 'bueno', 'ta bn eso', 'xd', 'sip bn dixo', ':ok_hand:', ':thumbs_up']))


class UpdateUsername(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.db_models = [UserNameReg]
        self.updating = False
        self.updated = False

    async def on_ready(self):
        if self.updating or self.updated:
            return

        self.log.debug('Actualizando usuarios...')
        c = self.all()

        if c is not None:
            self.log.debug('Usuarios actualizados: %i', c)

    async def on_member_join(self, member):
        if not self.updating:
            UpdateUsername.do_it(member)

    async def on_member_update(self, before, after):
        if not self.updating:
            UpdateUsername.do_it(after)

        if before.name != after.name:
            cfg = self.config_mgr(before.server.id)
            channel = cfg.get(ModLog.chan_config_name, '')
            if channel == '':
                return

            channel = before.server.get_channel(channel)
            if channel is None:
                channel = discord.Object(id=channel)

            disp = ' (nick actual: "{}")'.format(after.display_name) if after.display_name != after.name else ''
            await self.bot.send_message(channel, 'El usuario "*{}*" ha cambiado su nombre a "**{}**"{}.'.format(
                before.name, after.name, disp
            ))

    def all(self):
        if self.updating or self.updated:
            return

        self.updating = True

        # Don't do this at home
        j = {u.userid: u.name for u in
             UserNameReg.select(
                 UserNameReg.userid,
                 UserNameReg.name,
                 peewee.fn.MAX(UserNameReg.timestamp)
             ).group_by(UserNameReg.userid)}

        # Neither this thing
        k = [{'userid': m.id, 'name': m.name}
             for m in self.bot.get_all_members() if m.id not in j or j[m.id] != m.name]
        k = [i for n, i in enumerate(k) if i not in k[n + 1:]]  # https://stackoverflow.com/a/9428041

        with self.bot.db.atomic():
            for idx in range(0, len(k), 100):
                UserNameReg.insert_many(k[idx:idx + 100]).execute()

        self.updating = False
        self.updated = True
        return len(k)

    @staticmethod
    def do_it(user):
        if not isinstance(user, discord.User):
            raise RuntimeError('user argument can only be a discord.User')

        r = UserNameReg.select().where(UserNameReg.userid == user.id).order_by(UserNameReg.timestamp.desc()).limit(1)
        u = r.get() if r.count() > 0 else None

        if r.count() == 0 or u.name != user.name:
            old = '(ninguno)' if u is None else u.name
            log.debug('Actualizando usuario "%s" -> "%s" id %s', old, user.name, user.id)
            UserNameReg.create(userid=user.id, name=user.name)
            return True

        return False


class UserNote(BaseModel):
    userid = peewee.TextField()
    serverid = peewee.TextField()
    note = peewee.TextField(default='')


class UserNameReg(BaseModel):
    userid = peewee.TextField()
    name = peewee.TextField()
    timestamp = peewee.DateTimeField(default=datetime.now)
