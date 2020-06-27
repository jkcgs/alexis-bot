import logging

import peewee
from playhouse.db_url import connect

from bot.lib.configuration import BotConfiguration
from bot.logger import new_logger

peewee_log = new_logger('peewee')
peewee_log.setLevel(logging.INFO)


class BotDatabase:
    _db = None

    @staticmethod
    def get_instance():
        cfg = BotConfiguration.get_instance()
        dburl = cfg['database_url']
        if dburl.startswith('mysql:'):
            dburl += '&amp;' if '?' in dburl else '?'
            dburl += 'charset=utf8mb4;'

        if BotDatabase._db is None:
            BotDatabase._db = connect(dburl, autorollback=True)

        return BotDatabase._db

    @staticmethod
    def initialize():
        ins = BotDatabase.get_instance()
        ins.create_tables([ServerConfig], safe=True)
        return ins


class BaseModel(peewee.Model):
    class Meta:
        database = BotDatabase.get_instance()


class ServerConfig(BaseModel):
    serverid = peewee.TextField()
    name = peewee.TextField()
    value = peewee.TextField(default='')
