from datetime import datetime
import logging


logging.basicConfig(filename='debug.log', level=logging.DEBUG)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def debug(message: str):
    logging.debug('[%s] %s', now(), message)


def log(message: str, do_not_print=False):
    if not do_not_print:
        print(f'[{now()}] Info - {message}')
    logging.info('[%s] %s', now(), message)


def error(message: str):
    print(f'[{now()}] Error - {message}')
    logging.error('[%s] %s', now(), message)
