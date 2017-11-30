from modules.base.command import Command
import urllib.parse as urlparse
from discord import Embed


class Weather(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'weather'
        self.aliases = ['clima']
        self.help = 'Entrega información del clima'
        self.urlbase = 'http://api.openweathermap.org/data/2.5/weather?q='

        self.enabled = True
        if 'weatherapi_key' not in bot.config or bot.config['weatherapi_key'].strip() == '':
            self.log.warning('API Key de clima no configurado, comando desactivado')
            self.enabled = False

    async def handle(self, message, cmd):
        if not self.enabled:
            return

        if len(cmd.args) < 1:
            await cmd.answer('Formato: !clima <lugar>')
            return

        place = urlparse.quote(cmd.text)
        url = '{}{}&units=metric&lang=es&APPID={}'.format(self.urlbase, place, self.bot.config['weatherapi_key'])
        self.log.debug('cargando ' + url)

        await cmd.typing()
        async with self.http.get(url) as r:
            if r.status != 200:
                if r.status == 404:
                    await cmd.answer('Lugar no encontrado')
                    return
                if r.status == 401:
                    await cmd.answer('La API key no funciona D:')
                    return
                else:
                    await cmd.answer('Error desconocido uwu')
                    return

            data = await r.json()
            e = Embed()
            e.description = ':flag_{}: Clima de **{}**'.format(data['sys']['country'].lower(), data['name'])
            e.add_field(name='Clima', value=data['weather'][0]['description'])
            e.add_field(name='Temperatura', value='{} ºC'.format(data['main']['temp']))
            e.add_field(name='Presión atmosférica', value='{} hPa'.format(data['main']['pressure']))
            e.add_field(name='Humedad', value='{}%'.format(data['main']['humidity']))
            e.add_field(name='Viento', value='{} m/s ({}º)'.format(data['wind']['speed'], data['wind']['deg']))
            e.add_field(name='Nubosidad', value='{}%'.format(data['clouds']['all']))
            e.set_thumbnail(url='http://openweathermap.org/img/w/{}.png'.format(data['weather'][0]['icon']))
            await cmd.answer(embed=e)
