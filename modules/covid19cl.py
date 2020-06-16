from datetime import datetime

from discord import Embed

from bot import Command, categories

cached_data = None
cached_ts = datetime.now().timestamp()
last_date = None


def nf(val):
    return '.'.join([str(val)[::-1][i:i + 3] for i in range(0, len(str(val)), 3)])[::-1]


def embed(data, data_diff):
    description = \
        f'Información del día **{data["fecha"]}** (hasta las 21:00 del día anterior)\n\n' \
        f'**Total confirmados:** {data_diff["confirmados"]}\n' \
        f'*({nf(data["sintomaticos"])} sintomáticos, {nf(data["asintomaticos"])} asintomáticos)*\n' \
        f'**Total activos:** {data_diff["activos"]}\n' \
        f'**Recuperados:** {data_diff["recuperados"]}\n' \
        f'**Fallecidos:** {data_diff["fallecidos"]}\n\n' \
        f'**Exámenes realizados:** {nf(data["total_examenes"])} (+{nf(data["examenes"])})\n' \
        f'**Pacientes conectados:** {data_diff["conectados"]}, críticos: {data_diff["criticos"]}\n' \
        f'**Ventiladores disponibles:** {data_diff["ventiladores_disp"]}\n\n' \
        f'**Residencias sanitarias**: {data["rs_residencias"]} ' \
        f'con {nf(data["rs_habitaciones"])} habitaciones'

    the_embed = Embed(title='Estado del Coronavirus COVID-19 en Chile', description=description)
    the_embed.set_footer(text='Información actualizada al: {}'.format(data['ts_capturado']))
    return the_embed


class Covid19CL(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'
    url = 'https://api.mak.wtf/covid'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'covid19cl'
        self.aliases = ['covid', 'coronavirus']
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        try:
            await cmd.typing()
            data = await self.get_data()

            data_diff = {}
            fields = ['activos', 'conectados', 'confirmados', 'criticos', 'fallecidos',
                      'recuperados', 'ventiladores_disp']
            for field in fields:
                data_diff[field] = nf(data[field])
                if data['ayer']:
                    val = data[field] - data['ayer'][field]
                    data_diff[field] += ' ({})'.format(['', '+'][int(val > 0)] + nf(val))

            the_embed = embed(data, data_diff)
            await cmd.answer(embed=the_embed)

            return
        except Exception as e:
            self.log.error(e)
            await cmd.answer('No se pudo cargar la información: {}'.format(str(e)))

    async def get_data(self):
        global cached_data, cached_ts, last_date
        now = datetime.now()
        now_date = now.strftime('%m%d')
        if last_date and cached_data and (last_date == now_date or (cached_ts + 10) > datetime.now().timestamp()):
            return cached_data

        self.log.debug('Updating data...')
        async with self.http.get(self.url) as r:
            if r.status != 200:
                raise ValueError('No se pudo obtener la información ({}).'.format(r.status))

            data = await r.json()
            cached_data = data
            now = datetime.now()
            cached_ts = now.timestamp()
            last_date = now.strftime('%m%d')
            return data
