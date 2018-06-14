import asyncio
from datetime import datetime
from pytz import reference

from discord import Embed

from bot import Command, BaseModel
from peewee import DateTimeField, TextField, BooleanField
from bot.utils import pat_delta, timediff_parse, no_tags, deltatime_to_str, format_date


class RemindMe(Command):
    __author__ = 'makzk'
    __version__ = '1.0.1'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'remindme'
        self.help = 'Te ayuda a recordar algo'
        self.db_models = [RemindMeEvent]

    async def handle(self, evt):
        last = RemindMeEvent.get_or_none((RemindMeEvent.userid == evt.author.id) & (RemindMeEvent.sent == False))

        if evt.argc < 2:
            if evt.argc == 0:
                if last is None:
                    await evt.answer('no tienes un recordatorio activo.')
                else:
                    await evt.answer('tienes un recordatorio activo! "{}". Usa `$CMD cancel` para cancelarlo.'.format(
                        last.description))
            else:
                if evt.args[0] == 'cancel':
                    if last is None:
                        await evt.answer('no tienes un recordatorio activo.')
                    else:
                        evt.sent = True
                        evt.save()
                        await evt.answer('recordatorio cancelado.')
                else:
                    await evt.answer('formato: $CMD <tiempo> <mensaje>')

            return

        if last is not None:
            await evt.answer('ya tienes un recordatorio activo: "{}". Usa `$CMD cancel` para cancelarlo.'.format(
                last.description))
            return

        if not pat_delta.match(evt.args[0]):
            await evt.answer('tiempo de recordatorio incorrecto. El formato es NM1NM2(...), por ejemplo, '
                             '1d, 3h30m, 3m15s, 30m, etc')
            return

        dt = timediff_parse(evt.args[0])
        if dt.total_seconds() < 10 or dt.total_seconds() > 315705600:
            await evt.answer('el tiempo de recordatorio debe estar entre 10 segundos y 10 años')
            return

        text = no_tags(' '.join(evt.args[1:]), self.bot, emojis=False).replace('\n', ' ')
        if len(text) > 150:
            await evt.answer('el texto del recordatorio sólo puede tener hasta 150 carácteres')
            return

        time = datetime.now() + dt
        RemindMeEvent.create(userid=evt.author.id, description=text, alerttime=time)

        await evt.answer('se te enviará un recordatorio con tu descripción ingresada en {delta} ({datetime})'.format(
            delta=deltatime_to_str(dt), datetime=format_date(time)
        ))

    async def task(self):
        await self.bot.wait_until_ready()
        try:
            query = RemindMeEvent.select().where(
                (RemindMeEvent.alerttime <= datetime.now()) &
                (RemindMeEvent.sent == False)
            )
            for event in query:
                user = await self.bot.get_user_info(event.userid)
                if user is not None:
                    emb = Embed(title='RemindMe!', description=event.description)
                    emb.set_footer(text='Creada: {}'.format(
                        format_date(event.created))
                    )
                    await self.bot.send_message(user, embed=emb)

                event.sent = True
                event.save()
        except Exception as e:
            if not isinstance(e, RuntimeError):
                self.log.exception(e)
        finally:
            await asyncio.sleep(5)

        if not self.bot.is_closed:
            self.bot.loop.create_task(self.task())


class RemindMeEvent(BaseModel):
    created = DateTimeField(default=datetime.now)
    userid = TextField()
    description = TextField()
    alerttime = DateTimeField()
    sent = BooleanField(default=False)
