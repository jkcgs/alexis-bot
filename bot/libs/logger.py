import datetime
import logging
import os
from os import path

from bot.defaults import default_log_format, datetime_format, filename_format


def create_logger(name, log_format=default_log_format, log_path=None, logtime=None):
    log = logging.getLogger(name)
    if len(log.handlers) > 1:
        return log

    formatter = logging.Formatter(log_format, datetime_format)

    if log_format is not None:
        log.setLevel(logging.DEBUG)
        stdout_logger = logging.StreamHandler()
        stdout_logger.setLevel(logging.DEBUG)
        stdout_logger.setFormatter(formatter)
        log.addHandler(stdout_logger)

    if log_path is not None:
        if not os.path.isdir(log_path):
            os.makedirs(log_path)

        dt = datetime.datetime.now() if logtime is None else logtime
        filename = dt.strftime(filename_format) + '.log'
        file_logger = logging.FileHandler(path.join(log_path, filename), encoding='utf-8')
        file_logger.setLevel(logging.DEBUG)
        file_logger.setFormatter(formatter)
        log.addHandler(file_logger)

    return log
