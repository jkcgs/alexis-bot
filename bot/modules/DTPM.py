import re

from bs4 import BeautifulSoup

from discord import Embed
from bot import Command

pat_stop = re.compile('^[Pp][a-zA-Z][0-9]+$')
pat_rec = re.compile('^[a-zA-Z]?[0-9]{2,3}$')
pat_rec_err = re.compile('error_solo_paradero">([A-Z]?[0-9]{2,3}[A-Z]?)</div>[\n\r\t ]+[<a-z "=_]+>([a-zA-Z .]+)<')


# Hola Maxine
class DTPM(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'transantiago'
        self.aliases = ['ts']
        self.help = 'Muestra próximas llegadas de buses a un paradero de Transantiago'

    async def handle(self, cmd):
        if cmd.argc < 1:
            await cmd.answer('formato: $CMD <parada> [recorrido]')
            return

        if not pat_stop.match(cmd.args[0]):
            await cmd.answer('formato de parada incorrecto')
            return

        if cmd.argc > 1 and not pat_rec.match(cmd.args[1]):
            await cmd.answer('formato de recorrido incorrecto')
            return

        try:
            await cmd.typing()
            data = await self.get_arrivals(cmd.args[0].upper())
            if isinstance(data, str):
                await cmd.answer('error: *{}*'.format(data))
                return

            if len(data) < 1:
                await cmd.answer('no se encontró información o el paradero no existe')
                return

            if cmd.argc >= 2:
                for result in data:
                    if result['route_id'] == cmd.args[1].upper():
                        if result['bus_plate_number'] is None:
                            await cmd.answer('"*{}*"'.format(result['arrival_estimation']))
                        else:
                            await cmd.answer('tiempo estimado de llegada: **{}** (patente *{}*)'.format(
                                result['arrival_estimation'], result['bus_plate_number']
                            ))
                        return
                await cmd.answer('no hay llegadas próximas para ese recorrido')
            else:
                routes = []
                for arrival in data[:18]:
                    if arrival['bus_plate_number'] is None:
                        routes.append('**{}**: *{}*'.format(arrival['route_id'], arrival['arrival_estimation']))
                    else:
                        routes.append('**{}**: {} (patente *{}*)'.format(
                            arrival['route_id'], arrival['arrival_estimation'], arrival['bus_plate_number']
                        ))

                e = Embed(title='Próximas llegadas paradero ' + cmd.args[0].upper(), description='\n'.join(routes))
                await cmd.answer(e)

        except Exception as e:
            await cmd.answer('ocurrió un error al obtener la información')
            self.log.exception(e)

    async def get_arrivals(self, bus_stop):
        url = 'http://web.smsbus.cl/web/buscarAction.do'
        self.log.debug('loading %s', url)

        await self.http.get(url + '?d=cargarServicios')
        async with self.http.post(url, data={'d': 'busquedaParadero', 'ingresar_paradero': bus_stop}) as r:
            txt = await r.text()
            dom = BeautifulSoup(txt, 'html.parser')
            error = dom.find(id='respuesta_error')
            if error is not None:
                return error.text

            num_stop = dom.find(id='numero_parada_respuesta')
            if len(num_stop.find_all(class_='texto_h2')) > 1:
                prox = [
                    {
                        'route_id': list(num_stop.find_all(class_='texto_h2'))[1].text,
                        'bus_plate_number': p.find(id='proximo_bus_respuesta').text.strip(),
                        'arrival_estimation': p.find(id='proximo_tiempo_respuesta').text.strip(),
                        'distance': p.find(id='proximo_distancia_respuesta').text.strip()
                    }
                    for p in dom.find_all(id='proximo_respuesta')
                ]
            else:
                prox = [
                    {
                        'route_id': p.find(id='servicio_respuesta_solo_paradero').text,
                        'bus_plate_number': p.find(id='bus_respuesta_solo_paradero').text.strip(),
                        'arrival_estimation': p.find(id='tiempo_respuesta_solo_paradero').text.strip(),
                        'distance': p.find(id='distancia_respuesta_solo_paradero').text.strip()
                    }
                    for p in dom.find_all(id='proximo_solo_paradero')
                ]

            err = [
                {
                    'route_id': e.group(1),
                    'bus_plate_number': None,
                    'arrival_estimation': e.group(2),
                    'distance': None
                }
                for e in pat_rec_err.finditer(txt)
            ]

            return prox + err
