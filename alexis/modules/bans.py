from datetime import datetime
import peewee

from alexis import Command
from alexis.base.database import BaseModel
import random

from alexis.base.utils import is_int


class BanCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ban'
        self.help = 'Banea (simbólicamente) a un usuario'
        self.allow_pm = False
        self.pm_error = 'banéame esta xd'
        self.db_models = [Ban]
        self.default_enabled = False

        self.user_delay = 10

    async def handle(self, message, cmd):
        if cmd.argc < 1:
            await cmd.answer('Formato: $PX$NM <nombre, id, @mención>')
            return

        mention = await cmd.get_user(cmd.text, member_only=True)
        if mention is None:
            await cmd.answer('usuario no encontrado')
            return

        mention_name = mention.display_name

        if not cmd.owner and cmd.is_owner(mention):
            await cmd.answer('nopo wn no hagai esa wea xd')
            return

        if mention.id == self.bot.user.id:
            await cmd.answer('OYE NUUUUUUU >w<')
            return

        if mention.bot:
            await cmd.answer('con mi colega no, tamo? :angry:')
            return

        # Evitar que alguien se banee a si mismo
        if self.bot.last_author == mention.id:
            await cmd.answer('no hagai trampa po wn xd')
            return

        if not random.randint(0, 1):
            await cmd.answer('¡**$AU** intentó banear a **{}**, quien se salvó de milagro!'
                             .format(mention_name), withname=False)
            return

        user, created = Ban.get_or_create(userid=mention.id, server=message.server.id,
                                          defaults={'user': str(mention)})
        update = Ban.update(bans=Ban.bans + 1, lastban=datetime.now(), user=str(mention))
        update = update.where(Ban.userid == mention.id, Ban.server == message.server.id)
        update.execute()

        if created:
            text = 'Uff, ¡**$AU** le ha dado a **{}** su primer ban!'.format(mention_name)
        else:
            text = '¡**$AU** ha baneado a **{}** sumando **{} baneos**!'
            text = text.format(mention_name, user.bans + 1)
        await cmd.answer(text, withname=False)


class Bans(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'bans'
        self.help = 'Muestra la cantidad de bans de una persona'
        self.allow_pm = False
        self.pm_error = 'no po wn que te crei'

    async def handle(self, message, cmd):
        if len(cmd.args) != 1:
            await cmd.answer('formato: $PX$NM <usuario (nombre*, id, mención)>')
            return

        mention = await cmd.get_user(cmd.text)
        if mention is None:
            await cmd.answer('usuario no encontrado')
            return

        if cmd.is_owner(mention):
            mesg = 'te voy a decir la cifra exacta: Cuatro mil trescientos cuarenta y '
            mesg += 'cuatro mil quinientos millones coma cinco bans, ese es el valor.'
            await cmd.answer(mesg)
            return

        user, created = Ban.get_or_create(userid=mention.id, server=message.server.id,
                                          defaults={'user': str(mention)})

        if user.bans == 0:
            mesg = "```\nException in thread \"main\" cl.discord.alexis.ZeroBansException\n"
            mesg += "    at AlexisBot.main(AlexisBot.java:34)\n```"
        else:
            word = 'ban' if user.bans == 1 else 'bans'
            if user.bans == 2:
                word = '~~papás~~ bans'

            mesg = '**{}** tiene {} {}'.format(mention.display_name, user.bans, word)

        await cmd.answer(mesg)


class SetBans(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'setbans'
        self.help = 'Determina la cantidad de baneos de un usuario'
        self.allow_pm = False
        self.pm_error = 'como va a funcionar esta weá por pm wn que chucha'
        self.owner_only = True

    async def handle(self, message, cmd):
        if cmd.argc < 2 or not is_int(cmd.args[-1]):
            await cmd.answer('Formato: $PX$NM <nombre, id, cantidad> <cantidad>')
            return

        mention = await cmd.get_user(' '.join(cmd.args[0:-1]))
        if mention is None:
            await cmd.answer('usuario no encontrado')
            return

        num_bans = int(cmd.args[-1])
        user, _ = Ban.get_or_create(userid=mention.id, server=message.server.id,
                                    defaults={'user': str(mention)})
        update = Ban.update(bans=num_bans, lastban=datetime.now(), user=str(mention))
        update = update.where(Ban.userid == mention.id, Ban.server == message.server.id)
        update.execute()

        name = mention.display_name
        if num_bans == 0:
            mesg = 'bans de **{}** reiniciados xd'.format(name)
            await cmd.answer(mesg)
        else:
            word = 'ban' if num_bans == 1 else 'bans'
            mesg = '**{}** ahora tiene {} {}'.format(name, num_bans, word)
            await cmd.answer(mesg)


class BanRank(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'banrank'
        self.aliases = [self.bot.config['command_prefix'] + 'banrank']
        self.help = 'Muestra el ranking de usuarios baneados. Con dos símbolos muestra una lista más extensa.'
        self.allow_pm = False
        self.pm_error = 'como va a funcionar esta weá por pm wn que chucha'

    async def handle(self, message, cmd):
        bans = Ban.select().where(Ban.server == message.channel.server.id).order_by(Ban.bans.desc())
        px = self.bot.config['command_prefix']
        banlist = []
        limit = 10 if message.content == '{px}{px}banrank'.format(px=px) else 5

        i = 1
        for item in bans.iterator():
            banlist.append('{}. {}: {}'.format(i, item.user, item.bans))

            i += 1
            if i > limit:
                break

        if len(banlist) == 0:
            await cmd.answer('no hay bans registrados')
        else:
            await cmd.answer('\nranking de bans:\n```\n{}\n```'.format('\n'.join(banlist)))


class Ban(BaseModel):
    user = peewee.TextField()
    userid = peewee.TextField(default="")
    bans = peewee.IntegerField(default=0)
    server = peewee.TextField()
    lastban = peewee.DateTimeField(null=True)
