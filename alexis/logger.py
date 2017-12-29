import logging
import os
import datetime

logger_created = False


def get_logger(name):
    global logger_created
    logger = logging.getLogger(name)

    if not logger_created:
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

        logger_created = True

    return logger


log = get_logger('Alexis')
