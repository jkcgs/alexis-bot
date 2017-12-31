from os import path

import yaml
import bs4

from alexis import Command
import re


class Value(Command):
    rx_div = re.compile('^([A-Z]{3}|UF)$')
    rx_num = re.compile('^\d+([.,]\d+)?$')
    baseurl = 'https://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20yahoo.finance.xchange' \
              '%20where%20pair%20in%20(%22{}{}%22)&format=json' \
              '&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback='
    baseurl_alt = 'http://www.xe.com/currencyconverter/convert/?Amount=1&From={}&To={}'
    baseurl_uf = 'http://api.sbif.cl/api-sbifv3/recursos_api/{}?apikey={}&formato=json'

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
        self.name = 'value'
        self.aliases = ['valor', 'uf', 'utm']
        self.help = 'Entrega datos de conversión de divisas'
        self.default_config = {
            'sbif_apikey': ''
        }

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
            await cmd.answer('formato de divisas incorrecto')
            return

        if not Value.valid_currency(div1) or not Value.valid_currency(div2):
            await cmd.answer('una de las divisas ingresadas es incorrecta. '
                             'Puedes utilizar UF, UTM, o una de las divisas de la lista de esta página: '
                             'http://www.xe.com/iso4217.php')
            return

        try:
            cant = float(cant.replace(',', '.'))
        except ValueError:
            await cmd.answer('formato incorrecto de valor a convertir')
            return

        await cmd.typing()

        try:
            if div1 == div2:
                await cmd.answer('técnicamente, no hay conversión entre dos divisas iguales, '
                                 'así que no me vengai na con weas')
                return

            if div1 in ['UF', 'UTM']:
                if self.bot.config['sbif_apikey'] == '':
                    await cmd.answer('La información de {} no está disponible'.format(div1))
                else:
                    value = await self.sbif(div1.lower())
                    if div2 == 'CLP':
                        if value is None:
                            await cmd.answer('no se pudo obtener el valor')
                        elif cant == 1:
                            await cmd.answer('La {} está a **$ {:.2f}**'.format(div1, value))
                        else:
                            await cmd.answer('{} {} son **$ {:.2f}**'.format(cant, div1, value*cant))
                    else:
                        value_conv = await self.convert_alt('CLP', div2)
                        answer = cant*value*value_conv
                        await cmd.answer('{} {} son **{:.2f} {}**'.format(cant, div1, answer, div2))
            else:
                value = await self.convert_alt(div1, div2)
                if value < 1:
                    await cmd.answer('**{} {}** son **{:.6f} {}**'.format(cant, div1, cant * value, div2))
                else:
                    await cmd.answer('**{} {}** son **{:.2f} {}**'.format(cant, div1, cant * value, div2))
        except DivRetrievalError as e:
            await cmd.answer('no pude obtener los datos de divisas D:\n```{}```'.format(str(e)))

    async def formato(self, cmd):
        await cmd.answer('formato: !value [cantidad] <divisa1> [a] <divisa2>\n'
                         '!uf [cantidad] [a] <divisa2>\n'
                         '!utm [cantidad] [a] <divisa2>')

    async def convert(self, div1, div2):
        attempts = 0
        url = Value.baseurl.format(div1, div2)
        while attempts < 10:
            self.log.debug('Cargando datos de divisa, intento ' + str(attempts + 1))
            self.log.debug('Cargando url %s', url)
            async with self.http.get(url) as r:
                data = await r.json()
                if r.status != 200:
                    attempts += 1
                    continue

                try:
                    if data['query']['count'] == 0:
                        raise DivRetrievalError('No se encontraron los datos solicitados en el servidor de conversión')
                    value = float(data['query']['results']['rate']['Rate'])
                except (KeyError, ValueError) as e:
                    raise DivRetrievalError('El valor de las divisas no está disponible: ' + str(e))

                return value

    async def convert_alt(self, div1, div2):
        url = Value.baseurl_alt.format(div1, div2)
        if div1 not in Value.currencies or div2 not in Value.currencies:
            raise DivRetrievalError('Una de las divisas ingresadas es incorrectas.')

        self.log.debug('Cargando datos de divisa (alt)')
        self.log.debug('URL: %s', url)

        async with self.http.get(url) as r:
            if r.status != 200:
                self.log.debug(await r.text())
                raise DivRetrievalError('La alternativa para datos de divisas no está disponible (status {})'
                                        .format(r.status))

            soup = bs4.BeautifulSoup(await r.text(), 'lxml')
            cont = soup.find('span', {'class': 'uccResultAmount'})
            value = float(cont.string)
            return value

    async def sbif(self, api):
        # TODO: Cache
        attempts = 0
        url = Value.baseurl_uf.format(api, self.bot.config['sbif_apikey'])

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

    @staticmethod
    def valid_currency(curr):
        return curr == 'UF' or curr == 'UTM' or curr in Value.currencies


class DivRetrievalError(BaseException):
    pass
