import peewee
db = peewee.SqliteDatabase('database.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class Post(BaseModel):
    id = peewee.CharField()
    permalink = peewee.CharField()
    over_18 = peewee.BooleanField()


class Ban(BaseModel):
    user = peewee.TextField()
    bans = peewee.IntegerField(default=0)
