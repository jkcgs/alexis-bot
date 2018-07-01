import re

import discord

from bot import Command

pat_code = re.compile('^[a-zA-Z0-9]{8,20}$')
api_base = 'https://correos.owo.cl/{}'


class Correos(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'correos'
        self.help = 'Tracking para el sistema de envíos de Correos de Chile'

    async def handle(self, evt):
        if evt.argc == 0:
            await evt.answer('formato: $CMD <código>')
            return

        if not evt.is_pm:
            try:
                await self.bot.delete_message(evt.message)
            except discord.Forbidden:
                pass

            await evt.answer('el comando **$CMD** solo puede ser ejecutado vía PM')
            return

        if not pat_code.match(evt.args[0]):
            await evt.answer('código incorrecto')
            return

        await evt.typing()
        async with self.http.get(api_base.format(evt.args[0])) as req:
            data = await req.json()
            if 'error' in data:
                if data['error'] == 404:
                    await evt.answer('código no encontrado')
                else:
                    await evt.answer('error: {}'.format(data['message']))

                return

            last_entry = data['entries'][0]
            desc = '{} *({})*\n**Lugar**: {}'.format(last_entry['status'], last_entry['datetime'], last_entry['place'])
            await evt.answer_embed(desc, 'Estado envío')
