import json
import aiohttp
import asyncio

from alexis import Command
from alexis.utils import is_float

chaucha_api = 'https://api2.orionx.io/graphql'
chaucha_json = [{
    "operationName": "getMarketIdleData",
    "query": "query getMarketIdleData($code: ID) { market(code: $code) { code lastTrade { price } } }",
    "variables": {
        "code": "CHACLP"
    }
}]
headers = {
    'content-type': 'application/json',
    'fingerprint': '34119444335432e80868790a11c15a36'
}


class Chaucha(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'chaucha'
        self.aliases = ['cha']
        self.help = 'Entrega el valor de la chauchita'
        self.user_delay = 5
        self.current = None

    async def handle(self, cmd):
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

        if self.current is None:
            await cmd.answer('datos no disponibles')
            return

        txt = 'una chaucha vale' if mult == 1 else (str(mult) + ' chauchas valen')
        await cmd.answer('{}: **${}**'.format(txt, str(self.current * mult)))

    async def task(self):
        await self.bot.wait_until_ready()
        try:
            req = self.http.post(chaucha_api, data=json.dumps(chaucha_json), headers=headers, timeout=20)

            async with req as r:
                if r.status == 200:
                    data = await r.json()
                    self.current = int(data[0]['data']['market']['lastTrade']['price'])
        except (asyncio.TimeoutError, aiohttp.ServerDisconnectedError):
            # self.log.debug('Error al cargar datos de chaucha: el servidor demoró mucho en responder')
            pass
        except Exception as e:
            self.log.debug('Error al cargar datos de chaucha')
            self.log.exception(e)
        finally:
            if not self.bot.is_closed:
                await asyncio.sleep(15)
                self.bot.loop.create_task(self.task())
