import re

from bot import Command, categories
from bot.utils import is_float

pat_currency = re.compile('[a-zA-Z]{3}')
baseurl = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE' \
          '&from_currency={}&to_currency={}&apikey={}'
baseurl_sbif = 'https://api.sbif.cl/api-sbifv3/recursos_api/{}?apikey={}&formato=json'
cryptomemes = ['btc', 'xmr', 'eth', 'ltc']


class Value(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'value'
        self.aliases = ['uf', 'utm'] + cryptomemes
        self.help = 'Entrega datos de conversión de divisas'
        self.format = '!value [cantidad] <divisa1> <divisa2>'
        self.format_shortcut = '$CMD [cantidad] <divisa2>'
        self.category = categories.INFORMATION
        self.default_config = {
            'sbif_apikey': '',
            'currency_apikey': ''
        }

        self.div_handlers = {
            'UTM': self.handler_utm,
            'UF': self.handler_uf
        }

        self.div_defaults = {
            'UTM': 'CLP',
            'UF': 'CLP'
        }

        for m in cryptomemes:
            self.div_defaults[m.upper()] = 'USD'

    async def handle(self, cmd):
        div_from = 'USD'
        div_to = 'EUR'
        mult = 1

        if cmd.cmdname != self.name:
            div_from = cmd.cmdname.rstrip('2').upper()
            if div_from in self.div_defaults.keys():
                div_to = self.div_defaults[div_from]

            if cmd.argc >= 1:
                if is_float(cmd.args[0]):
                    mult = float(cmd.args[0])

                    if cmd.argc > 1 and self.valid_currency(cmd.args[1]):
                        div_to = cmd.args[1]
                else:
                    div_to = cmd.args[0]
        else:
            if cmd.argc == 1:
                if not self.valid_currency(cmd.args[0]):
                    await cmd.answer('formato incorrecto [2]. Formato: `{}`'.format(self.format))
                    return

                div_from = cmd.args[0].upper()
                if div_from not in self.div_defaults.keys():
                    await cmd.answer('formato incorrecto [3]. Formato: `{}`'.format(self.format))
                    return

                div_to = self.div_defaults[div_from]

            elif cmd.argc == 2:
                if (is_float(cmd.args[0]) and not is_float(cmd.args[1])) \
                        or (is_float(cmd.args[1]) and not is_float(cmd.args[2])):
                    mult = float(cmd.args[0]) if is_float(cmd.args[0]) else float(cmd.args[1])
                    div_from = cmd.args[1].upper() if is_float(cmd.args[0]) else cmd.args[0].upper()

                    if not self.valid_currency(div_from):
                        await cmd.answer('formato incorrecto [4]. Formato: `{}`'.format(self.format))
                        return

                    if div_from not in self.div_defaults.keys():
                        await cmd.answer('formato incorrecto [5]. Formato: `{}`'.format(self.format))
                        return

                    div_to = self.div_defaults[div_from]
                else:
                    div_from = cmd.args[0]
                    div_to = cmd.args[1]

            elif cmd.argc >= 3:
                if not is_float(cmd.args[0]):
                    await cmd.answer('formato incorrecto [4]. Formato: `{}`'.format(self.format))
                    return
                mult = float(cmd.args[0].replace(',', '.'))
                div_from = cmd.args[1]
                div_to = cmd.args[2]

        if not self.valid_currency(div_from) or not self.valid_currency(div_to):
            await cmd.answer('Divisa incorrecta. Formato: `{}`'.format(self.format))
            return

        try:
            div_from = div_from.upper()
            div_to = div_to.upper()

            await cmd.typing()
            if div_from in self.div_handlers.keys():
                result = await self.div_handlers[div_from](div_to, mult)
            else:
                result = await self.handler(div_from, div_to, mult)
        except DivRetrievalError as e:
            await cmd.answer('error: ' + str(e))
            return

        precision = 5 if result < 1 else 2
        result = '{:.{prec}f}'.format(result, prec=precision)
        await cmd.answer('{mult} {dfrom} = **{result}** {to}'.format(
            dfrom=div_from, to=div_to, mult=mult, result=result))

    async def handler_utm(self, dv_to, mult):
        val = await self.sbif('UTM')
        return await self.handler('CLP', dv_to, mult * val)

    async def handler_uf(self, dv_to, mult):
        val = await self.sbif('UF')
        return await self.handler('CLP', dv_to, mult * val)

    async def handler(self, dv_from, dv_to, mult):
        if dv_from == dv_to:
            return mult
        else:
            return await self.convert(dv_from, dv_to) * mult

    #
    # Services readers
    #

    async def convert(self, div1, div2):
        if self.bot.config['currency_apikey'] == '':
            raise DivRetrievalError('La API key de conversión de divisas no está configurada')

        attempts = 0
        url = baseurl.format(div1, div2, self.bot.config['currency_apikey'])
        while attempts < 10:
            self.log.debug('Cargando datos de divisa, intento ' + str(attempts + 1))
            self.log.debug('Cargando url %s', url)
            async with self.http.get(url) as r:
                data = await r.json()
                if r.status != 200:
                    attempts += 1
                    continue

                try:
                    k = 'Realtime Currency Exchange Rate'
                    if k not in data.keys():
                        if 'Error Message' in data.keys() and data['Error Message'].startswith('Invalid API call.'):
                            raise DivRetrievalError('Divisa incorrecta')
                        else:
                            raise DivRetrievalError('Formato de respuesta no esperada')
                    else:
                        j = '5. Exchange Rate'
                        if j not in data[k].keys():
                            raise DivRetrievalError('Formato de respuesta no esperada')

                        value = float(data[k][j])
                except ValueError as e:
                    self.log.exception(e)
                    raise DivRetrievalError('El valor de las divisas no está disponible')

                return value

    async def sbif(self, api):
        # TODO: Cache
        attempts = 0
        if self.bot.config['sbif_apikey'] == '':
            raise DivRetrievalError('La API key de SBIF no está configurada')

        url = baseurl_sbif.format(api.lower(), self.bot.config['sbif_apikey'])

        while attempts < 10:
            async with self.http.get(url) as r:
                try:
                    data = await r.json(content_type='text/json')
                except TypeError:
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

    def valid_currency(self, curr):
        if not isinstance(curr, str):
            return False

        curr = curr.upper()
        return curr in self.div_handlers.keys() or pat_currency.match(curr)


class DivRetrievalError(BaseException):
    pass
