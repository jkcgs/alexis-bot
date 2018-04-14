import peewee
import random
from discord import Embed
from datetime import datetime

from bot import Command, BaseModel
from bot.utils import is_int


class BanCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ban'
        self.help = '$[ban-help]'
        self.allow_pm = False
        self.pm_error = '$[ban-pm-error]'
        self.db_models = [Ban]

        self.user_delay = 10

    async def handle(self, cmd):
        if cmd.argc < 1:
            await cmd.answer('$[format]: $PX$NM $[ban-cmd-format]')
            return

        member = await cmd.get_user(cmd.text, member_only=True)
        if member is None:
            await cmd.answer('$[user-not-found]')
            return

        mention_name = member.display_name

        if not cmd.owner and cmd.is_owner(member):
            await cmd.answer('$[ban-owner]')
            return

        if member.id == self.bot.user.id:
            await cmd.answer('$[ban-bot]')
            return

        if member.bot:
            await cmd.answer('$[ban-other-bot]')
            return

        # Evitar que alguien se banee a si mismo
        if self.bot.last_author == member.id:
            await cmd.answer('$[ban-self]')
            return

        # No banear personas que no están en el canal
        if not member.permissions_in(cmd.message.channel).read_messages:
            await cmd.answer('$[ban-other-absent]', locales={'other': mention_name})
            return

        if not random.randint(0, 1):
            await cmd.answer('$[ban-no-luck]', withname=False,
                             locales={'author': cmd.author.display_name, 'other': mention_name})
            return

        user, created = Ban.get_or_create(userid=member.id, server=cmd.message.server.id,
                                          defaults={'user': str(member)})
        update = Ban.update(bans=Ban.bans + 1, lastban=datetime.now(), user=str(member))
        update = update.where(Ban.userid == member.id, Ban.server == cmd.message.server.id)
        update.execute()

        if created:
            await cmd.answer('$[ban-first-one]', withname=False,
                             locales={'author': cmd.author.display_name, 'other': mention_name})
        else:
            await cmd.answer('$[ban-success]', withname=False,
                             locales={
                                 'author': cmd.author.display_name, 'other': mention_name, 'amount': user.bans + 1
                             })


class Bans(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'bans'
        self.help = '$[bans-help]'
        self.allow_pm = False
        self.pm_error = '$[bans-pm-error]'

    async def handle(self, cmd):
        if len(cmd.args) != 1:
            user = cmd.author
        else:
            user = await cmd.get_user(cmd.text)
            if user is None:
                await cmd.answer('$[user-not-found]')
                return

        if cmd.is_owner(user) and not cmd.owner:
            await cmd.answer('$[bans-owner-error]')
            return

        userbans, created = Ban.get_or_create(userid=user.id, server=cmd.message.server.id,
                                              defaults={'user': str(user)})

        locales = None
        if userbans.bans == 0:
            mesg = "```\nException in thread \"main\" cl.discord.alexis.ZeroBansException\n"
            mesg += "    at AlexisBot.main(AlexisBot.java:34)\n```"
        else:
            word = cmd.lng('bans-singular') if userbans.bans == 1 else cmd.lng('bans-plural')
            locales = {'amount': userbans.bans, 'ban': word}

            if user.id == cmd.author.id:
                mesg = '$[bans-self]'
            else:
                mesg = '$[bans-other]'
                locales['other'] = user.display_name

        await cmd.answer(mesg, withname=False, locales=locales)


class SetBans(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'setbans'
        self.help = '$[setbans-help]'
        self.allow_pm = False
        self.pm_error = '$[setbans-pm-error]'
        self.owner_only = True

    async def handle(self, cmd):
        if cmd.argc < 2 or not is_int(cmd.args[-1]):
            await cmd.answer('$[format]: $PX$NM $[setbans-format]')
            return

        mention = await cmd.get_user(' '.join(cmd.args[0:-1]))
        if mention is None:
            await cmd.answer('$[user-not-found]')
            return

        num_bans = int(cmd.args[-1])
        user, _ = Ban.get_or_create(userid=mention.id, server=cmd.message.server.id,
                                    defaults={'user': str(mention)})
        update = Ban.update(bans=num_bans, lastban=datetime.now(), user=str(mention))
        update = update.where(Ban.userid == mention.id, Ban.server == cmd.message.server.id)
        update.execute()

        name = mention.display_name
        if num_bans == 0:
            await cmd.answer('$[setbans-reset]', locales={'other': name})
        else:
            word = cmd.lng('bans-singular') if num_bans == 1 else cmd.lng('bans-plural')
            await cmd.answer('$[setbans-info]', locales={'other': name, 'amount': num_bans, 'ban': word})


class BanRank(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'banrank'
        self.aliases = [self.bot.config['command_prefix'] + 'banrank']
        self.help = '$[banrank-help]'
        self.allow_pm = False
        self.pm_error = '$[setbans-pm-error]'

    async def handle(self, cmd):
        bans = Ban.select().where(Ban.server == cmd.message.channel.server.id).order_by(Ban.bans.desc())
        px = self.bot.config['command_prefix']
        banlist = []
        limit = 10 if cmd.cmdname == '{}{}'.format(px, self.name) else 5

        i = 1
        for item in bans.iterator():
            u = await cmd.get_user(item.userid) or item.user
            banlist.append('{}. {}: {}'.format(i, u, item.bans))

            i += 1
            if i > limit:
                break

        if len(banlist) == 0:
            await cmd.answer('$[banrank-empty]')
        else:
            embed = Embed(title='$[banrank-title]', description='\n'.join(banlist))
            await cmd.answer(embed)


class Ban(BaseModel):
    user = peewee.TextField()
    userid = peewee.TextField(default="")
    bans = peewee.IntegerField(default=0)
    server = peewee.TextField()
    lastban = peewee.DateTimeField(null=True)
