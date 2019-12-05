from bot import Command
from bot.utils import img_embed

from urllib.parse import urlencode

base_url = 'https://nekos.life/api/v2/'


class NekosLife(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'nekos'
        self.help = '$[nekos-help]'
        self.format = '$[nekos-format]'
        self.nsfw_only = True

        self.img_types = []

    async def on_ready(self):
        # Load possible image endpoints (image types)
        url = base_url + 'endpoints'
        self.log.info('Loading nekos.life endpoints from %s ...', url)

        async with self.http.get(url) as r:
            data = await r.json()
            if not isinstance(data, list):
                self.log.warn('Invalid data received for nekos.life endpoints')
                return

            # Look for image endpoints
            for ep in data:
                if '/api/v2/img/' in ep:
                    self.img_types = [
                        t[2:-1] for t in ep.split('<')[1][:-1].split(',')
                        if t[2:-1] not in ['v3', 'nekoapi_v3.1']
                    ]
                    break

            # Check if types were retrieved
            if len(self.img_types) == 0:
                self.log.warn('No image types were retrieved')
            else:
                self.log.info('%i image types were found', len(self.img_types))

    async def handle(self, cmd):
        # no subcmd or help
        if cmd.argc == 0 or cmd.args[0] == 'help':
            if len(self.img_types) == 0:
                await cmd.answer('$[nekos-no-types]')
            else:
                await cmd.answer('$[nekos-types]', locales={'image_types': ', '.join(self.img_types)})

            return

        # check valid image type
        if cmd.args[0] not in self.img_types:
            await cmd.answer('$[nekos-invalid-type]')
            return

        # send image
        url = base_url + 'img/' + cmd.args[0]
        self.log.debug('Loading %s ...', url)

        await cmd.typing()
        async with self.http.get(url) as r:
            data = await r.json()
            if 'url' not in data:
                await cmd.answer('$[nekos-invalid-response]')
            else:
                await cmd.answer(img_embed(data['url']))


class OwOify(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'owoify'
        self.help = '$[nekos-owoify-help]'
        self.format = '$[nekos-owoify-format]'

    async def handle(self, cmd):
        # filter text and check its length
        text = cmd.no_tags()
        if cmd.argc == 0 or len(text) > 200:
            await cmd.answer('$[nekos-owoify-length-error]')
            return

        # get converted text from api
        url = base_url + 'owoify?' + urlencode({'text': text})
        await cmd.typing()
        async with self.http.get(url) as r:
            data = await r.json()

            if 'msg' in data:
                await cmd.answer('$[nekos-owoify-error]', locales={'error_msg': data['msg']})
            elif 'owo' in data:
                await cmd.answer(data['owo'], withname=True)
            else:
                await cmd.answer('$[nekos-invalid-response]')
