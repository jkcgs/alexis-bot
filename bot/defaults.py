# This module contains default definitions for bot settings and whatever

default_log_format = '%(asctime)s | %(levelname)-8s | %(name)s || %(message)s'

config = {
    'token': '',
    'debug': False,
    'command_prefix': '!',
    'database_url': 'sqlite:///db.sqlite3',
    'playing': '!help',
    'bot_owners': ['130324995984326656'],
    'owner_role': 'AlexisMaster',
    'ext_modpath': '',
    'subreddit': [],
    'default_lang': 'es',
    'log_path': 'logs',
    'log_to_files': False,
    'log_format': default_log_format
}
datetime_format = '%Y-%m-%d %H:%M:%S'
filename_format = '%Y-%m-%d_%H-%M-%S'
