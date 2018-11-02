import base64

import discord
from discord import Embed

from bot import Command

url = 'https://assets.imgix.net/examples/clouds.jpg?w=640&txtsize=64&txtfont64=RnV0dXJhIENvbmRlbnNlZCBNZWRpdW0' \
      '&txtclr=ff2e4357&txtalign=middle%2Ccenter&txt64={}&h=200&fit=crop&blur=150&txtfit=max'


class Spoiler(Command):
    __author__ = 'makzk'
    __version__ = '1.1.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'spoiler'
        self.help = '$[spoiler-help]'
        self.format = '$[spoiler-format]'
        self.allow_pm = False

    async def handle(self, cmd):
        if cmd.argc == 0:
            await cmd.answer('$[format]: $[spoiler-format]')
            return

        if not self.can_delete_msg(cmd.server):
            await cmd.answer('$[spoiler-error-cant]', locales={'mention': cmd.author.mention})
        else:
            try:
                await self.bot.delete_message_silent(cmd.message)

            except discord.Forbidden:
                await cmd.answer('$[spoiler-error-couldnt]', locales={'mention': cmd.author.mention})

        args = cmd.text.split('|')

        enc = base64.b64encode(args[0].encode('utf-8'))
        img_url = url.format(enc.decode('utf-8'))
        emb = Embed(description='[$[spoiler-link]]({})'.format(img_url))
        emb.set_footer(text='$[spoiler-from]', icon_url=cmd.author.avatar_url or cmd.author.default_avatar_url)

        locales = {}
        if len(args) > 1:
            emb.title = '$[spoiler-title]'
            locales['title'] = args[1]

        await cmd.answer(emb, locales=locales)

    def can_delete_msg(self, server):
        self_member = server.get_member(self.bot.user.id)
        return self_member.server_permissions.manage_messages
