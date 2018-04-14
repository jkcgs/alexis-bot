from bot import Command
import urllib.parse as urlparse
from discord import Embed


class Weather(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'weather'
        self.aliases = ['clima']
        self.help = 'Entrega información del clima'
        self.urlbase = 'http://api.openweathermap.org/data/2.5/weather?q='
        self.default_config = {
            'weatherapi_key': ''
        }

        self.enabled = True

    def on_loaded(self):
        if self.bot.config['weatherapi_key'] == '':
            self.log.warn('La API key del clima no está configurada. Puedes agregarla en el valor weatherapi_key de la'
                          'configuración')

    async def handle(self, cmd):
        if self.bot.config['weatherapi_key'] == '':
            await cmd.answer('este comando está desactivado debido a que no está configurado')
            return

        if cmd.argc < 1:
            await cmd.answer('formato: $PX$NM <lugar>')
            return

        place = urlparse.quote(cmd.text)
        url = '{}{}&units=metric&lang=es&APPID={}'.format(self.urlbase, place, self.bot.config['weatherapi_key'])
        self.log.debug('cargando ' + url)

        await cmd.typing()
        async with self.http.get(url) as r:
            if r.status != 200:
                if r.status == 404:
                    await cmd.answer('lugar no encontrado')
                    return
                if r.status == 401:
                    await cmd.answer('la API key no funciona D:')
                    return
                else:
                    await cmd.answer('error desconocido uwu ({})'.format(r.status))
                    return

            data = await r.json()
            if 'deg' in data['wind']:
                wind = '{} m/s ({}º)'.format(data['wind']['speed'], data['wind']['deg'])
            else:
                wind = '{} m/s'.format(data['wind']['speed'])

            e = Embed(colour=12608321)
            e.description = ':flag_{}: Clima de **{}**'.format(data['sys']['country'].lower(), data['name'])
            e.set_footer(text='Desde OpenWeatherMap (https://openweathermap.org/)',
                         icon_url='https://openweathermap.org/themes/openweathermap/'
                                  'assets/vendor/owm/img/icons/logo_60x60.png')
            e.add_field(name='Clima', value=data['weather'][0]['description'])
            e.add_field(name='Temperatura', value='{} ºC'.format(data['main']['temp']))
            e.add_field(name='Presión atmosférica', value='{} hPa'.format(data['main']['pressure']))
            e.add_field(name='Humedad', value='{}%'.format(data['main']['humidity']))
            e.add_field(name='Viento', value=wind)
            e.add_field(name='Nubosidad', value='{}%'.format(data['clouds']['all']))
            e.set_thumbnail(url='http://openweathermap.org/img/w/{}.png'.format(data['weather'][0]['icon']))
            await cmd.answer(embed=e)
