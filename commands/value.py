from commands.base.command import Command
import re


class Value(Command):
    rx_div = re.compile('^[A-Z]{3}$')
    baseurl = 'https://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20yahoo.finance.xchange' \
              '%20where%20pair%20in%20(%22{}{}%22)&format=json' \
              '&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback='

    def __init__(self, bot):
        super().__init__(bot)
        self.name = ['value', 'valor']
        self.help = 'Entrega datos de conversión de divisas'

    async def handle(self, message, cmd):
        if len(cmd.args) < 2:
            await self.formato(cmd)
            return

        if cmd.argc == 2:
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
            await cmd.answer('Formato de divisas incorrecto')
            return

        try:
            cant = float(cant.replace(',', '.'))
        except ValueError:
            await cmd.answer('Formato incorrecto de valor a convertir')
            return

        await cmd.typing()

        attempts = 0
        while attempts < 10:
            self.log.debug('Cargando datos de divisa, intento ' + str(attempts+1))
            async with self.http.get(Value.baseurl.format(div1, div2)) as r:
                data = await r.json()
                if r.status != 200:
                    attempts += 1
                    continue

                try:
                    value = float(data['query']['results']['rate']['Rate'])
                except (KeyError, ValueError):
                    await cmd.answer('no pude obtener los datos de divisas D:')
                    return

                await cmd.answer('**{} {}** son **{} {}**'.format(cant, div1, cant*value, div2))
                return

        await cmd.answer('no pude obtener los datos de divisas D:')

    async def formato(self, cmd):
        await cmd.answer('Formato: !value [cantidad] <divisa1> [a] <divisa2>')