from bot.libs.configuration import StaticConfig
from bot.libs.logger import create_logger, default_format


def new_logger(name):
    config = StaticConfig('config.yml')
    config.load({
        'log_path': 'logs',
        'log_to_files': False,
        'log_format': default_format
    })

    log_path = None if not config['log_to_files'] else config['log_path']
    newlog = create_logger(name, config['log_format'], log_path)
    return newlog
