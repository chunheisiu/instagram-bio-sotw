import logging
from pathlib import Path
from typing import Dict, Union, Optional


def get_logger(config: Dict[str, Union[dict, str]], module: str, handler_type: Optional[str] = 'stream'):
    """
    Get or initialize the logger for the module.
    In each module, add:
     >>> from log_helper import get_logger
     >>> module_logger = get_logger(__name__)
    Then, call :meth:`logger.info` or :meth:`logger.error`
    based on the level of severity.

    :param config: config params
    :param module: module name
    :param handler_type: handler type (file or stream)
    :return: logger for the module
    """
    # Create logger
    logger = logging.getLogger(module)
    logger.setLevel(logging.INFO)
    # Set logger format and date format with config params
    log_fmt = config['LOGGER']['FORMAT']
    date_fmt = config['LOGGER']['DATE_FORMAT']
    formatter = logging.Formatter(fmt=log_fmt, datefmt=date_fmt)
    # Determine handler type
    # Default handler is StreamHandler
    handler = None
    if handler_type.lower() == 'stream':
        handler = logging.StreamHandler()
    elif handler_type.lower() == 'file':
        log_file_dir = Path(config['LOGGER']['LOG_FILE_DIR'])
        log_file_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(f'{log_file_dir}/{module}.log')
    # Set formatter and add handler
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
