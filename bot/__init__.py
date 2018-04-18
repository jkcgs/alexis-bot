#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Este módulo contiene al bot y lo ejecuta si se corre el script."""

from .events import CommandEvent, MessageEvent, BotMentionEvent
from .libs.configuration import StaticConfig, Configuration, BaseModel
from .libs.language import Language, SingleLanguage
from .command import Command
from .manager import Manager

from .libs.configuration import get_database, init_db
from .command import message_handler
from .events import parse_event
from .logger import log
from . import defaults

from .bot import AlexisBot
