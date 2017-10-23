import peewee

db = peewee.SqliteDatabase('database.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class ServerConfig(BaseModel):
    serverid = peewee.TextField()
    name = peewee.TextField()
    value = peewee.TextField(default='')
