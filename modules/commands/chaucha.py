import json

import asyncio

from modules.base.command import Command
from modules.base.utils import is_float

chaucha_api = 'https://api.orionx.io/graphql'
chaucha_json = [{
    "operationName": "marketCurrentStats",
    "query": "query marketCurrentStats($marketCode: ID!) { market(code: $marketCode) { lastTrade { price } } }",
    "variables": {
        "marketCode": "CHACLP"
    }
}]
headers = {'content-type': 'application/json'}


class Chaucha(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'chaucha'
        self.aliases = ['cha']
        self.help = 'Entrega el valor de la chauchita'
        self.user_delay = 5

    async def handle(self, message, cmd):
        mult = 1
        if cmd.argc == 1:
            if not is_float(cmd.args[0]):
                await cmd.answer('formato: $PX$NM [múltiplo]')
                return
            else:
                mult = float(cmd.args[0].replace(',', '.'))
                if mult <= 0:
                    await cmd.answer('formato: $PX$NM [múltiplo (positivo porfa)]')
                    return

        try:
            await cmd.typing()
            req = self.http.post(chaucha_api, data=json.dumps(chaucha_json), headers=headers, timeout=30)

            async with req as r:
                if r.status == 200:
                    data = await r.json()
                    val = int(data[0]['data']['market']['lastTrade']['price'])
                    txt = 'una chaucha vale' if mult == 1 else (str(mult) + ' chauchas valen')
                    await cmd.answer('{}: **${}**'.format(txt, str(val * mult)))
                else:
                    await cmd.answer('algo pasó jaj, status: ' + str(r.status))
        except asyncio.TimeoutError:
            await cmd.answer('el servidor demoró mucho en responder D:')
        except KeyError as e:
            self.log.exception(e)
            await cmd.answer('no se pudo cargar el valor de la chaucha :(')

