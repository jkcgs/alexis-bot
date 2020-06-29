# This module contains default definitions for bot settings and whatever

default_log_format = '%(asctime)s | %(levelname)-8s | %(name)s || %(message)s'

config = {
    'token': '',
    'database_url': 'sqlite:///db.sqlite3',
    'command_prefix': '!',
    'debug': False,
    'bot_owners': ['130324995984326656'],
    'owner_role': 'AlexisMaster',
    'ext_modpath': '',
    'default_lang': 'es',
    'log_path': 'logs',
    'log_to_files': False,
    'log_format': default_log_format,
    'whitelist': False,
    'whitelist_autoleave': False,
    'whitelist_contact': '130324995984326656',
    'whitelist_servers': ['198944348379938816'],
    'blacklist_servers': [],
    'shutdown_channel': ''
}
datetime_format = '%Y-%m-%d %H:%M:%S'
filename_format = '%Y-%m-%d_%H-%M-%S'
