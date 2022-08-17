from datetime import datetime

import peewee
from bot import Command, BaseModel

optout_cache = {}
noopt_cache = set()


class UserLogOptOut(BaseModel):
    userid = peewee.TextField()
    timestamp = peewee.DateTimeField(default=datetime.now)

    @classmethod
    def user_opted_out(cls, userid):
        if userid in optout_cache:
            return optout_cache[userid]
        if userid in noopt_cache:
            return None

        try:
            result = UserLogOptOut.get(userid=userid).timestamp
            optout_cache[userid] = result
            return result
        except UserLogOptOut.DoesNotExist:
            noopt_cache.add(userid)
            return None
    
    @classmethod
    def user_optout(cls, userid):
        res, created = UserLogOptOut.get_or_create(userid=userid)
        if created and userid in noopt_cache:
            noopt_cache.remove(userid)
        if userid not in optout_cache:
            optout_cache[userid] = res.timestamp


class ModlogOptOut(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'

    db_models = [UserLogOptOut]

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'optout'
        self.help = '$[userlog-optout-help]'
        self.format = '$[userlog-optout-format]'

        global optout_cache
        optout_cache = {u.userid: u.timestamp for u in UserLogOptOut.select()}
    
    async def handle(self, cmd):
        if cmd.argc == 0:
            await cmd.answer('$[userlog-optout-details]', as_embed=True)
            return
        
        if cmd.args[0] != 'yes':
            await cmd.answer('$[userlog-optout-confirm]')
            return

        UserLogOptOut.user_optout(cmd.author.id)
        await cmd.answer('$[userlog-optout-done]')
