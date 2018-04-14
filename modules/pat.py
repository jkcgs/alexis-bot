import random
from bot.libs.configuration import yaml
from bot import Command, StaticConfig
from bot.utils import img_embed

default_pats = 'https://gist.github.com/jkcgs/137a28dc01b3e8538a253652f44eaf09/' \
               'raw/039dfdf76945915ad5d723d0031daa94d2e03e0b/pats.yml'


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

        if len(cmd.args) > 0:
            mention = await cmd.get_user(cmd.text)
            if mention is None:
                await cmd.answer('usuario no encontrado. Formato: !pat [@usuario]')
                return

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
        else:
            url = random.choice(self.config['pats'])
            text = '{}, toma una palmadita :3'.format(cmd.author_name)

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
