import json
import os

from crontab import CronTab

from log_helper import get_logger

# Load config
with open('config.json') as config_file:
    config = json.load(config_file)

# Init logger
logger = get_logger(__name__)

# Get current directory
path = os.getcwd()

# Set up CronTab
job_comment = config['CRON']['COMMENT']
job_pattern = config['CRON']['SCHEDULE']

cron = CronTab(user=config['CRON']['USERNAME'])
cron.remove_all(comment=job_comment)
job = cron.new(command=f'cd {path} && {path}/{config["CRON"]["VENV"]}/bin/python {path}/main.py',
               comment=job_comment)
job.setall(job_pattern)
cron.write()

logger.info(f'Finished writing cron {job_comment} with pattern {job_pattern}')
