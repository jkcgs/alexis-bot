import random
from bot.libs.configuration import yaml
from bot import Command, StaticConfig, categories
from bot.utils import img_embed

default_pats = 'https://l.owo.cl/default_pats'


class Pat(Command):

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'pat'
        self.help = '$[pat-help]'
        self.category = categories.IMAGES
        self.config = None

    async def handle(self, cmd):
        if self.config is None:
            await cmd.answer('$[command-not-available]')
            return

        mention = None
        if len(cmd.args) > 0:
            mention = cmd.get_member_or_author(cmd.text)
            if mention is None:
                await cmd.answer('$[user-not-found]. $[format]: $[pat-format]')
                return

            text = '$[pat-to-user-2]'
            if mention.id == cmd.author.id:
                url = random.choice(self.config['self_pats'])
            elif mention.id == self.bot.user.id:
                url = self.config['bot_pat']
                text = '$[pat-to-bot]'
            else:
                url = random.choice(self.config['pats'])
        else:
            url = random.choice(self.config['pats'])
            text = '$[pat-to-user]'

        await cmd.answer(embed=img_embed(url, text), withname=False, locales={
            'user_to': mention.display_name if mention is not None else None,
            'user_from': cmd.author.display_name
        })

    async def on_ready(self):
        self.log.debug('Loading pats...')
        if not StaticConfig.exists('pats'):
            self.log.debug('Loading remote default pats')
            async with self.http.get(default_pats) as r:
                data = await r.text()
                defaults = yaml.load(data)
        else:
            defaults = {
                'pats': [],
                'self_pats': [],
                'bot_pat': 'http://i.imgur.com/tVzapCY.gif'
            }

        self.config = StaticConfig.get_config('pats', defaults)
        self.log.debug('Pats loaded')
