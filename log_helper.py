import logging

log_fmt = '[%(asctime)s][%(levelname)s][%(module)s: %(funcName)s] %(message)s'
date_fmt = '%m/%d/%Y %H:%M:%S'

logging.basicConfig(format=log_fmt, datefmt=date_fmt)


def get_logger(module: str):
    """
    Get or initialize the logger for the module.
    In each module, add::
     >>> from log_helper import get_logger
     >>> logger = get_logger(__name__)
    Then, call :meth:`logger.info` or :meth:`logger.error`
    based on the level of severity.
    :param module: module name
    :return: logger for the module
    """
    logger = logging.getLogger(module)
    logger.setLevel(logging.INFO)
    return logger
