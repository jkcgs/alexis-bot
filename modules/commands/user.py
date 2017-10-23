import re

import discord

from modules.base.command import Command, ConfigError
from discord import Embed


class UserCmd(Command):
    rx_channel = re.compile('^<#[0-9]+>$')
    chan_config_name = 'join_send_channel'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'user'
        self.help = 'Entrega información sobre un usuario'
        self.allow_pm = False
        self.configurations = {UserCmd.chan_config_name: ''}

    async def handle(self, message, cmd):
        if len(cmd.args) > 1 and len(message.mentions) == 1:
            user = message.mentions[0]
        else:
            user = cmd.author

        embed = UserCmd.gen_embed(user)
        await cmd.answer('Acerca de **{}**'.format(user.id), embed=embed)

    # Restaurar el rol de muteado una vez que el usuario ha reingresado
    async def on_member_join(self, member):
        channel = self.get_config(UserCmd.chan_config_name, member.server)
        if channel == '':
            return

        self.log.debug('user info channel id: %s', channel)
        channel = discord.Object(id=channel)
        await self.bot.send_message(channel, embed=UserCmd.gen_embed(member))

    async def config_handler(self, name, value, cmd):
        if name == UserCmd.chan_config_name:
            if not UserCmd.rx_channel.match(value):
                raise ConfigError('Por favor ingresa un canal como valor')

            self.set_config(UserCmd.chan_config_name, value[2:-1], cmd.message.server)
            await cmd.answer('Canal actualizado')

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
