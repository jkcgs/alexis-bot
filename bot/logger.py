from datetime import datetime

from bot.lib.configuration import BotConfiguration
from bot.lib.logger import create_logger

start_time = datetime.now()


def new_logger(name):
    config = BotConfiguration.get_instance()
    log_path = None if not config['log_to_files'] else config['log_path']
    newlog = create_logger(name, config['log_format'], log_path, start_time)
    return newlog
