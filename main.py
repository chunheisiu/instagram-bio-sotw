import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

import requests
import zhon.hanzi
from instagram_private_api import Client, ClientTwoFactorRequiredError, ClientError

from json_helper import to_json, from_json
from log_helper import get_logger

# Load config
with open('config.json') as config_file:
    config = json.load(config_file)

# Init logger
handler_type = 'stream'
if len(sys.argv) == 2:
    handler_type = sys.argv[1]
logger = get_logger(config=config, module=__name__, handler_type=handler_type)

# Init settings directory
settings_file_dir = Path(config['INSTAGRAM']['SETTINGS_FILE_DIR'])
settings_file_dir.mkdir(parents=True, exist_ok=True)


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
    LAST_FM_URL = f'http://ws.audioscrobbler.com/2.0/'
    last_fm_params = {'method': 'user.gettoptracks',
                      'format': 'json',
                      'user': username,
                      'api_key': config['LAST_FM']['KEY'],
                      'limit': 1,
                      'period': '7day'}

    # Retrieve the SOTW from Last.fm
    r = requests.get(LAST_FM_URL, params=last_fm_params, headers={'User-Agent': 'Mozilla/5.0'})
    track = r.json()['toptracks']['track']
    logger.info('Retrieved Song of the Week from Last.fm')
    if len(track) < 1:
        raise IndexError('At least one track is expected to return from Last.fm')
    track = track[0]
    # Extract the artist and tack name from the JSON response
    track_dict = {'artist': track['artist']['name'], 'name': track['name']}
    logger.info(f'Song of the Week: {track_dict}')
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


def onlogin_callback(api, new_settings_file):
    """
    Callback function for Instagram client login.

    :param api: Instagram client
    :param new_settings_file: settings file path
    :return:
    """
    cache_settings = api.settings
    with open(new_settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        logger.info(f'Settings saved: {new_settings_file!s}')


def init_ig_client(username: str, password: str) -> Client:
    """
    Initialize the Instagram client.

    :param username: username of the account
    :param password: password of the account
    :return: Initialized Instagram client
    """
    settings_file = f'{settings_file_dir}/settings_{username}.json'
    api = Client(username, password, on_login=lambda x: onlogin_callback(x, settings_file))
    try:
        if not os.path.isfile(settings_file):
            # Create a new login if existing settings is not found
            logger.error(f'Unable to find file: {settings_file!s}')
            logger.info(f'Attempt new login request for {username}...')
            api.login()
        else:
            # Reuse saved settings
            with open(settings_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            logger.info(f'Reusing settings: {settings_file!s}')
            api = Client(username, password, settings=cached_settings)
        logger.info('Logged in')
        return api
    except ClientTwoFactorRequiredError as e:
        logger.info('2FA Required')
        # 2FA authentication is required
        response = json.loads(e.error_response)
        two_factor_info = response['two_factor_info']
        two_factor_identifier = two_factor_info['two_factor_identifier']
        verification_code = input('Enter verification code: ')
        try:
            api.login2fa(two_factor_identifier, verification_code)
            logger.info('Logged in')
            return api
        except ClientError as e:
            logger.error(e.error_response)
    except ClientError as e:
        logger.error(e.error_response)


def update_ig_profile(api: Client, profile: dict):
    """
    Update Instagram profile of the current user.

    :param api: Instagram client
    :param profile: Dict of profile to replace
    :return:
    """
    try:
        res = api.edit_profile(**profile)
        logger.info(f'status: {res["status"]}')
    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    # Get the current date
    curr_date = get_formatted_date(config['DATE_FMT'])

    # Get the SOTW from Last.fm
    user_sotw = get_lastfm_user_sotw(config['LAST_FM']['USERNAME'])
    user_sotw = format_sotw(user_sotw)

    # Load the profile from config and update with current date and SOTW
    ig_profile = config['INSTAGRAM']['PROFILE']
    ig_profile['biography'] = ig_profile['biography'].format(date=curr_date, track=user_sotw)

    # Initialize the Instagram client and update profile
    ig_client = init_ig_client(config['INSTAGRAM']['USERNAME'], config['INSTAGRAM']['PASSWORD'])
    if ig_client:
        update_ig_profile(ig_client, ig_profile)
