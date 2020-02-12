from datetime import datetime

from discord import Embed

from bot import Command, BaseModel, categories
from peewee import DateTimeField, TextField, BooleanField
from bot.utils import timediff_parse, no_tags, deltatime_to_str, format_date, auto_int
from bot.regex import pat_delta


class RemindMeEvent(BaseModel):
    created = DateTimeField(default=datetime.now)
    userid = TextField()
    description = TextField()
    alerttime = DateTimeField()
    sent = BooleanField(default=False)


class RemindMe(Command):
    __author__ = 'makzk'
    __version__ = '1.0.2'
    db_models = [RemindMeEvent]

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'remindme'
        self.help = '$[remindme-help]'
        self.usage = '$[remindme-usage]'
        self.category = categories.UTILITY
        self.schedule = (self.remind_task, 5)
        self.default_config = {
            'remindme_text_limit': 150
        }

    async def handle(self, evt):
        text_limit = self.bot.config.get('remindme_text_limit', 150)
        last = RemindMeEvent.get_or_none((RemindMeEvent.userid == evt.author.id) & (RemindMeEvent.sent == False))

        if evt.argc < 2:
            if evt.argc == 0:
                if last is None:
                    await evt.answer('$[remindme-no-active]')
                else:
                    await evt.answer('$[remindme-already-active]')
            else:
                if evt.args[0] == 'cancel':
                    if last is None:
                        await evt.answer('$[remindme-no-active]')
                    else:
                        last.sent = True
                        last.save()
                        await evt.answer('$[remindme-cancelled]')
                else:
                    await evt.answer('$[format]: $[remindme-usage]')

            return

        if last is not None:
            await evt.answer('$[remindme-already-active]')
            return

        if not pat_delta.match(evt.args[0]):
            await evt.answer('$[remindme-error-time]')
            return

        dt = timediff_parse(evt.args[0])
        if dt.total_seconds() < 10 or dt.total_seconds() > 315705600:
            await evt.answer('$[remindme-error-limit]')
            return

        text = no_tags(' '.join(evt.args[1:]), self.bot, emojis=False).replace('\n', ' ')
        if len(text) > text_limit:
            await evt.answer('$[remindme-error-text-limit]', locales={'max': text_limit, 'amount': len(text)})
            return

        time = datetime.now() + dt
        RemindMeEvent.create(userid=evt.author.id, description=text, alerttime=time)

        await evt.answer('$[remindme-success]', locales={
            'delta': deltatime_to_str(dt), 'datetime': format_date(time)
        })

    async def remind_task(self):
        query = RemindMeEvent.select().where(
            (RemindMeEvent.alerttime <= datetime.now()) &
            (RemindMeEvent.sent == False)
        )
        for event in query:
            user = self.bot.get_user(auto_int(event.userid))
            if user is not None:
                emb = Embed(title='RemindMe!', description=event.description)
                emb.set_footer(text='$[remindme-footer]')
                await self.bot.send_message(user, embed=emb, locales={'date': format_date(event.created)})

            event.sent = True
            event.save()
