import itertools
from bot.database import BotDatabase, BaseModel
from bot.manager import Manager


def run():
    print('Loading models...')
    models = [
        x for x in itertools.chain.from_iterable(
            cls.db_models for cls in [
                cls for cls in Manager.get_mods() if len(getattr(cls, 'db_models', [])) > 0
            ]
        ) if issubclass(x, BaseModel)
    ]

    print('Models loaded ({}):'.format(len(models)), models)
    print('Creating tables...')
    BotDatabase.initialize().create_tables(models)
    print('Tables created!')


if __name__ == '__main__':
    run()
