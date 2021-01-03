import json
import os
import sys
from typing import Dict, Union

from crontab import CronTab

from log_helper import get_logger


def add_job(config: Dict[str, Union[dict, str]]):
    """
    Add a cron job to CronTab.

    :param config: config dict
    :return:
    """
    # Get current directory
    path = os.getcwd()

    # Extract config params
    job_comment = config['CRON']['COMMENT']
    job_pattern = config['CRON']['SCHEDULE']

    # Set up CronTab
    cron = CronTab(user=config['CRON']['USERNAME'])

    # Remove existing job and add job
    cron.remove_all(comment=job_comment)
    job = cron.new(command=f'cd {path} && {path}/{config["CRON"]["VENV"]}/bin/python {path}/main.py file',
                   comment=job_comment)
    job.setall(job_pattern)
    cron.write()

    logger.info(f'Added cron job {job_comment} with pattern {job_pattern}')


def remove_job(config: dict):
    """
    Remove a cron job from CronTab.

    :param config: config dict
    :return:
    """
    # Extract config param
    job_comment = config['CRON']['COMMENT']

    # Set up CronTab and remove job
    cron = CronTab(user=config['CRON']['USERNAME'])
    cron.remove_all(comment=job_comment)
    cron.write()

    logger.info(f'Removed cron job {job_comment}')


# Load config
with open('config.json') as config_file:
    config_file = json.load(config_file)

# Init logger
logger = get_logger(config=config_file, module=__name__, handler_type='stream')

# Determine what operation to perform according to sys args
if len(sys.argv) == 1:
    add_job(config_file)
elif len(sys.argv) == 2:
    op = sys.argv[1].lower()
    if op == 'add':
        add_job(config_file)
    elif op == 'remove':
        remove_job(config_file)
