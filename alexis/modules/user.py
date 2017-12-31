import re

import discord

from alexis import Command
from discord import Embed


class UserCmd(Command):
    rx_channel = re.compile('^<#[0-9]+>$')
    chan_config_name = 'join_send_channel'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'user'
        self.help = 'Entrega información sobre un usuario'
        self.allow_pm = False

    async def handle(self, message, cmd):
        if cmd.argc >= 1 and cmd.args[0] == 'channel':
            chan = message.channel.mention if cmd.argc == 1 else cmd.args[1]
            await UserCmd._setchannel_handler(cmd, chan)
            return

        user = message.mentions[0] if len(message.mentions) == 1 else cmd.author
        embed = UserCmd.gen_embed(user)
        await cmd.answer('acerca de **{}**'.format(user.id), embed=embed)

    # Restaurar el rol de muteado una vez que el usuario ha reingresado
    async def on_member_join(self, member):
        cfg = self.config_mgr(member.server.id)
        channel = cfg.get(UserCmd.chan_config_name, '')
        if channel == '':
            return

        channel = discord.Object(id=channel)
        await self.bot.send_message(channel, 'Nuevo usuario! <@{mid}> ID: **{mid}**'.format(mid=member.id),
                                    embed=UserCmd.gen_embed(member))

    async def on_member_remove(self, member):
        cfg = self.config_mgr(member.server.id)
        channel = cfg.get(UserCmd.chan_config_name, '')
        if channel == '':
            return

        channel = discord.Object(id=channel)
        await self.bot.send_message(channel, 'El usuario <@{mid}> ({mid}) dejó el servidor.'.format(mid=member.id))

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
    def gen_embed(member):
        embed = Embed()
        embed.add_field(name='Nombre', value=str(member))
        embed.add_field(name='Nick', value=member.nick if member.nick is not None else 'Ninguno :c')
        embed.add_field(name='Usuario creado el', value=UserCmd.parsedate(member.created_at))
        embed.add_field(name='Se unió al server el', value=UserCmd.parsedate(member.joined_at))
        if member.avatar_url != '':
            embed.set_thumbnail(url=member.avatar_url)

        return embed

    @staticmethod
    def parsedate(the_date):
        return the_date.strftime('%d de %B de %Y, %H:%M:%S')
