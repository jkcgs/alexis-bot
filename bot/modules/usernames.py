import asyncio
from datetime import datetime
from threading import Thread

import peewee
from peewee import fn

from bot import Command, BaseModel


class UserNameReg(BaseModel):
    userid = peewee.TextField()
    name = peewee.TextField()
    timestamp = peewee.DateTimeField(default=datetime.now)


class UsernamesRegistry(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    db_models = [UserNameReg]

    def __init__(self, bot):
        super().__init__(bot)
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
        if not self.ready or self.updating:
            return

        last = self.get_last_name(member)
        if last is not None and last.name != member.name:
            UserNameReg.create(userid=member.id, name=member.name)

    async def on_user_update(self, before, after):
        if not self.ready or self.updating or not before or before.name == after.name:
            return

        UserNameReg.create(userid=after.id, name=after.name)

    async def run_all(self):
        if self.updating or self.updated:
            return

        self.log.debug('Updating users\' names...')
        c = self.all()

        if c is not None:
            self.log.debug('Users\' names updated: %i', c)
        else:
            self.log.debug('No users were updated')

    def all(self):
        if self.updating or self.updated:
            return

        self.updating = True

        # Retrieve every last user name
        """
        SELECT t1.* FROM usernamereg t1
        JOIN (
            SELECT userid, max(timestamp) max_timestamp
            FROM usernamereg
            GROUP BY userid
        ) t2
        ON t1.userid = t2.userid AND t1.timestamp = t2.max_timestamp
        ORDER BY t1.timestamp DESC
        """
        u_alias = UserNameReg.alias()
        subq = u_alias.select(
            u_alias.userid, fn.MAX(u_alias.timestamp).alias('max_ts')
        ).group_by(u_alias.userid)
        prediq = ((UserNameReg.userid == subq.c.userid) & (UserNameReg.timestamp == subq.c.max_ts))
        query = UserNameReg.select().join(subq, on=prediq).order_by(UserNameReg.timestamp.desc())
        self.log.debug('Query created: %s', query)

        j = {u.userid: u.name for u in query}
        self.log.debug('Query result mapped: %i users', len(j.keys()))

        # Filter by unregistered users
        k = [{'userid': m.id, 'name': m.name}
             for m in self.bot.get_all_members() if str(m.id) not in j or j[str(m.id)] != m.name]
        k = [i for n, i in enumerate(k) if i not in k[n + 1:]]  # https://stackoverflow.com/a/9428041

        # Register new users' names
        with self.bot.db.atomic():
            for idx in range(0, len(k), 100):
                UserNameReg.insert_many(k[idx:idx + 100]).execute()

        self.updating = False
        self.updated = True
        return len(k)

    @staticmethod
    def get_last_name(user):
        r = UserNameReg.select().where(UserNameReg.userid == user.id) \
            .order_by(UserNameReg.timestamp.desc()).limit(1)
        u = r.get() if r.count() > 0 else None
        return u

    @staticmethod
    def get_names(userid):
        xd = UserNameReg.select().where(UserNameReg.userid == userid).order_by(UserNameReg.timestamp.desc()).limit(10)
        return [u.name for u in xd]
