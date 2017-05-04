#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import platform
import sqlite3
import requests
import sys
import yaml
import discord

import logger
from models import *

__author__ = 'Nicolás Santisteban, Jonathan Gutiérrez'
__license__ = 'MIT'
__version__ = '0.1.0'


class Alexis(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)

        self.log = logger.get_logger('Alexis')

        db.connect()
        db.create_tables([Post, Ban], True)

        try:
            with open('config.yml', 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.log.exception(e)
            raise

    def go(self):
        self.log.info('"Alexis Bot" version {}.'.format(__version__))
        self.log.info('Python {} on {}.'.format(sys.version, sys.platform))
        self.log.info(platform.uname())
        self.log.info('SQLite3 support for version {}.'.format(sqlite3.sqlite_version))
        self.log.info('------')
        self.log.info('Connecting...')

        try:
            self.loop.create_task(self.get_reddit_new())
            self.run(self.config['token'])
        except Exception as e:
            self.log.exception(e)
            raise

    async def on_ready(self):
        self.log.info('Logged in as:')
        self.log.info(self.user.name)
        self.log.info(self.user.id)
        self.log.info('------')
        await self.change_presence(game=discord.Game(name=self.config['playing']))

    async def on_message(self, message):
        # !ping
        if message.content == '!ping':
            await self.send_message(message.channel, 'pong!')

        # !ban (no PM)
        elif message.content.startswith('!ban') and message.server is not None:
            for mention in message.mentions:
                user, created = Ban.get_or_create(user=mention, server=message.server)
                up = Ban.update(bans=Ban.bans + 1).where(Ban.user == mention, Ban.server == message.server)
                up.execute()

                ban_txt = 'vez' if user.bans + 1 == 1 else 'veces'
                text = 'El usuario **{}** ha sido baneado {} {}.'.format(mention.name, user.bans + 1, ban_txt)
                await self.send_message(message.channel, text)

    async def get_reddit_new(self):
        post_id = ''
        await self.wait_until_ready()
        while not self.is_closed:
            try:
                for subreddit in self.config['subreddit']:
                    url = 'https://www.reddit.com/r/{}/new/.json'.format(subreddit)
                    agent = 'Alexis/{}'.format(__version__)
                    r = requests.get(url, headers={'User-agent': agent})

                    if not r.status_code == 200:
                        continue

                    data = r.json()['data']['children'][0]['data']

                    try:
                        exists = Post.get(Post.id == data['id'])
                    except Post.DoesNotExist:
                        exists = False

                    while data['id'] != post_id and not exists:
                        post_id = data['id']
                        channels = self.config['channel_nsfw'] if data['over_18'] else self.config['channel_id']

                        for channel in channels:
                            d = 'Nuevo post en **/r/{subreddit}** por **/u/{autor}**: https://www.reddit.com{permalink}'
                            text = d.format(subreddit=data['subreddit'],
                                            autor=data['author'],
                                            permalink=data['permalink'])
                            await self.send_message(discord.Object(id=channel), text)

                        if not exists:
                            Post.create(id=post_id, permalink=data['permalink'], over_18=data['over_18'])
                            self.log.info('Nuevo post en /r/{}: {}'.format(data['subreddit'], data['permalink']))

            except Exception as e:
                self.log.warning(e)
            await asyncio.sleep(60)

if __name__ == '__main__':
    bot = Alexis()
    bot.go()
