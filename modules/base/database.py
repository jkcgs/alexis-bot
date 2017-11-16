import peewee

db = peewee.SqliteDatabase('database.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class ServerConfig(BaseModel):
    serverid = peewee.TextField()
    name = peewee.TextField()
    value = peewee.TextField(default='')


class ServerConfigMgr:
    def __init__(self):
        self.q = ServerConfig.select().execute()
        self.sv = {}

        for conf in list(self.q):
            if conf.serverid not in self.sv:
                self.sv[conf.serverid] = {}
            self.sv[conf.serverid][conf.name] = conf.value

    def get(self, svid, name):
        return '' if name not in self.sv[svid] else self.sv[svid][name]

    def set(self, svid, name, value):
        q, _ = ServerConfig.get_or_create(serverid=svid, name=name)
        q.value = value
        q.save()
        self._local_save(svid, name, value)

        return q.value

    def _local_save(self, svid, name, value):
        if svid not in self.sv:
            self.sv[svid] = {}

        self.sv[svid][name] = value
