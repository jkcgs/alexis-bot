from bs4 import BeautifulSoup
import json
import asyncio
from discord import Embed

from alexis import Command


class NextSteamSale(Command):
    url = 'https://www.whenisthenextsteamsale.com/'
    sale = {''}

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'nextsteamsale'
        self.aliases = ['steamsale']
        self.help = '$[nss-help]'

    async def handle(self, cmd):
        
        await cmd.typing()
        sale = NextSteamSale.sale
        if sale != '':
            start_date = sale['StartDate'].split('T')
            end_date = sale['EndDate'].split('T')
            confirmed = "$[yes]" if sale['IsConfirmed'] else '$[no]'
            remaining_time = sale['RemainingTime'].split('.')

            e = Embed()
            e.description = '$[nss-title]'
            e.add_field(name='$[name]', value=sale['Name'], inline=False)
            e.add_field(name='$[start-date]', value='$[nss-start-date]', inline=False)
            e.add_field(name='$[end-date]', value='$[nss-end-date]', inline=False)
            e.add_field(name='$[nss-confirmed]', value=confirmed)
            e.add_field(name='$[nss-length]', value='$[nss-length-value]')
            e.add_field(name='$[nss-remaining-time]', value='$[nss-remaining-time-value]' , inline=False)

            await cmd.answer(embed=e, locales={
                'startdate': start_date[0],
                'starthour': start_date[1],
                'enddate': end_date[0],
                'endhour': end_date[1],
                'days': sale['Length'],
                'remainingdays': remaining_time[0],
                'remaininghours': remaining_time[1]
            })
        

    async def task(self):
        await self.bot.wait_until_ready()
        try:
            async with self.http.get(NextSteamSale.url) as s:
                content = await s.text()
                soup = BeautifulSoup(content, 'html.parser')
                NextSteamSale.sale = json.loads(soup.find('input', {'id': 'hdnNextSale'}).attrs['value'])

        except Exception as err:
            self.log.error(err)
            raise err
        finally:
            if not self.bot.is_closed:
                await asyncio.sleep(15)
                self.bot.loop.create_task(self.task())
            



