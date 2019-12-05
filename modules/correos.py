import re

import discord

from bot import Command, categories

pat_code = re.compile('^[a-zA-Z0-9]{8,20}$')
api_base = 'https://api.owo.cl/correos/{}'


class Correos(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'correos'
        self.help = '$[correos-help]'
        self.format = '$[correos-format]'
        self.category = categories.INFORMATION

    async def handle(self, evt):
        if evt.argc == 0:
            await evt.answer('$[format]: $[correos-format]')
            return

        if not evt.is_pm:
            try:
                await self.bot.delete_message(evt.message, silent=True)
            except discord.Forbidden:
                pass

            await evt.answer('$[correos-error-pm]')
            return

        if not pat_code.match(evt.args[0]):
            await evt.answer('$[correos-invalid-code]')
            return

        await evt.typing()
        async with self.http.get(api_base.format(evt.args[0])) as req:
            data = await req.json()
            if 'error' in data:
                if data['error'] == 404:
                    await evt.answer('$[correos-code-notfound]')
                else:
                    await evt.answer('$[correos-error]', locales={'error': data['message']})

                return

            last_entry = data['entries'][0]
            desc = '{} *({})*\n**$[correos-location]**: {}'.format(
                last_entry['status'], last_entry['datetime'], last_entry['place'])
            await evt.answer_embed(desc, '$[correos-title]')
