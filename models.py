import peewee
db = peewee.SqliteDatabase('database.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class Post(BaseModel):
    id = peewee.CharField()
    permalink = peewee.CharField(null=True)
    over_18 = peewee.BooleanField(default=False)


class Ban(BaseModel):
    user = peewee.TextField()
    bans = peewee.IntegerField(default=0)
    server = peewee.TextField(null=True)


class Redditor(BaseModel):
	name = peewee.TextField()
	posts = peewee.IntegerField(default=0)

class Meme(BaseModel):
    name = peewee.TextField()
    content = peewee.TextField()