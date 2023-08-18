from pathlib import Path
from subprocess import CalledProcessError
import json

from helpers import get_new_token
from models import Setting

CONFIG = Path('/etc/service-status-indicator/.config.json')
TOKEN = 'insecure'
DEFAULT_REFRESH_INTERVAL = 60

# Initialize the configuration file
if not CONFIG.exists() or CONFIG.stat().st_size == 0:
    try:
        TOKEN = get_new_token()
    except CalledProcessError as err:
        print('Error on initial token generation (openssl missing?)')

    with open(CONFIG, 'w', encoding='utf8') as file:
        json.dump({
            'default-refresh-interval': DEFAULT_REFRESH_INTERVAL,
            'token': TOKEN
        }, file)


def get_setting(setting: Setting):
    with open(CONFIG, 'r', encoding='utf8') as config_file:
        return dict(json.load(config_file)).get(setting)


def set_setting(setting: Setting, value):
    with open(CONFIG, 'r', encoding='utf8') as config_file:
        config = dict(json.load(config_file))
        config[setting] = value
    with open(CONFIG, 'w', encoding='utf8') as config_file:
        json.dump(config, config_file)
