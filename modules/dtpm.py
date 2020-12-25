import re

from bs4 import BeautifulSoup

import json

from lxml import etree

from discord import Embed
from bot import Command, categories

pat_stop = re.compile('^[Pp][a-zA-Z][0-9]+$')
pat_rec = re.compile('^[a-zA-Z]?[0-9]{2,3}[cenvxyCENVXY]{0,2}$')
pat_rec_err = re.compile('error_solo_paradero">([A-Z]?[0-9]{2,3}[A-Z]?)</div>[\n\r\t ]+[<a-z "=_]+>([a-zA-Z .]+)<')

red_emoji = "<:REDBus:787112489494118410>"


# This XSLT object transforms the raw XML data received, removing it's namespaces.

strip_namespaces = etree.XSLT(etree.XML("""<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" indent="no"/>

<xsl:template match="/|comment()|processing-instruction()">
    <xsl:copy>
      <xsl:apply-templates/>
    </xsl:copy>
</xsl:template>

<xsl:template match="*">
    <xsl:element name="{local-name()}">
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
</xsl:template>

<xsl:template match="@*">
    <xsl:attribute name="{local-name()}">
      <xsl:value-of select="."/>
    </xsl:attribute>
</xsl:template>
</xsl:stylesheet>"""))


# Hola Maxine
class DTPM(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'transantiago'
        self.aliases = ['ts']
        self.help = '$[dtpm-help]'
        self.format = '$[dtpm-format]'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        if cmd.argc < 1:
            await cmd.answer('$[format]: $[dtpm-format]')
            return

        if not pat_stop.match(cmd.args[0]):
            await cmd.answer('$[dtpm-error-invalid-stop]')
            return

        if cmd.argc > 1 and not pat_rec.match(cmd.args[1]):
            await cmd.answer('$[dtpm-error-invalid-line]')
            return

        try:
            await cmd.typing()
            data = await self.get_arrivals(cmd.args[0].upper())
            if isinstance(data, str):
                await cmd.answer('$[dtpm-error]', locales={'error': data})
                return
                
            if cmd.argc >= 2:
                # Sends info for a single route
                if cmd.args[1].upper() not in data[0]:
                    await cmd.answer('$[dtpm-no-arrivals]')
                
                else:
                    route = data[0].get(cmd.args[1].upper())
                    if isinstance(route, dict):
                        await cmd.answer('$[dtpm-estimated-time]', locales={
                        'time': route[0]['time_prediction'],
                        'plate': route[0]['license_plate']})
                        
                    else:
                        await cmd.answer(route)
                
                return
                
            else:
                # Sends info for all the routes in the specified stop
                routes = []
                for route in list(data[0].keys())[:18]:
                    if isinstance(data[0][route], str):
                        routes.append('**{}**: {}'.format(route, data[0][route]))
                    else:
                        next_bus = data[0][route][0]
                        routes.append('**{}**: {} (patente *{}*)'.format(
                            route, next_bus['time_prediction'], next_bus['license_plate']
                        ))
                
                print(data[1])
                
                e = Embed(title='$[dtpm-next-arrivals]', description="{} **{}**\n".format(red_emoji, data[1])+'\n'.join(routes))
                await cmd.answer(e, locales={'stop': cmd.args[0].upper()})


        except Exception as e:
            await cmd.answer('$[dtpm-error-raised]')
            self.log.exception(e)

    async def get_arrivals(self, bus_stop):
    
        """
        This will build an array with an "arrivals" dictionary
        and the bus stop name.
        The structure is as follows:
            - Array item 0
                - Route Number (with arrivals) (key)
                    - Array of buses
                        - Bus 1 (dict if it has arrival data, string if it only mentions arrival periods)
                            - "distance" (key)
                                - Distance from bus stop (string)
                            - "time_prediction" (key)
                                - Predicted time until arrival to bus stop (string)
                            - "license_plate" (key)
                                - License Plate of the bus (string)
                        - Bus 2 (If present)
                   
                - Route Number (If no bus is coming) (key)
                    - API's error message (string)
            
            - Array item 1
                - Bus stop name (string)
                
        If the requests fails because of a typing error (invalid bus stop), it will
        return a string with the error message provided by the API.
        """
        
        url = 'http://ws13.smsbus.cl/wspatentedos/services/PredictorParaderoServicioWS'
        body_data = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:pred="http://predParaderoServicioWS.ws.simtws.wirelessiq.cl">
   <soapenv:Header/>
   <soapenv:Body>
      <pred:predictorParaderoServicio>
         <pred:paradero>{}</pred:paradero>
         <pred:servicio></pred:servicio>
         <pred:cliente>0</pred:cliente>
         <pred:resolucion></pred:resolucion>
         <pred:ipUsuarioFinal></pred:ipUsuarioFinal>
         <pred:webTransId></pred:webTransId>
      </pred:predictorParaderoServicio>
   </soapenv:Body>
</soapenv:Envelope>""".format(bus_stop)

        header_data = {
            "Accept-Encoding": "gzip,deflate",
            "Content-Type": "text/xml;charset=UTF-8",
            "SOAPAction": "\"\"",
            "Content-Length": str(len(body_data)),
            "Host": "ws13.smsbus.cl",
            "Connection": "Keep-Alive",
            "User-Agent": "Apache-HttpClient/4.5.5 (Java/12.0.1)"
        }
        self.log.debug('Loading %s', url)

        await self.http.get(url)
        
        async with self.http.post(url, data=body_data, headers=header_data) as r:
            text = await r.text()
            
            # Here we get rid of the envelope tagz
            data_root = etree.XML(text[38:])
            root_tree = etree.ElementTree(data_root)
            
            usable_tree = strip_namespaces(root_tree)

            received_data = usable_tree.find("Body").find("predictorParaderoServicioResponse").find("predictorParaderoServicioReturn")

            bus_stop_data = received_data.find("respuestaParadero").text
            
            if (bus_stop_data == "Paradero invalido.") :
                return bus_stop_data
                
            else:
            
                results = {}
                return_list = []
                
                for route in received_data.find("servicios").findall("item"):
                    
                    """ NOTE: one could use .get() instead of .find().text, but the
                        first one isn't returning anything"""
                    
                    type = route.find("codigorespuesta").text
                    service = route.find("servicio").text
                    
                    results[service] = []
                    
                    # Checks if the type is one of the two that carry actual bus data
                    
                    if type in ("00", "01"):
                        results[service].append({
                        "distance": route.find("distanciabus1").text,
                        "time_prediction": route.find("horaprediccionbus1").text,
                        "license_plate": route.find("ppubus1").text
                        })
                        
                        if type == "00":
                            results[service].append({
                            "distance": route.find("distanciabus2").text,
                            "time_prediction": route.find("horaprediccionbus2").text,
                            "license_plate": route.find("ppubus2").text
                            })
                        
                    else:
                        results[service] = route.find("respuestaServicio").text
                
                return_list.append(results)
                
                # This is the name of the Bus Stop
                return_list.append(received_data.find("nomett").text)
                return return_list
