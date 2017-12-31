from os import path

import yaml

from alexis import Command
import random

from alexis.base.utils import img_embed


class Pat(Command):

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'pat'
        self.help = 'Te envía una imagen de animé de una caricia en la cabeza y algo más'
        self.config = {}
        self.load_config()

    async def handle(self, message, cmd):
        if len(cmd.args) != 1 or len(message.mentions) != 1:
            await cmd.answer('Formato: !pat <@mención>')
            return

        mention = message.mentions[0]
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

        await cmd.answer(embed=img_embed(url, text))

    def load_config(self):
        self.log.debug('[Pat] Cargando pats...')

        try:
            config_path = path.join(path.dirname(path.realpath(__file__)), 'pats.yml')
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            if config is None:
                raise Exception('La configuración está vacía')

            self.config = {
                'pats': config.get('pats', []),
                'self_pats': config.get('self_pats', []),
                'bot_pat': config.get('bot_pat', 'http://i.imgur.com/tVzapCY.gif')
            }
        except Exception as ex:
            self.log.exception(ex)
            self.config = {
                'pats': [],
                'self_pats': [],
                'bot_pat': 'http://i.imgur.com/tVzapCY.gif'
            }
