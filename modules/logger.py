import logging
import os
import datetime


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', '%d-%m-%Y %H:%M:%S')
    stdout_logger = logging.StreamHandler()
    stdout_logger.setLevel(logging.DEBUG)
    stdout_logger.setFormatter(formatter)
    logger.addHandler(stdout_logger)

    try:
        if not os.path.isdir('logs/'):
            os.makedirs('logs/')
        log_format = datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        file_logger = logging.FileHandler('logs/{}.log'.format(log_format), encoding='utf-8')
        file_logger.setLevel(logging.DEBUG)
        file_logger.setFormatter(formatter)
        logger.addHandler(file_logger)
    except OSError as e:
        logger.exception(e)
        raise

    return logger
