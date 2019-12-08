import logging
import sys


def create_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    console_out = logging.StreamHandler(sys.stdout)
    console_out.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_out.setFormatter(formatter)
    logger.addHandler(console_out)

    return logger
