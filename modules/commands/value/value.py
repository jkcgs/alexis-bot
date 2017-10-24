from os import path

import yaml

from modules.base.command import Command
import re


class Value(Command):
    rx_div = re.compile('^([A-Z]{3}|UF)$')
    rx_num = re.compile('^\d+(\.|,\d+)?$')
    baseurl = 'https://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20yahoo.finance.xchange' \
              '%20where%20pair%20in%20(%22{}{}%22)&format=json' \
              '&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback='
    baseurl_uf = 'http://api.sbif.cl/api-sbifv3/recursos_api/{}?apikey={}&formato=json'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['value', 'valor', 'uf', 'utm']
        self.help = 'Entrega datos de conversión de divisas'
        self.config = self.load_config()

    async def handle(self, message, cmd):
        if len(cmd.args) < 2 and cmd.cmdname not in ['uf', 'utm']:
            await self.formato(cmd)
            return

        cant = '1'
        div2 = 'usd'

        if cmd.cmdname in ['uf', 'utm']:
            div1 = cmd.cmdname.upper()
            if cmd.argc == 0:
                div2 = 'CLP'
                cant = '1'
            elif cmd.argc == 1:  # !uf [cant|divisa]
                if Value.rx_num.match(cmd.args[0]):
                    cant = cmd.args[0]
                    div2 = 'CLP'
                else:
                    cant = '1'
                    div2 = cmd.args[0]
            elif 2 <= cmd.argc <= 3:  # !uf cant [(a|to)] divisa
                if not Value.rx_num.match(cmd.args[0]):
                    await self.formato(cmd)
                    return

                cant = cmd.args[0]
                if cmd.argc == 3:  # !uf cant (a|to) divisa
                    if cmd.args[1] not in ['a', 'to']:
                        await self.formato(cmd)
                        return
                    else:
                        div2 = cmd.args[2]
                else:  # !uf cant divisa
                    div2 = cmd.args1
        elif cmd.argc == 2:
            div1 = cmd.args[0].upper()
            div2 = cmd.args[1].upper()
            cant = '1'
        elif cmd.argc == 3:
            if cmd.args[1].lower() in ['a', 'to']:
                div1 = cmd.args[0].upper()
                div2 = cmd.args[2].upper()
                cant = '1'
            else:
                cant = cmd.args[0]
                div1 = cmd.args[1].upper()
                div2 = cmd.args[2].upper()
        else:
            if cmd.args[2].lower() in ['a', 'to']:
                cant = cmd.args[0]
                div1 = cmd.args[1].upper()
                div2 = cmd.args[3].upper()
            else:
                cant = cmd.args[0]
                div1 = cmd.args[1].upper()
                div2 = cmd.args[2].upper()

        if not Value.rx_div.match(div1) or not self.rx_div.match(div2):
            self.log.debug('divisas incorrectas: %s, %s', div1, div2)
            await cmd.answer('Formato de divisas incorrecto')
            return

        try:
            cant = float(cant.replace(',', '.'))
        except ValueError:
            await cmd.answer('Formato incorrecto de valor a convertir')
            return

        await cmd.typing()

        try:
            if div1 in ['UF', 'UTM']:
                if self.config is None or self.config['sbif_apikey'] == '':
                    cmd.answer('La información de {} no está disponible'.format(div1))
                else:
                    value = await self.sbif(div1.lower())
                    if cant == 1:
                        await cmd.answer('La {} está a **$ {}**'.format(div1, value))
                    else:
                        await cmd.answer('{} {} son **$ {}**'.format(cant, div1, value*cant))
            else:
                value = await self.convert(div1, div2)
                await cmd.answer('**{} {}** son **{} {}**'.format(cant, div1, cant * value, div2))
        except DivRetrievalError as e:
            await cmd.answer('no pude obtener los datos de divisas D:\n```{}```'.format(str(e)))

    async def formato(self, cmd):
        await cmd.answer('Formato: !value [cantidad] <divisa1> [a] <divisa2>\n'
                         '!uf [cantidad] [a] <divisa2>\n'
                         '!utm [cantidad] [a] <divisa2>')

    async def convert(self, div1, div2):
        attempts = 0
        while attempts < 10:
            self.log.debug('Cargando datos de divisa, intento ' + str(attempts + 1))
            async with self.http.get(Value.baseurl.format(div1, div2)) as r:
                data = await r.json()
                if r.status != 200:
                    attempts += 1
                    continue

                try:
                    value = float(data['query']['results']['rate']['Rate'])
                except (KeyError, ValueError):
                    raise DivRetrievalError('no pude obtener los datos de divisas D:')

                return value

    async def sbif(self, api):
        attempts = 0
        url = Value.baseurl_uf.format(api, self.config['sbif_apikey'])

        while attempts < 10:
            async with self.http.get(url) as r:
                data = await r.json()

                if r.status != 200:
                    attempts += 1
                    continue

                try:
                    campo = api.upper() + 's'
                    value = float(data[campo][0]['Valor'].replace('.', '').replace(',', '.'))
                except (KeyError, ValueError):
                    raise DivRetrievalError('no pude obtener los datos de divisas (UF) D:')

                return value

    def load_config(self):
        try:
            config_path = path.join(path.dirname(path.realpath(__file__)), 'value.yml')
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)

            if 'sbif_apikey' not in config or config['sbif_apikey'].strip() == '':
                config['sbif_apikey'] = ''

            return config
        except FileNotFoundError:
            self.log.warning('No existe el archivo de configuración de !value. '
                             'La información de UF y UTM no estará disponible.')
            return None
        except Exception as ex:
            self.log.exception(ex)
            return None


class DivRetrievalError(BaseException):
    pass
