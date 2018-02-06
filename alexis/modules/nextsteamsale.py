from urllib.request import urlopen
from bs4 import BeautifulSoup
import json
from discord import Embed

from alexis import Command

class NextSteamSale(Command):
    url = 'https://www.whenisthenextsteamsale.com/'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'nextsteamsale'
        self.help = 'Muestra la información de la próxima oferta de Steam'

    async def handle(self, cmd):
        
        try:
            async with self.http.get(NextSteamSale.url) as s:
                content = await s.text()
                soup = BeautifulSoup(content, 'html.parser')
                sale = json.loads(soup.find('input', {'id':'hdnNextSale'}).attrs['value'])
                startDate = sale['StartDate'].split('T')
                endDate = sale['EndDate'].split('T')
                confirmed = "No"

                if sale['IsConfirmed'] == True:
                    confirmed = "Si"
                e = Embed()
                e.description = '**La [información](https://www.whenisthenextsteamsale.com/) de la siguiente oferta de Steam es:**'
                e.add_field(name='Nombre', value=sale['Name'], inline=False)
                e.add_field(name='Fecha de inicio', value=startDate[0] + ' a las ' + startDate[1] + ' hrs', inline=False)
                e.add_field(name='Fecha de término', value=endDate[0] + ' a las ' + endDate[1] + ' hrs', inline=False)
                e.add_field(name='Confirmado', value=confirmed)
                e.add_field(name='Duración', value=str(sale['Length']) + ' días') 
     

                await cmd.answer(embed=e)      
        except Exception as err:
            self.log.error(err)
            raise err



