from urllib.parse import urlencode
from os import path
import yaml

from modules.logger import log
from modules.base.command import Command


class SimSimiException(Exception):
    pass


class SimSimi:
    # Code stripped from:
    # https://github.com/six519/python-simsimi/blob/8192957936da1cba8b184785954a43e92b9ac03f/python_simsimi/simsimi.py

    def __init__(self, **kwargs):
        self.conversation_key = kwargs.get('conversation_key', '')
        self.conversation_language = kwargs.get('conversation_language', 'es')
        self.conversation_filter = kwargs.get('conversation_filter', '0.0')
        self.http = kwargs.get('http_session')

        if kwargs.get('is_trial', True):
            self.conversation_request_url = 'http://sandbox.api.simsimi.com/request.p'
        else:
            self.conversation_request_url = 'http://api.simsimi.com/request.p'

    async def get_conversation(self, text):
        request_param = {
            'key': self.conversation_key,
            'lc': self.conversation_language,
            'ft': self.conversation_filter,
            'text': text
        }

        request_url = "{}?{}".format(self.conversation_request_url, urlencode(request_param))
        log.debug('Cargando url ' + request_url)
        async with self.http.get(request_url) as r:
            response_dict = await r.json()

        if response_dict['result'] != 100:
            raise SimSimiException('Error: {}'.format(response_dict['msg']))

        return response_dict


class SimSimiCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'simsimi'
        self.help = 'Habla con SimSimi'
        self.user_delay = 5
        self.allow_pm = False
        self.config = self.load_config()
        self.sim = None
        self.enabled = True

        if self.config['api_key'] == '':
            self.log.warn('API KEY no definida para SimSimi, no será activado.')
        else:
            self.sim = SimSimi(conversation_key=self.config['api_key'], http_session=self.http,
                               is_trial=self.config['is_trial'])

    async def handle(self, message, cmd):
        if self.sim is None or cmd.text == '' or not self.enabled:
            return

        if cmd.text in ['off', 'on'] and cmd.owner:
            self.enabled = cmd.text == 'on'
            await cmd.answer('ya')
            return

        await cmd.typing()
        try:
            resp = await self.sim.get_conversation(cmd.text)
            await cmd.answer(resp.get('response', 'no c bro discupa'))
        except SimSimiException as e:
            await cmd.answer('el coso tiró un error: ' + str(e))

    def load_config(self):
        try:
            config_path = path.join(path.dirname(path.realpath(__file__)), 'config.yml')
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)

            if config is None:
                config = {}

            res_config = {
                'api_key': config.get('api_key', ''),
                'lang_code': config.get('lang_code', 'es'),
                'is_trial': config.get('is_trial', True)
            }
            return res_config
        except Exception as ex:
            self.log.exception(ex)
            return {
                'api_key': '',
                'lang_code': 'es',
                'is_trial': True
            }


