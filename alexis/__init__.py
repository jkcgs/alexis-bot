from .logger import log
from .bot import AlexisBot
from .command import Command
from .language import Language
from .message_cmd import MessageCmd
from .configuration import StaticConfig, ServerConfigMgr

config = StaticConfig('config.yml')
