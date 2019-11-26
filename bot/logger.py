from bot.libs.configuration import StaticConfig
from bot.libs.logger import create_logger


def new_logger(name):
    config = StaticConfig('config.yml')
    config.load({
        'log_path': 'logs',
        'log_to_files': False,
        'log_format': '%(asctime)s | %(levelname)-8s | %(name)-8s | %(message)s'
    })

    log_path = None if not config['log_to_files'] else config['log_path']
    return create_logger(name, config['log_format'], log_path)


log = new_logger('Core')
