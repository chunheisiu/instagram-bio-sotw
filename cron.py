import argparse
import json
import os
from typing import Dict, Union

from crontab import CronTab

from log_helper import get_logger

# Load config
with open('config.json') as config_file:
    config_file = json.load(config_file)

# Init logger
logger = get_logger(config=config_file, module=__name__, handler_type='stream')


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
    job = cron.new(command=f'cd {path} && {path}/{config["CRON"]["VENV"]}/bin/python {path}/main.py '
                           f'-l file',
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


def main():
    # Init Arg Parser
    parser = argparse.ArgumentParser(
        prog='instagram-bio-sotw',
        description='Update your Instagram bio with your Song of the Week from Last.fm.'
    )
    parser.add_argument('operation', default='add')
    args = parser.parse_args()

    # Determine what operation to perform according to sys args
    operation: str = args.operation
    if operation.lower() == 'add':
        add_job(config_file)
    elif operation.lower() == 'remove':
        remove_job(config_file)


if __name__ == '__main__':
    main()
