from commands.base.command import Command
from discord import Embed

import json


class Ping(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['poll', 'encuesta', 'strawpoll']
        self.help = 'Crea una encuesta en strawpoll.me . Separa el título y las opciones con " | "'

    async def handle(self, message, cmd):
        args = []
        max_opciones = 6
        for x in cmd.text.split("|"):
            x.strip('')
            args.append(x)
        if len(args) == 1:
            await cmd.answer('Uso: !poll <Título> | <Opción 1> | <Opción 2> [| <Opción ...> | <Opción {}>]'.format(max_opciones))
            return
        elif len(args) == 1:
            await cmd.answer('¡Necesitas ingresar opciones!')
            return
        elif len(args) == 2:
            await cmd.answer('¡Necesitas al menos 2 opciones!')
            return
        elif len(args) > max_opciones+1:
            await cmd.answer('¡Máximo 6 opciones!')
            return
        async with self.http.post(url='https://strawpoll.me/api/v2/polls',data=json.dumps({'title': args[0], 'options': args[1:]})) as poll_response:
            x = await poll_response.json()
            option_list = ''
            for options in x['options']:
                option_list += '- {}\n'.format(options)
            embed = Embed(title='StrawPoll: {}'.format(x['title']), color=0xFFD756)
            embed.set_thumbnail(url='https://pbs.twimg.com/profile_images/737742455643070465/yNKcnrSA_400x400.jpg')
            embed.url = 'https://strawpoll.me/{}'.format(x['id'])
            embed.description = 'Opciones:\n{}'.format(option_list)
            await cmd.answer(embed=embed)
            return
