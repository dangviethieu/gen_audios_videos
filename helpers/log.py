import logging
import sys
import os
import datetime


class ScreenFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    green = "\x1b[1;32m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[1;34m"
    light_blue = "\x1b[1;36m"
    purple = "\x1b[1;35m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)-10s - %(levelname)-8s - %(filename)-8s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(fmt=log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


def setup_custom_logger(name):
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger
    logger.setLevel(logging.DEBUG)

    # file handle
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)-16s - %(levelname)-8s - %(filename)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = logging.FileHandler('logs/{}.txt'.format(datetime.datetime.now().strftime('%Y-%m-%d')), 'a', 'utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # screen handle
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(ScreenFormatter())
    logger.addHandler(screen_handler)

    return logger

