import re

from discord import Embed
from alexis import Command

pat_stop = re.compile('^[Pp][a-zA-Z][0-9]+$')
pat_rec = re.compile('^[a-zA-Z]?[0-9]{2,3}$')


# Hola Maxine
class DTPM(Command):
    url_time = 'https://api.scltrans.it/v2/stops/{}/next_arrivals'

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
            url = DTPM.url_time.format(cmd.args[0].upper())
            self.log.debug('loading %s', url)
            async with self.http.get(url) as r:
                data = await r.json()
                if 'results' not in data or len(data['results']) < 1:
                    await cmd.answer('no se encontró información o el paradero no existe')
                    return

                if cmd.argc >= 2:
                    for result in data['results'][:10]:
                        if result['route_id'] == cmd.args[1].upper():
                            await cmd.answer('tiempo estimado de llegada: **{}** (patente *{}*)'.format(
                                result['arrival_estimation'], result['bus_plate_number']
                            ))
                            return
                    await cmd.answer('recorrido no encontrado')
                else:
                    routes = []
                    for arrival in data['results'][:10]:
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
