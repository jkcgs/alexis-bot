from bot import Command, categories
import urllib.parse as urlparse
from discord import Embed


class Weather(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'weather'
        self.aliases = ['clima']
        self.help = '$[weather-help]'
        self.format = '$[weather-format]'
        self.category = categories.INFORMATION
        self.urlbase = 'http://api.openweathermap.org/data/2.5/weather?q='
        self.default_config = {
            'weatherapi_key': ''
        }

        self.enabled = True

    def on_loaded(self):
        if self.bot.config['weatherapi_key'] == '':
            self.log.warn('Weather API key not set. Add the \'weatherapi_key\' to the settings.')

    async def handle(self, cmd):
        if self.bot.config['weatherapi_key'] == '':
            await cmd.answer('$[weather-error-not-set]')
            return

        if cmd.argc < 1:
            await cmd.answer('$[format]: $[weather-format]')
            return

        place = urlparse.quote(cmd.text)
        lang = cmd.lang.lang[0:2]
        url = '{}{}&units=metric&lang={}&APPID={}'.format(self.urlbase, place, lang, self.bot.config['weatherapi_key'])
        self.log.debug('Loading ' + url)

        await cmd.typing()
        async with self.http.get(url) as r:
            if r.status != 200:
                if r.status == 404:
                    await cmd.answer('$[weather-error-not-found]')
                    return
                if r.status == 401:
                    await cmd.answer('$[weather-error-key]')
                    return
                else:
                    await cmd.answer('$[weather-error]', locales={'error': r.status})
                    return

            data = await r.json()
            if 'deg' in data['wind']:
                wind = '{} m/s ({}º)'.format(data['wind']['speed'], data['wind']['deg'])
            else:
                wind = '{} m/s'.format(data['wind']['speed'])

            e = Embed(colour=12608321)
            e.description = ':flag_{}: $[weather-title]'.format(data['sys']['country'].lower())
            e.set_footer(text='$[weather-footer] (https://openweathermap.org/)',
                         icon_url='https://openweathermap.org/themes/openweathermap/'
                                  'assets/vendor/owm/img/icons/logo_60x60.png')
            e.add_field(name='$[weather-f-status]', value=data['weather'][0]['description'])
            e.add_field(name='$[weather-f-temp]', value='{} ºC'.format(data['main']['temp']))
            e.add_field(name='$[weather-f-pressure]', value='{} hPa'.format(data['main']['pressure']))
            e.add_field(name='$[weather-f-humidity]', value='{}%'.format(data['main']['humidity']))
            e.add_field(name='$[weather-f-wind]', value=wind)
            e.add_field(name='$[weather-f-clouds]', value='{}%'.format(data['clouds']['all']))
            e.set_thumbnail(url='http://openweathermap.org/img/w/{}.png'.format(data['weather'][0]['icon']))
            await cmd.answer(embed=e, locales={'location': data['name']})
