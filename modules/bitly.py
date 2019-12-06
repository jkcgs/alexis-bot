from discord import Embed

from bot import Command

api_url = 'https://api-ssl.bitly.com/v4/shorten'
protocols = ['http://', 'https://', 'magnet:']


class Bitly(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'bitly'
        self.help = '$[bitly-help]'
        self.format = '$[bitly-format]'
        self.owner_only = True
        self.user_delay = 30
        self.default_config = {
            'bitly_key': '',
            'bitly_domain': 'bit.ly',
            'bitly_min_length': 25
        }

    async def handle(self, cmd):
        if cmd.argc == 0:
            await cmd.answer('$[format]: $[bitly-format]')
            return

        min_length = self.bot.config.get('bitly_min_length', 25)
        long_url = cmd.text
        appended = False
        if not long_url.startswith(tuple(api_url)):
            appended = True
            long_url = 'https://' + long_url

        if len(long_url) < min_length:
            msg = ['$[bitly-err-len]', '$[bitly-err-len-prepend]'][appended]
            await cmd.answer(msg, locales={'min_length': min_length, 'current_length': len(long_url)})
            return

        await cmd.typing()

        try:
            link = await self.create(self, long_url)

            emb = Embed(title='$[bitly-title]', description=link)
            emb.set_footer(text='$[answer-for]', icon_url=str(cmd.author.avatar_url))
            await cmd.answer(emb, locales={'author': cmd.author.display_name})
        except RuntimeError as e:
            await cmd.answer('$[bitly-err-config]', locales={'error_text': str(e)})
        except ValueError as e:
            await cmd.answer('$[bitly-err]', locales={'error_text': str(e)})

    @staticmethod
    async def create(ins, long_url):
        if ins.bot.config.get('bitly_key', '').strip() == '':
            raise RuntimeError('$[bitly-err-no-key]')

        payload = {
            'domain': ins.bot.config.get('bitly_domain', 'bit.ly'),
            'long_url': long_url
        }

        key = 'Bearer ' + ins.bot.config['bitly_key']

        async with ins.http.post(api_url, json=payload, headers={'Authorization': key}) as r:
            data = await r.json()
            if r.status not in [200, 201]:
                if r.status == 403:
                    raise RuntimeError('$[bitly-err-forbidden]')
                if r.status == 400 and data['message'] == 'INVALID_ARG_LONG_URL':
                    raise RuntimeError('$[bitly-err-url]')

                ins.log.error('Invalid status code while trying to create a bitlink: %i', r.status)
                ins.log.debug(data)
                if 'message' in data:
                    raise ValueError(ins.lang.format('$[bitly-err-status-msg]', locales={
                        'status_code': r.status, 'error_message': r['message']}))
                else:
                    raise ValueError(ins.lang.format('$[bitly-err-status]', locales={'status_code': r.status}))

            return data['link']
