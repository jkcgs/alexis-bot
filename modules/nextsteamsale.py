from bs4 import BeautifulSoup
import json
from discord import Embed

from bot import Command, categories


class NextSteamSale(Command):
    url = 'https://www.whenisthenextsteamsale.com/'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'nextsteamsale'
        self.aliases = ['steamsale']
        self.help = '$[nss-help]'
        self.sale = None
        self.category = categories.INFORMATION
        self.schedule = (self.update_info, 43200)

    async def handle(self, cmd):
        if self.sale is None:
            await cmd.answer('$[data-not-available]')
            return

        start_date = self.sale['StartDate'].split('T')
        end_date = self.sale['EndDate'].split('T')
        confirmed = "$[yes]" if self.sale['IsConfirmed'] else '$[no]'
        remaining_time = self.sale['RemainingTime'].split('.')

        if len(remaining_time) == 2:
            remaining_time.insert(0, "0")
        
        e = Embed()
        
        e.description = '$[nss-title]'
        e.add_field(name='$[name]', value=self.sale['Name'], inline=False)
        e.add_field(name='$[start-date]', value='$[nss-start-date]', inline=False)
        e.add_field(name='$[end-date]', value='$[nss-end-date]', inline=False)
        e.add_field(name='$[nss-confirmed]', value=confirmed)
        e.add_field(name='$[nss-length]', value='$[nss-length-value]')
        if len(remaining_time) == 1:
            remaining_time.insert(1, "00:00:00")
            e.add_field(name='$[nss-remaining-time]', value='$[nss-sales-have-begun]', inline=False)
        else:
            e.add_field(name='$[nss-remaining-time]', value='$[nss-remaining-time-value]', inline=False)

        await cmd.answer(embed=e, locales={
            'startdate': start_date[0],
            'starthour': start_date[1],
            'enddate': end_date[0],
            'endhour': end_date[1],
            'days': self.sale['Length'],
            'remainingdays': remaining_time[0],
            'remaininghours': remaining_time[1]
        })

    async def update_info(self):
        try:
            self.log.debug('Loading next Steam sale information...')
            async with self.http.get(NextSteamSale.url) as s:
                content = await s.text()
                soup = BeautifulSoup(content, 'html.parser')
                elem = soup.find('input', {'id': 'hdnNextSale'})
                if elem and 'value' in elem.attrs:
                    self.sale = json.loads(elem.attrs['value'])
                else:
                    raise Exception('Next Steam sale data not available')

        except Exception as err:
            self.log.error(err)
            raise err
