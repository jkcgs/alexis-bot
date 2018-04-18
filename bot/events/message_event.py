import discord
import re

from discord import Embed

from bot.libs.configuration import ServerConfiguration
from bot.libs.language import SingleLanguage
from bot.utils import pat_emoji, is_owner, pat_channel

pat_user_mention = re.compile('^<@!?[0-9]+>$')
pat_snowflake = re.compile('^\d{10,19}$')


class MessageEvent:
    def __init__(self, message, bot):
        if not isinstance(message, discord.Message):
            raise RuntimeError('message argument is not a discord.Message instance')

        self.bot = bot
        self.message = message
        self.channel = message.channel
        self.author = message.author
        self.author_name = message.author.display_name
        self.is_pm = message.server is None
        self.self = message.author.id == bot.user.id
        self.text = message.content
        self.bot_owner = message.author.id in bot.config['bot_owners']
        self.owner = is_owner(bot, message.author, message.server)
        self.prefix = MessageEvent.get_prefix(message, bot)

        self.server = None
        self.server_member = None
        self.config = None

        if not self.is_pm:
            self.server = message.server
            self.server_member = message.server.get_member(self.bot.user.id)
            self.config = ServerConfiguration(self.bot.sv_config, message.server.id)
            self.lang = self.bot.get_lang(message.server.id)
        else:
            self.lang = SingleLanguage(self.bot.lang, bot.config['default_lang'])

    async def answer(self, content='', to_author=False, withname=True, **kwargs):
        """
        Envía un mensaje al canal desde donde se originó el mensaje
        :param content: El contenido del mensaje. Si es una instancia de discord.Embed, se convierte en un Embed
        :param to_author: Si se define como True, se envía directamente a quien envió el mensaje, en vez del canal desde
        donde se envió.
        :param withname: Establece si se agrega el nombre del usuario a quien se le responde al principio del mensaje en
        el formato "<display_name>, ...". Si el mensaje no lleva contenido, no se agrega la coma, ni un punto.
        :param kwargs: Parámetros adicionales a pasar a la función send_message de discord.Client
        """
        if isinstance(content, Embed):
            kwargs['embed'] = content
            content = ''

        content = content.replace('$AU', self.author_name)

        if withname:
            if content != '':
                content = ', ' + content
            content = self.author_name + content

        dest = self.message.author if to_author else self.message.channel
        return await self.bot.send_message(dest, content, **kwargs)

    async def answer_embed(self, msg, delete_trigger=False, withname=True):
        if delete_trigger:
            try:
                await self.bot.delete_message(self.message)
            except discord.Forbidden:
                pass

        if not isinstance(msg, Embed):
            msg = Embed(description=msg)

        if withname:
            msg.set_footer(text='para ' + self.author_name)

        await self.answer(embed=msg, withname=False)

    async def typing(self):
        """
        Envía el estado "Escribiendo..." al canal desde el cual se recibió el mensaje.
        """
        await self.bot.send_typing(self.message.channel)

    def member_by_id(self, user_id):
        """
        (Sólo para mensajes en guild) Entrega un miembro del servidor, según el ID de usuario
        :param user_id: El ID del usuario a buscar.
        :return: El discord.Member del servidor. Si no se encontró, retorna None
        """
        if self.is_pm:
            return None

        for member in self.message.server.members:
            if member.id == user_id:
                return member

        return None

    def is_owner(self, user):
        return is_owner(self.bot, user, self.message.server)

    def no_tags(self, users=True, channels=True, emojis=True):
        txt = self.text

        # tags de usuarios
        if users:
            for mention in self.message.mentions:
                mtext = mention.mention
                if mention.name != mention.display_name:
                    mtext = mtext.replace('@', '@!')

                txt = txt.replace(mtext, mention.display_name)

        # tags de canales
        if channels:
            for mention in self.message.channel_mentions:
                txt = txt.replace(mention.mention, '#' + mention.name)

        # emojis custom
        if emojis:
            for m in pat_emoji.finditer(txt):
                txt = txt.replace(m.group(0), m.group(1))

        return txt

    async def get_user(self, user, member_only=False):
        """
        Obtiene un usuario según su nombre, una mención, su ID o su nombre con discriminador de Discord.
        :param user:
        :param member_only:
        :return:
        """
        if self.is_pm:
            raise RuntimeError('Esta función no funciona desde PMs')

        if isinstance(user, discord.Member) or isinstance(user, discord.User):
            return user

        if user.startswith("@"):
            user = user[1:]

        u = self.message.server.get_member_named(user)
        if u is not None:
            return u

        if pat_user_mention.match(user):
            st = 3 if user[2] == '!' else 2
            user = user[st:-1]

        u = self.message.server.get_member(user)
        if u is not None:
            return u

        if member_only or not pat_snowflake.match(user):
            return None

        return await self.bot.get_user_info(user)

    def find_channel(self, channel):
        """
        Encuentra un canal según su nombre, #nombre, mención o ID, para un mensaje desde una guild.
        :param channel: El nombre, #nombre, mención o ID del canal a buscar
        :return: El discord.Channel. Si no se encontró, se devuelve None.
        """
        if self.is_pm:
            return None

        sv = self.message.server
        if pat_snowflake.match(channel):
            return sv.get_channel(channel)
        elif pat_channel.match(channel):
            return sv.get_channel(channel[2:-1])
        else:
            if channel.startswith('#'):
                channel = channel[1:]

            for chan in sv.channels:
                if chan.name == channel:
                    return chan

        return None

    def lng(self, name, **kwargs):
        return self.lang.get(name, **kwargs)

    def __str__(self):
        return '[{}  channel="{}#{}" author="{}" text="{}"]'.format(
            self.__class__.__name__, self.message.server, self.message.channel, self.message.author, self.text)

    @staticmethod
    def get_prefix(message, bot):
        prefix = bot.config['command_prefix']
        if message.server is not None:
            prefix = bot.sv_config.get(message.server.id, 'command_prefix', prefix)

        return prefix

