from datetime import datetime
import peewee

from modules.base.command import Command
from modules.base.database import BaseModel
import random


class BanCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ban'
        self.help = 'Banea (simbólicamente) a un usuario'
        self.allow_pm = False
        self.pm_error = 'banéame esta xd'
        self.db_models = [Ban]

        self.user_delay = 10

    async def handle(self, message, cmd):
        if len(cmd.args) > 1 or len(message.mentions) != 1:
            await cmd.answer('Formato: !ban <mención>')
            return

        mention = message.mentions[0]
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

        # Actualizar id del último que usó un comando (omitir al mismo bot)
        if self.bot.last_author is None or not cmd.own:
            self.bot.last_author = message.author.id

        # Evitar que alguien se banee a si mismo
        if self.bot.last_author == mention.id:
            await cmd.answer('no hagai trampa po wn xd')
            return

        if not random.randint(0, 1):
            await cmd.answer('¡**{}** intentó banear a **{}**, quien se salvó de milagro!'
                             .format(cmd.author.mention, mention_name))
            return

        user, created = Ban.get_or_create(userid=mention.id, server=message.server.id,
                                          defaults={'user': str(mention)})
        update = Ban.update(bans=Ban.bans + 1, lastban=datetime.now(), user=str(mention))
        update = update.where(Ban.userid == mention.id, Ban.server == message.server.id)
        update.execute()

        if created:
            text = 'Uff, ¡**{}** le ha dado a **{}** su primer ban!'.format(cmd.author.mention, mention_name)
        else:
            text = '¡**{}** ha baneado a **{}** sumando **{} baneos**!'
            text = text.format(cmd.author.mention, mention_name, user.bans + 1)
        await cmd.answer(text)


class Bans(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'bans'
        self.help = 'Muestra la cantidad de bans de una persona'
        self.allow_pm = False
        self.pm_error = 'no po wn que te crei'

    async def handle(self, message, cmd):
        if len(cmd.args) > 1 or len(message.mentions) != 1:
            await cmd.answer('Formato: !ban <mención>')
            return

        mention = message.mentions[0]
        if cmd.is_owner(mention):
            mesg = 'Te voy a decir la cifra exacta: Cuatro mil trescientos cuarenta y '
            mesg += 'cuatro mil quinientos millones coma cinco bans, ese es el valor.'
            await cmd.answer(mesg)
            return

        name = mention.nick if mention.nick is not None else mention.name
        user, created = Ban.get_or_create(userid=mention.id, server=message.server.id,
                                          defaults={'user': str(mention)})

        if user.bans == 0:
            mesg = "```\nException in thread \"main\" java.lang.NullPointerException\n"
            mesg += "    at AlexisBot.main(AlexisBot.java:34)\n```"
        else:
            word = 'ban' if user.bans == 1 else 'bans'
            if user.bans == 2:
                word = '~~papás~~ bans'

            mesg = '**{}** tiene {} {}'.format(name, user.bans, word)

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
        is_valid = not (len(cmd.args) < 2 or len(message.mentions) != 1)
        num_bans = 0

        try:
            num_bans = int(cmd.args[1])
        except (IndexError, ValueError):
            is_valid = False

        if not is_valid:
            await cmd.answer('Formato: !setbans <mención> <cantidad>')
            return

        mention = message.mentions[0]
        user, _ = Ban.get_or_create(userid=mention.id, server=message.server.id,
                                    defaults={'user': str(mention)})
        update = Ban.update(bans=num_bans, lastban=datetime.now(), user=str(mention))
        update = update.where(Ban.userid == mention.id, Ban.server == message.server.id)
        update.execute()

        name = mention.display_name
        if num_bans == 0:
            mesg = 'Bans de **{}** reiniciados xd'.format(name)
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
        banlist = []
        limit = 10 if message.content == '!!banrank' else 5

        i = 1
        for item in bans.iterator():
            banlist.append('{}. {}: {}'.format(i, item.user, item.bans))

            i += 1
            if i > limit:
                break

        if len(banlist) == 0:
            await cmd.answer('No hay bans registrados')
        else:
            await cmd.answer('Ranking de bans:\n```\n{}\n```'.format('\n'.join(banlist)))


class BanMigrate(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'banmigrate'
        self.help = 'Migra los bans antiguos al nuevo formato'
        self.allow_pm = False
        self.pm_error = 'a quien vai a banear por pm, como tan wn'
        self.owner_only = True

    async def handle(self, message, cmd):
        try:
            # Revisar columnas actuales para ver si es necesario actualizar el modelo
            cols = self.bot.db.get_columns('ban')
            has_lastban = False
            has_userid = False
            for col in cols:
                if col.name == 'lastban':
                    has_lastban = True
                if col.name == 'userid':
                    has_userid = True

            # Actualizar si es necesario
            if not has_lastban or not has_userid:
                from playhouse.migrate import SqliteMigrator
                from playhouse.migrate import migrate
                migrator = SqliteMigrator(self.bot.db)
                with self.bot.db.transaction():
                    if not has_lastban:
                        migrate(migrator.add_column('ban', 'lastban', peewee.DateTimeField(null=True)))
                    if not has_userid:
                        migrate(migrator.add_column('ban', 'userid', peewee.TextField(default='')))
                    self.log.debug('Modelo de base de datos actualizado')
            else:
                self.log.debug('El modelo de la base de datos ya está actualizado')
        except Exception as e:
            self.log.exception(e)

        users = list(self.bot.get_all_members())
        bans = Ban.select().where(Ban.userid == '', Ban.server == message.server.id)
        num_users = 0

        # Agregar userid a usuarios que no lo tengan registrado
        for ban in bans.iterator():
            num_users += 1
            sel_user = None
            for user in users:
                if str(user) == ban.user:
                    sel_user = user
                    break

            if sel_user is None:
                continue

            update = Ban.update(userid=sel_user.id)
            update = update.where(Ban.user == ban.user, Ban.server == message.server.id)
            update.execute()

        self.log.debug('%i usuarios actualizados', num_users)
        await cmd.answer('{} usuarios actualizados'.format(num_users))


class Ban(BaseModel):
    user = peewee.TextField()
    userid = peewee.TextField(default="")
    bans = peewee.IntegerField(default=0)
    server = peewee.TextField()
    lastban = peewee.DateTimeField(null=True)
