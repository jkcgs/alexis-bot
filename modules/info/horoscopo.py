import discord
import peewee
import pytz
from datetime import datetime

from discord import Embed

from bot import Command, categories, BaseModel


class Horoscopo(Command):
    __version__ = '1.2.0'
    __author__ = 'makzk'
    api_url = 'https://api.adderou.cl/tyaas/'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'horoscopo'
        self.help = '$[horoscopo-help]'
        self.format = '`$[horoscopo-format]'
        self.db_models = [SuscriptorHoroscopo]
        self.category = categories.INFORMATION
        self.schedule = (self.update, 180)

        self.horoscopo = None
        self.update_day = None

    async def handle(self, cmd):
        if self.horoscopo is None:
            await cmd.answer('$[horoscopo-unavailable]')
            return

        if cmd.argc == 0:
            await cmd.answer('$[format]: $[horoscopo-format]')
            return

        if cmd.args[0] in ['update', 'reload'] and cmd.bot_owner:
            await cmd.typing()
            await self.update()
            await cmd.answer('$[horoscopo-loaded]')
            return

        if cmd.args[0] == 'suscribir':
            if cmd.argc < 2:
                await cmd.answer('$[format]: ' + self.format)
                return

            try:
                suscrip = SuscriptorHoroscopo.get(SuscriptorHoroscopo.userid == cmd.author.id)
                await cmd.answer('$[horoscopo-already-subscribed]', locales={'sign_name', suscrip.signo.title()})
                return
            except SuscriptorHoroscopo.DoesNotExist:
                pass

            signo = cmd.args[1]
            if self.get_sign(signo) is None:
                await cmd.answer('$[horoscopo-invalid-sign]')
                return

            SuscriptorHoroscopo.create(userid=cmd.author.id, signo=signo)
            await cmd.answer('$[horoscopo-subscribed]', locales={'sign_name': signo.title()})

            return

        if cmd.args[0] == 'desuscribir':
            if cmd.argc < 1:
                await cmd.answer('$[format]: $CMD desuscribir')
            else:
                try:
                    suscrip = SuscriptorHoroscopo.get(SuscriptorHoroscopo.userid == cmd.author.id)
                    name = suscrip.signo.title()
                    SuscriptorHoroscopo.delete_instance(suscrip)
                    await cmd.answer('$[horoscopo-removed]', locales={'sign_name': name})
                except SuscriptorHoroscopo.DoesNotExist:
                    await cmd.answer('$[horoscopo-not-subscribed]')

            return

        curr = datetime.now(pytz.timezone('Chile/Continental'))
        if self.horoscopo is None or self.update_day is None or self.update_day != curr.day:
            await cmd.typing()
            await self.update()

        signo = self.get_sign(cmd.args[0])
        if signo is None:
            await cmd.answer('$[horoscopo-invalid-sign]')
            return

        await cmd.answer(self.make_embed(signo))

    def get_sign(self, name):
        if isinstance(name, dict):
            return name
        elif name in self.horoscopo['horoscopo']:
            return self.horoscopo['horoscopo'][name]
        else:
            for sign in self.horoscopo['horoscopo'].values():
                if 'nombre' in sign and sign['nombre'].lower() == name.lower():
                    return sign
            return None

    def make_embed(self, signo):
        signo = self.get_sign(signo)
        if signo is None:
            return None

        embed = Embed(title='$[horoscopo-title] - {}'.format(self.horoscopo['titulo']))
        embed.description = '**{}** (*{}*)\n\n'.format(signo['nombre'], signo['fechaSigno'])
        embed.description += '**$[horoscopo-e-love]**: {}\n'.format(signo['amor'])
        embed.description += '**$[horoscopo-e-health]**: {}\n'.format(signo['salud'])
        embed.description += '**$[horoscopo-e-money]**: {}\n'.format(signo['dinero'])
        embed.description += '**$[horoscopo-e-colour]**: {} **$[horoscopo-e-number]**: {}\n'.format(
            signo['color'], signo['numero'])
        embed.set_footer(text='$[horoscopo-e-footer]')
        return embed

    async def update(self):
        self.log.debug('Loading %s ...', Horoscopo.api_url)
        async with self.http.get(Horoscopo.api_url) as r:
            data = await r.json()

            curr = datetime.now(pytz.timezone('Chile/Continental'))
            if self.horoscopo is None or self.horoscopo['titulo'] != data['titulo']:
                self.horoscopo = data
                self.update_day = curr.day
                self.log.debug('Horoscope data updated.')
                self.bot.loop.create_task(self.send_update())

    async def send_update(self):
        last_date = self.config_mgr('all').get('horoscopo_last')
        if last_date == self.horoscopo['titulo']:
            return

        suscriptores = SuscriptorHoroscopo.select()
        for suscriptor in suscriptores:
            embed = self.make_embed(suscriptor.signo)
            if embed is None:
                SuscriptorHoroscopo.delete_instance(suscriptor)
                continue

            user = await self.bot.get_user_info(suscriptor.userid)
            if user is None:
                SuscriptorHoroscopo.delete_instance(suscriptor)
                continue

            try:
                await self.bot.send_message(content='$[horoscopo-update]', embed=embed, destination=user)
            except discord.Forbidden:
                pass

        self.config_mgr('all').set('horoscopo_last', self.horoscopo['titulo'])


class SuscriptorHoroscopo(BaseModel):
    userid = peewee.TextField()
    signo = peewee.TextField()
