import re

from bot import Command, categories
from bot.utils import is_float

pat_currency = re.compile('[a-zA-Z]{3}')
baseurl = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE' \
          '&from_currency={}&to_currency={}&apikey={}'
baseurl_sbif = 'https://api.sbif.cl/api-sbifv3/recursos_api/{}?apikey={}&formato=json'

baseurl_orionx = 'https://ymxh3ju7n5.execute-api.us-east-1.amazonaws.com/client/graphql'

localsbif = ['uf', 'utm']
cryptomemes = ['btc', 'xmr', 'eth', 'ltc', 'xlm', 'xrp', 'bch', 'dash', 'doge']
cryptoclp = ['cha', 'luk']


class Value(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'value'
        self.aliases = localsbif + cryptomemes + cryptoclp
        self.help = '$[value-help]'
        self.format = '$[value-format]'
        self.format_shortcut = '$[value-format-short]'
        self.category = categories.INFORMATION
        self.default_config = {
            'sbif_apikey': '',
            'currency_apikey': ''
        }

        self.div_handlers = {}

        for m in cryptomemes:
            self.div_handlers[m.upper()] = (self.convert_crypto, 'USD')

        for m in localsbif:
            self.div_handlers[m.upper()] = (self.sbif, 'CLP')

        for m in cryptoclp:
            self.div_handlers[m.upper()] = (self.orionx, 'CLP')

    async def handle(self, cmd):
        div_from = 'USD'
        div_to = 'EUR'
        mult = 1

        if cmd.cmdname != self.name:
            div_from = cmd.cmdname.rstrip('2').upper()
            if div_from in self.div_handlers.keys():
                _, div_to = self.div_handlers[div_from]

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
                    await cmd.answer('$[value-error-currency] [2] $[format]: $[value-format]')
                    return

                div_from = cmd.args[0].upper()
                if div_from not in self.div_handlers.keys():
                    await cmd.answer('$[value-error-currency] [3] $[format]: $[value-format]')
                    return

                _, div_to = self.div_handlers[div_from]

            elif cmd.argc == 2:
                if (is_float(cmd.args[0]) and not is_float(cmd.args[1])) \
                        or (is_float(cmd.args[1]) and not is_float(cmd.args[2])):
                    mult = float(cmd.args[0]) if is_float(cmd.args[0]) else float(cmd.args[1])
                    div_from = cmd.args[1].upper() if is_float(cmd.args[0]) else cmd.args[0].upper()

                    if not self.valid_currency(div_from):
                        await cmd.answer('$[value-error-currency] [4] $[format]: $[value-format]')
                        return

                    if div_from not in self.div_handlers.keys():
                        await cmd.answer('$[value-error-currency] [5] $[format]: $[value-format]')
                        return

                    _, div_to = self.div_handlers[div_from]
                else:
                    div_from = cmd.args[0]
                    div_to = cmd.args[1]

            elif cmd.argc >= 3:
                if not is_float(cmd.args[0]):
                    await cmd.answer('$[value-error-currency] [6] $[format]: $[value-format]')
                    return
                mult = float(cmd.args[0].replace(',', '.'))
                div_from = cmd.args[1]
                div_to = cmd.args[2]

        if not self.valid_currency(div_from) or not self.valid_currency(div_to):
            await cmd.answer('$[value-error-currency] $[format]: $[value-format]')
            return

        try:
            div_from = div_from.upper()
            div_to = div_to.upper()

            await cmd.typing()
            result = await self.handler(div_from, div_to, mult)
        except DivRetrievalError as e:
            await cmd.answer('$[error]', locales={'errortext': str(e)})
            return

        precision = 5 if result < 1 else 2
        result = '{:.{prec}f}'.format(result, prec=precision)
        await cmd.answer('{mult} {dfrom} = **{result}** {to}'.format(
            dfrom=div_from, to=div_to, mult=mult, result=result))

    """
    Handles different types of currency supported by the different APIs connected here
    """
    async def handler(self, dv_from, dv_to, mult):
        if dv_from in self.div_handlers:
            handler, default_to = self.div_handlers[dv_from]
            val = await handler(dv_from)
            return await self.handler(default_to, dv_to, mult * val)

        if dv_from == dv_to:
            return mult

        return await self.convert(dv_from, dv_to) * mult

    #
    # Services readers
    #

    async def convert(self, div1, div2):
        if self.bot.config['currency_apikey'] == '':
            raise DivRetrievalError('$[value-error-apikey]')

        attempts = 0
        url = baseurl.format(div1, div2, self.bot.config['currency_apikey'])
        while attempts < 10:
            self.log.debug('Loading currency data, attempt ' + str(attempts + 1))
            self.log.debug('Loading URL %s', url)
            async with self.http.get(url) as r:
                data = await r.json()
                if r.status != 200:
                    attempts += 1
                    continue

                try:
                    k = 'Realtime Currency Exchange Rate'
                    if k not in data.keys():
                        if 'Error Message' in data.keys() and data['Error Message'].startswith('Invalid API call.'):
                            raise DivRetrievalError('$[value-error-currency]')
                        else:
                            raise DivRetrievalError('$[value-error-answer]')
                    else:
                        j = '5. Exchange Rate'
                        if j not in data[k].keys():
                            raise DivRetrievalError('$[value-error-answer]')

                        value = float(data[k][j])
                except ValueError as e:
                    self.log.exception(e)
                    raise DivRetrievalError('$[value-error-unavailable]')

                return value

    async def convert_crypto(self, meme):
        return await self.convert(meme, 'USD')

    async def sbif(self, api):
        # TODO: Cache
        attempts = 0
        if self.bot.config['sbif_apikey'] == '':
            raise DivRetrievalError('$[value-error-sbif-key]')

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
                    raise DivRetrievalError('$[value-error-sbif]')

                return value

    async def orionx(self, meme):
        q = [{
            "query": "query getMarketStatsHome($x:ID){market(code:$x){lastTrade{price}}}",
            "variables": {"x": meme + "CLP"}
        }]

        self.log.debug('Loading url %s for %s', baseurl_orionx, meme + "CLP")
        async with self.http.post(baseurl_orionx, json=q, headers={'fingerprint': 'xd'}) as r:
            try:
                data = await r.json()
                return data[0]['data']['market']['lastTrade']['price']
            except KeyError:
                raise DivRetrievalError('$[value-error-data-not-available]')
        return 0

    def valid_currency(self, curr):
        if not isinstance(curr, str):
            return False

        curr = curr.upper()
        return curr in self.div_handlers.keys() or pat_currency.match(curr)


class DivRetrievalError(BaseException):
    pass
