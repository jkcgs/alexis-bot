import datetime
import logging
import os
from os import path

default_format = '%(asctime)s | %(levelname)-8s | %(name)-8s | %(message)s'
datetime_format = '%Y-%m-%d %H:%M:%S'
filename_format = '%Y-%m-%d_%H-%M-%S'


def create_logger(name, log_format=default_format, log_path=None):
    log = logging.getLogger(name)
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
        filename = datetime.datetime.now().strftime(datetime_format) + '.log'
        file_logger = logging.FileHandler(path.join(log_path, filename), encoding='utf-8')
        file_logger.setLevel(logging.DEBUG)
        file_logger.setFormatter(formatter)
        log.addHandler(file_logger)

    return log
