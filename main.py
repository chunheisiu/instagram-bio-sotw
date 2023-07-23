import argparse
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import pyotp
import requests
import zhon.hanzi
from instagrapi import Client
from instagrapi.exceptions import ClientError, TwoFactorRequired

from log_helper import get_logger

# Load config
with open('config.json') as config_file:
    config = json.load(config_file)

# Init Arg Parser
parser = argparse.ArgumentParser(
    prog='instagram-bio-sotw',
    description='Update your Instagram bio with your Song of the Week from Last.fm.'
)
parser.add_argument('-l', '--log', default='stream')
args = parser.parse_args()

# Init logger
handler_type: str = args.log_handler_type
logger = get_logger(config=config, module=__name__, handler_type=handler_type)


def get_formatted_date(fmt: str = '%m/%d', rm_zero_pad: bool = True) -> str:
    """
    Format the date of start of week.

    :param fmt: format of the date
    :param rm_zero_pad: remove zero padding from date?
    :return: formatted current date
    """
    today = datetime.now().date()
    date = today - timedelta(days=(today.weekday() + 1) % 7)
    date = date.strftime(fmt)
    if rm_zero_pad:
        date = date.lstrip('0').replace('/0', '/')
    return date


def get_lastfm_user_sotw(username: str) -> Dict[str, str]:
    """
    Retrieve the Song of the Week for a user from Last.fm.

    :param username: username of the user
    :return: Dict of `{artist, track}`
    """
    last_fm_url = f'https://ws.audioscrobbler.com/2.0/'
    last_fm_params = {'method': 'user.gettoptracks',
                      'format': 'json',
                      'user': username,
                      'api_key': config['LAST_FM']['KEY'],
                      'limit': 1,
                      'period': '7day'}

    # Retrieve the SOTW from Last.fm
    logger.info('Retrieving Song of the Week from Last.fm...')
    r = requests.get(last_fm_url, params=last_fm_params, headers={'User-Agent': 'Mozilla/5.0'})
    track = r.json()['toptracks']['track']

    if len(track) < 1:
        raise IndexError('At least one track is expected to return from Last.fm')
    track = track[0]
    # Extract the artist and tack name from the JSON response
    track_dict = {'artist': track['artist']['name'], 'name': track['name']}
    logger.info(f'Song of the Week: {track_dict}')
    logger.info('Retrieved Song of the Week from Last.fm')
    return track_dict


def format_sotw(sotw: Dict[str, str]) -> str:
    """
    Format the Song of the Week.
    :param sotw: dict of {artist, track}
    :return: SOTW formatted as "artist – track name"
    """
    sotw_str = f'{sotw["artist"]} – {sotw["name"]}'
    # Separate CJK and non-CJK characters
    sotw_str_non_cjk = re.findall(f'[^{zhon.hanzi.characters}]', sotw_str)
    sotw_str_cjk = re.findall(f'[{zhon.hanzi.characters}]', sotw_str)
    # Calculate the length of the string with len(CJK characters) * 2
    sotw_str_len = len(sotw_str_non_cjk) + 2 * len(sotw_str_cjk)
    # Append \n if string is longer than 25 characters
    return f'\n{sotw_str}' if sotw_str_len > 25 else sotw_str


def init_ig_client(settings_file_dir: Path, username: str, password: str, otp: Optional[str] = None) -> Client:
    """
    Initialize the Instagram client.

    :param settings_file_dir: settings file directory
    :param username: username of the account
    :param password: password of the account
    :param otp: OTP code of the account
    :return: Initialized Instagram client
    """
    settings_file = Path(f'{settings_file_dir}/settings_{username}.json')
    client = Client()

    try:
        if os.path.isfile(settings_file):
            # Reuse login settings if existing settings is found
            logger.info('Existing settings found')
            client.load_settings(settings_file)
        logger.info(f'Attempt to login with username {username}...')
        client.login(username=username, password=password)
    except TwoFactorRequired:
        # 2FA authentication is required
        logger.info('Login failed: 2FA required')
        if otp is not None:
            totp = pyotp.TOTP(otp)
            verification_code = totp.now()
        else:
            verification_code = input('Enter verification code: ')
        try:
            # Attempt to log in with verification code
            logger.info(f'Attempt to login with username {username}...')
            client.login(username=username, password=password, verification_code=verification_code)
        except ClientError as e:
            logger.error(e.response)
    except ClientError as e:
        logger.error(e.response)

    if client:
        # Save login settings
        client.dump_settings(settings_file)

    return client


def update_ig_profile(client: Client, profile: dict):
    """
    Update Instagram profile of the current user.

    :param client: Instagram client
    :param profile: Dict of profile to replace
    :return:
    """
    try:
        res = client.account_edit(**profile)
        if res:
            logger.info('Instagram profile successfully updated')
    except Exception as e:
        logger.error(e)


def main():
    """
    Main method.

    :return:
    """
    # Init settings directory
    settings_file_dir = Path(config['INSTAGRAM']['SETTINGS_FILE_DIR'])
    settings_file_dir.mkdir(parents=True, exist_ok=True)

    # Get the current date
    curr_date = get_formatted_date(config['DATE_FMT'])

    # Get the SOTW from Last.fm
    user_sotw = get_lastfm_user_sotw(config['LAST_FM']['USERNAME'])
    user_sotw = format_sotw(user_sotw)

    # Load the profile from config and update with current date and SOTW
    instagram_config = config['INSTAGRAM']
    ig_profile = instagram_config.get('PROFILE')
    ig_profile['biography'] = ig_profile['biography'].format(date=curr_date, track=user_sotw)

    # Initialize the Instagram client and update profile
    ig_client = init_ig_client(
        settings_file_dir=settings_file_dir,
        username=instagram_config.get('USERNAME'),
        password=instagram_config.get('PASSWORD'),
        otp=instagram_config.get('OTP')
    )
    if ig_client:
        update_ig_profile(ig_client, ig_profile)


if __name__ == '__main__':
    main()
