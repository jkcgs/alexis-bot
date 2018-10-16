import logging
import os
import datetime
from os import path

from bot.libs.configuration import StaticConfig

logger_created = False


def get_logger(name):
    global logger_created
    logger = logging.getLogger(name)

    if not logger_created:
        config = StaticConfig('config.yml')
        config.load({'log_path': 'logs', 'log_to_files': True})

        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', '%Y-%m-%d %H:%M:%S')
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

        logger_created = True

    return logger


class TaggedLogger:
    def __init__(self, logger, tag):
        self.logger = logger
        self.tag = tag

    def info(self, message, *args):
        self.logger.info('[{}] {}'.format(self.tag, message), *args)

    def debug(self, message, *args):
        self.logger.debug('[{}] {}'.format(self.tag, message), *args)

    def error(self, message, *args):
        self.logger.error('[{}] {}'.format(self.tag, message), *args)

    def warn(self, message, *args):
        self.logger.warn('[{}] {}'.format(self.tag, message), *args)

    def exception(self, exception):
        self.logger.exception(exception)


log = get_logger('Alexis')
