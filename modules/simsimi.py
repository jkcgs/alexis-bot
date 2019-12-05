from urllib.parse import urlencode

from bot import Command, categories


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
        async with self.http.get(request_url) as r:
            response_dict = await r.json()

        if response_dict['result'] != 100:
            raise SimSimiException(response_dict['msg'])

        return response_dict


class SimSimiCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'simsimi'
        self.aliases = ['s']
        self.help = '$[simsimi-help]'
        self.category = categories.FUN
        self.user_delay = 5
        self.allow_pm = False
        self.enabled = True
        self.key_index = 0
        self.default_config = {
            'simsimi_apikeys': [],
            'simsimi_lang': 'es'
        }

    def on_loaded(self):
        if len(self.bot.config['simsimi_apikeys']) == 0:
            self.log.warn('No API keys added for SimSimi, you can add them to the simsimi_apikeys value on the config.')

    async def handle(self, cmd):
        if cmd.text == '':
            return

        if len(self.bot.config['simsimi_apikeys']) == 0:
            await cmd.answer('$[simsimi-not-available]')
            return

        if cmd.text in ['off', 'on'] and cmd.owner:
            self.enabled = cmd.text == 'on'
            await cmd.answer('ok')
            return

        await cmd.typing()
        start_index = self.key_index

        while True:
            try:
                sim = self.get_bot(lang=cmd.config.get('simsimi_lang', self.bot.config['simsimi_lang']))
                if sim is None:
                    await cmd.answer('$[simsimi-no-apikeys]')
                    break

                resp = await sim.get_conversation(cmd.no_tags())
                await cmd.answer(resp.get('response', '$[simsimi-no-answer]'))
                break
            except SimSimiException as e:
                if str(e) == 'Daily Request Query Limit Exceeded.'\
                        or str(e) == 'Unauthorized'\
                        or str(e) == 'Trial app is expired.':
                    if self.key_index + 1 >= len(self.bot.config['simsimi_apikeys']):
                        self.key_index = 0
                    else:
                        self.key_index += 1

                    if self.key_index == start_index:
                        await cmd.answer('$[simsimi-no-apicalls]')
                        break
                else:
                    await cmd.answer('$[simsimi-error]', locales={'error': str(e)})
                    break

    def get_bot(self, lang):
        keys = self.get_keys()

        if not self.enabled:
            return None

        key = keys[self.key_index].get('key', '')
        is_trial = keys[self.key_index].get('is_trial', True)
        if key == '':
            return None

        return SimSimi(conversation_key=key, http_session=self.http, is_trial=is_trial, conversation_language=lang)

    def get_keys(self):
        return self.bot.config.get('simsimi_apikeys', [])

    def load_config(self):
        self.on_loaded()
