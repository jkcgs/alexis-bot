from aiohttp import ClientSession, ContentTypeError
from bot import Command, categories, BotMentionEvent


class SimSimiException(Exception):
    def __init__(self, msg=None, code=None):
        super().__init__(msg)
        self.code = code


class SimSimiCmd(Command):
    __version__ = '1.0.1'
    __author__ = 'makzk'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'simsimi'
        self.aliases = ['s']
        self.help = '$[simsimi-help]'
        self.category = categories.FUN
        self.user_delay = 5
        self.allow_pm = False
        self.mention_handler = True
        self.enabled = False
        self.default_config = {
            'simsimi_apikey': '',
            'simsimi_lang': 'es'
        }

    def on_loaded(self):
        if not self.bot.config.get('simsimi_apikey', ''):
            self.log.warn('No API keys added for SimSimi, you can add them to the simsimi_apikeys value on the config.')
        self.enabled = True

    async def handle(self, cmd):
        first = cmd.args[0] if len(cmd.args) > 0 else ''
        if not first:
            return

        if isinstance(cmd, BotMentionEvent) and (not cmd.starts_with or first == 'prefix'):
            return

        if not self.enabled:
            await cmd.answer('$[simsimi-not-available]')
            return

        if cmd.text in ['off', 'on'] and cmd.owner:
            await self.handle_toggle(cmd)
            return

        await self.handle_talk(cmd)

    async def handle_toggle(self, cmd):
        if not self.key:
            await cmd.answer('$[simsimi-no-apikey]')
            return

        self.enabled = cmd.text == 'on'
        await cmd.answer('ok')

    async def handle_talk(self, cmd):
        await cmd.typing()

        try:
            lang = cmd.lng('simsimi-lang') or self.lang
            country = cmd.lng('simsimi-country') or None
            message = cmd.no_tags()
            self.log.debug('Received message: "%s"', message)
            resp = await self.talk(cmd.channel, lang, country, message)
            await cmd.answer(resp or '$[simsimi-no-answer]', withname=False)
        except SimSimiException as e:
            if e.code == 228:
                await cmd.answer(':speech_balloon: $[simsimi-do-not-understand]', withname=False)
            else:
                await cmd.answer('$[simsimi-error]', locales={'error': str(e)})
        except ContentTypeError as e:
            await cmd.answer('⚠️ $[simsimi-cant-answer]')
            self.log.exception(e)

    @property
    def key(self):
        return self.bot.config['simsimi_apikey']

    @property
    def lang(self):
        return self.bot.config['simsimi_lang']

    _sessions = {}
    api_url = 'https://wsapi.simsimi.com/190410/talk'

    def get_session(self, channel=None):
        channelid = 'global' if not channel else channel.id
        if channelid not in self._sessions:
            self._sessions[channelid] = ClientSession(headers={'x-api-key': self.key})
        return self._sessions[channelid]

    async def talk(self, channel, language, country, text):
        session = self.get_session(channel)
        data = {'lang': language, 'utext': text}
        if country:
            data['country'] = country if isinstance(country, list) else [country]

        async with session.post(self.api_url, json=data) as r:
            resp = await r.json()

        if resp['status'] != 200:
            raise SimSimiException(resp['statusMessage'], resp['status'])

        return ':speech_balloon: ' + resp['atext']

    def load_config(self):
        self.on_loaded()
