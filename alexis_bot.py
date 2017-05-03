#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import discord
import yaml

import logger

__author__ = 'Nicolás Santisteban, Jonathan Gutiérrez'
__license__ = 'MIT'
__version__ = '0.1.0'


class Alexis(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)
        self.log = logger.get_logger('Alexis')

        try:
            with open('config.yml', 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.log.exception(e)
            raise

    def go(self):
        pass
