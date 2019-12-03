import asyncio
from datetime import datetime
from threading import Thread

import discord
import peewee

from bot import Command, BaseModel


class UpdateUsername(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.db_models = [UserNameReg]
        self.updating = False
        self.updated = False
        self.ready = False
        self.loop = asyncio.new_event_loop()

    async def on_ready(self):
        t = Thread(target=self.start_update, args=(self.loop,))
        t.start()

    def start_update(self, loop):
        self.log.debug('Running initial update...')
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_all())
        self.ready = True

    async def on_member_join(self, member):
        if self.ready and not self.updating:
            self.bot.loop.create_task(self.do_it(member))

    async def on_member_update(self, before, after):
        if self.ready and not self.updating:
            self.bot.loop.create_task(self.do_it(after))

    async def run_all(self):
        if self.updating or self.updated:
            return

        self.log.debug('Updating users\' names...')
        c = self.all()

        if c is not None:
            self.log.debug('Users updated: %i', c)
        else:
            self.log.debug('No users were updated')

    def all(self):
        if self.updating or self.updated:
            return

        self.updating = True

        # Retrieve every last user name
        # SELECT * FROM usernamereg t1 WHERE timestamp = (
        #   SELECT MAX(timestamp) FROM t1 WHERE t1.timestamp = usernamereg.timestamp
        # ) ORDER BY timestamp DESC
        u_alias = UserNameReg.alias()
        j = {u.userid: u.name for u in
             UserNameReg.select().where(
                 UserNameReg.timestamp == u_alias.select(peewee.fn.MAX(u_alias.timestamp)).where(
                     u_alias.userid == UserNameReg.userid)
             ).order_by(
                 UserNameReg.timestamp.desc()
             )}

        # Filter by unregistered users
        k = [{'userid': m.id, 'name': m.name}
             for m in self.bot.get_all_members() if m.id not in j or j[m.id] != m.name]
        k = [i for n, i in enumerate(k) if i not in k[n + 1:]]  # https://stackoverflow.com/a/9428041

        # Register new users' names
        with self.bot.db.atomic():
            for idx in range(0, len(k), 100):
                UserNameReg.insert_many(k[idx:idx + 100]).execute()

        self.updating = False
        self.updated = True
        return len(k)

    async def do_it(self, user):
        if not isinstance(user, discord.User) and not isinstance(user, discord.Member):
            raise RuntimeError('user argument can only be a discord.User or discord.Member')

        with self.bot.db.atomic():
            r = UserNameReg.select().where(UserNameReg.userid == user.id).order_by(UserNameReg.timestamp.desc()).limit(1)
            u = r.get() if r.count() > 0 else None

            if r.count() == 0 or u.name != user.name:
                old = '(none)' if u is None else u.name
                self.log.debug('Updating user name "%s" -> "%s" ID %s', old, user.name, user.id)
                UserNameReg.create(userid=user.id, name=user.name)
                return True

        return False


def get_names(userid):
    xd = UserNameReg.select().where(UserNameReg.userid == userid).order_by(UserNameReg.timestamp.desc()).limit(10)
    return [u.name for u in xd]


class UserNameReg(BaseModel):
    userid = peewee.TextField()
    name = peewee.TextField()
    timestamp = peewee.DateTimeField(default=datetime.now)