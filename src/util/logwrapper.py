import logging

logging.basicConfig(level=logging.INFO)


def debug(message: str):
    logging.debug(message)


def info(message: str):
    logging.info(message)


def warning(message: str):
    logging.warning(message)


def error(message: str):
    logging.error(message)
