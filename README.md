## instagram-bio-sotw

This repository contains the source files for `instagram-bio-sotw`, a Python application that allows you to update your Instagram bio with your Song of the Week from Last.fm.
"Song of the Week" here is defined as the most played song during the previous 7-day period.

### Setup
1. Create a Python virtual environment.
   ```shell script
   python -m venv venv
   source ./venv/bin/activate
   
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. Configure the parameters `config.json.example` and rename it to `config.json`.

### Run
To run the application once, run `python main.py`.
If you have 2FA enabled on your account, you will be prompted to enter the verification code on the first login attempt.
Subsequent login attempts will reuse the same login token.

To setup a cron job to automatically run the application weekly, run `python cron.py`.
