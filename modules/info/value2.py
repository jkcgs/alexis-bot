from bot import Command, categories
from bot.utils import is_float


class Value2(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'

    baseurl = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE' \
              '&from_currency={}&to_currency={}&apikey={}'
    baseurl_sbif = 'https://api.sbif.cl/api-sbifv3/recursos_api/{}?apikey={}&formato=json'

    # Lista de divisas obtenidas desde http://www.xe.com/iso4217.php
    currencies = 'AED,AFN,ALL,AMD,ANG,AOA,ARS,AUD,AWG,AZN,BAM,BBD,BDT,BGN,BHD,BIF,BMD,BND,BOB,BRL,BSD,BTN,BWP,BYN,' \
                 'BZD,CAD,CDF,CHF,CLP,CNY,COP,CRC,CUC,CUP,CVE,CZK,DJF,DKK,DOP,DZD,EGP,ERN,ETB,EUR,FJD,FKP,GBP,GEL,' \
                 'GGP,GHS,GIP,GMD,GNF,GTQ,GYD,HKD,HNL,HRK,HTG,HUF,IDR,ILS,IMP,INR,IQD,IRR,ISK,JEP,JMD,JOD,JPY,KES,' \
                 'KGS,KHR,KMF,KPW,KRW,KWD,KYD,KZT,LAK,LBP,LKR,LRD,LSL,LYD,MAD,MDL,MGA,MKD,MMK,MNT,MOP,MRO,MUR,MVR,' \
                 'MWK,MXN,MYR,MZN,NAD,NGN,NIO,NOK,NPR,NZD,OMR,PAB,PEN,PGK,PHP,PKR,PLN,PYG,QAR,RON,RSD,RUB,RWF,SAR,' \
                 'SBD,SCR,SDG,SEK,SGD,SHP,SLL,SOS,SPL,SRD,STD,SVC,SYP,SZL,THB,TJS,TMT,TND,TOP,TRY,TTD,TVD,TWD,TZS,' \
                 'UAH,UGX,USD,UYU,UZS,VEF,VND,VUV,WST,XAF,XCD,XDR,XOF,XPF,YER,ZAR,ZMW,ZWD'.split(',')

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'value2'
        self.aliases = ['uf2', 'utm2']
        self.help = 'djklasjdlaksdj'
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

    async def handle(self, cmd):
        div_from = ''
        div_to = 'EUR'
        mult = 1

        if cmd.cmdname != self.name:
            div_from = cmd.cmdname.rstrip('2').upper()
            if div_from in self.div_defaults.keys():
                div_to = self.div_defaults[div_from]

            if cmd.argc == 1:
                if is_float(cmd.args[0]):
                    mult = float(cmd.args[0])
                else:
                    div_to = cmd.args[0]
            elif cmd.argc > 1:
                if not is_float(cmd.args[0]):
                    await cmd.answer('formato incorrecto [1]')
                    return

                mult = float(cmd.args[0])
                div_to = cmd.args[1]
        else:
            if cmd.argc < 2:
                await cmd.answer('formato incorrecto [2]')
                return

            if cmd.argc >= 3 and not is_float(cmd.args[0]):
                await cmd.answer('formato incorrecto [3]')
                return

            if cmd.argc == 2 and (is_float(cmd.args[0]) or is_float(cmd.args[1])):
                await cmd.answer('formato incorrecto [4]')
                return

            div_from = cmd.args[1 if cmd.argc > 2 else 0]
            div_to = cmd.args[2 if cmd.argc > 2 else 1]

            if cmd.argc > 2:
                mult = float(cmd.args[0])

        div_from = div_from.upper()
        div_to = div_to.upper()

        try:
            if div_from.upper() in self.div_handlers.keys():
                result = await self.div_handlers[div_from](div_to, mult)
            else:
                result = await self.handler(div_from, div_to, mult)
        except DivRetrievalError2 as e:
            await cmd.answer('error: ' + str(e))
            return

        await cmd.answer('from: {}, to: {}, mult: {}, result: {}'.format(div_from, div_to, mult, result))

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
            raise DivRetrievalError2('La API key de conversión de divisas no está configurada')

        attempts = 0
        url = Value2.baseurl.format(div1, div2, self.bot.config['currency_apikey'])
        while attempts < 10:
            self.log.debug('Cargando datos de divisa, intento ' + str(attempts + 1))
            self.log.debug('Cargando url %s', url)
            async with self.http.get(url) as r:
                data = await r.json()
                if r.status != 200:
                    attempts += 1
                    continue

                try:
                    value = float(data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
                except (KeyError, ValueError) as e:
                    raise DivRetrievalError2('El valor de las divisas no está disponible: ' + str(e))

                return value

    async def sbif(self, api):
        # TODO: Cache
        attempts = 0
        if self.bot.config['sbif_apikey'] == '':
            raise DivRetrievalError2('La API key de SBIF no está configurada')

        url = Value2.baseurl_sbif.format(api.lower(), self.bot.config['sbif_apikey'])

        while attempts < 10:
            async with self.http.get(url) as r:
                data = await r.json(content_type='text/json')

                if r.status != 200:
                    attempts += 1
                    continue

                try:
                    campo = api.upper() + 's'
                    value = float(data[campo][0]['Valor'].replace('.', '').replace(',', '.'))
                except (KeyError, ValueError):
                    raise DivRetrievalError2('no pude obtener los datos de divisas (UF) D:')

                return value


class DivRetrievalError2(BaseException):
    pass
