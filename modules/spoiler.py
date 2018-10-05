import base64

import discord
from discord import Embed

from bot import Command

url = 'https://assets.imgix.net/examples/clouds.jpg?w=640&txtsize=64&txtfont64=RnV0dXJhIENvbmRlbnNlZCBNZWRpdW0' \
      '&txtclr=ff2e4357&txtalign=middle%2Ccenter&txt64={}&h=200&fit=crop&blur=150&txtfit=max'


class Spoiler(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'spoiler'
        self.help = '$[spoiler-help]'
        self.allow_pm = False

    async def handle(self, cmd):

        if not self.can_delete_msg(cmd.server):
            await cmd.answer('$[spoiler-error-cant]', locales={'mention': cmd.author.mention})
        else:
            try:
                await self.bot.delete_message_silent(cmd.message)

            except discord.Forbidden:
                await cmd.answer('$[spoiler-error-couldnt]', locales={'mention': cmd.author.mention})

        if cmd.argc == 0:
            await cmd.answer('$[format]: $[spoiler-format]')
            return

        enc = base64.b64encode(cmd.text.encode('utf-8'))
        img_url = url.format(enc.decode('utf-8'))
        emb = Embed(description='[$[spoiler-link]]({})'.format(img_url))
        emb.set_footer(text='$[spoiler-from]', icon_url=cmd.author.avatar_url or cmd.author.default_avatar_url)
        await cmd.answer(emb)

    def can_delete_msg(self, server):
        self_member = server.get_member(self.bot.user.id)
        return self_member.server_permissions.manage_messages
