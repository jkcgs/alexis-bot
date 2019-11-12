import logging
import os
import datetime
from os import path

from bot.libs.configuration import StaticConfig


def create_logger(name):
    logger = logging.getLogger(name)
    config = StaticConfig('config.yml')
    config.load({
        'log_path': 'logs',
        'log_to_files': False,
        'log_format': '%(asctime)s | %(levelname)-8s | %(name)-8s | %(message)s'
    })

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(config['log_format'], '%Y-%m-%d %H:%M:%S')
    stdout_logger = logging.StreamHandler()
    stdout_logger.setLevel(logging.DEBUG)
    stdout_logger.setFormatter(formatter)
    logger.addHandler(stdout_logger)

    if config['log_to_files']:
        try:
            if not os.path.isdir(config['log_path']):
                os.makedirs(config['log_path'])
            log_format = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            file_logger = logging.FileHandler(
                path.join(config['log_path'], '{}.log'.format(log_format)), encoding='utf-8')
            file_logger.setLevel(logging.DEBUG)
            file_logger.setFormatter(formatter)
            logger.addHandler(file_logger)
        except OSError as e:
            logger.exception(e)
            raise

    return logger


log = create_logger('Core')
