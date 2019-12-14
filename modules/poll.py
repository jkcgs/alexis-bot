from bot import Command, categories
from discord import Embed

import json


class Poll(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'poll'
        self.aliases = ['encuesta', 'strawpoll']
        self.help = '$[poll-help]'
        self.format = '$[poll-format]'
        self.category = categories.UTILITY

        self.default_config = {
            'polls_max_options': 6
        }

    async def handle(self, cmd):
        max_options = self.bot.config.get('polls_max_options', 6)
        args = [x.strip() for x in cmd.text.split('|') if x.strip() != '']

        if len(args) <= 2:
            await cmd.answer('$[format]: $[poll-format]')
            return
        elif len(args) >= max_options:
            await cmd.answer('$[poll-error-max]', locales={'max': max_options})
            return

        op = json.dumps({'title': args[0], 'options': args[1:]})
        head = {'Content-Type': 'application/json'}
        await cmd.typing()

        async with self.http.post(url='https://www.strawpoll.me/api/v2/polls', data=op, headers=head) as poll_response:
            x = await poll_response.json()
            option_list = ''
            for options in x['options']:
                option_list += '- {}\n'.format(options)

            embed = Embed(title='StrawPoll: {}'.format(x['title']), color=0xFFD756)
            embed.set_thumbnail(url='https://pbs.twimg.com/profile_images/737742455643070465/yNKcnrSA_400x400.jpg')
            embed.url = 'https://www.strawpoll.me/{}'.format(x['id'])
            embed.description = '$[poll-options]:\n{}'.format(option_list)
            await cmd.answer(embed=embed)
            return
