import random
from bot.libs.configuration import yaml
from os import path
from bot import Command, StaticConfig
from bot.utils import img_embed

default_pats = 'https://gist.github.com/jkcgs/137a28dc01b3e8538a253652f44eaf09/' \
               'raw/4d202bd98180703b6f4145c8995cdf5b09914b8e/pats.yml'


class Pat(Command):

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'pat'
        self.help = 'Te envía una imagen de animé de una caricia en la cabeza y algo más'
        self.config = None

    async def handle(self, cmd):
        if self.config is None:
            await cmd.answer('this is not working yet')
            return

        if len(cmd.args) != 1 or len(cmd.message.mentions) != 1:
            await cmd.answer('Formato: !pat <@mención>')
            return

        mention = cmd.message.mentions[0]
        text = '{}, {} te ha dado una palmadita :3'.format(
            mention.display_name, cmd.author_name
        )

        if mention.id == cmd.author.id:
            url = random.choice(self.config['self_pats'])
        elif mention.id == self.bot.user.id:
            url = self.config['bot_pat']
            text = 'oye nuuuu >_<'
        else:
            url = random.choice(self.config['pats'])

        await cmd.answer(embed=img_embed(url, text), withname=False)

    async def task(self):
        self.log.debug('[Pat] Cargando pats...')
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
