#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import discord
import asyncio
import requests
import yaml
import sys
import platform
import sqlite3
import re

import logger
from models import *

__author__ = 'Nicolás Santisteban, Jonathan Gutiérrez'
__license__ = 'MIT'
__version__ = '0.0.3'

client = discord.Client()
log = logger.get_logger('Alexis')

try:
    db.connect()
except Exception as e:
    log.exception(e)
    raise

try:
    db.create_tables([Post, Ban], True)
except:
    pass

try:
    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)
except Exception as e:
    log.exception(e)
    raise

if __name__ == '__main__':
    async def get_reddit_new():
        post_id = ''
        await client.wait_until_ready()
        while not client.is_closed:
            try:
                for subreddit in config['subreddit']:
                    r = requests.get('https://www.reddit.com/r/{}/new/.json'.format(subreddit),
                                     headers={'User-agent': 'Alexis'})
                    if r.status_code == 200:
                        try:
                            exists = Post.select().where(Post.id == r.json()['data']['children'][0]['data']['id']).get()
                        except:
                            exists = False

                        while r.json()['data']['children'][0]['data']['id'] != post_id and not exists:
                            j = r.json()['data']['children'][0]['data']
                            post_id = j['id']

                            if j['over_18']:
                                channels = config['channel_nsfw']
                            else:
                                channels = config['channel_id']

                            for channel in channels:
                                await client.send_message(discord.Object(id=channel),
                                                          'Nuevo post en **/r/{subreddit}** por **{autor}**: https://www.reddit.com{permalink}'.format(
                                                              subreddit=j['subreddit'], autor=j['author'],
                                                              permalink=j['permalink']))

                            if not exists:
                                Post.create(id=post_id, permalink=j['permalink'], over_18=j['over_18'])
                                log.info('Nuevo post en /r/{}: {}'.format(j['subreddit'], j['permalink']))
            except Exception as e:
                log.warning(e)
            await asyncio.sleep(60)


    @client.event
    async def on_message(message):
        if message.content == '!ping':
            await client.send_message(message.channel, 'pong!')
        elif message.content.startswith('!ban'):
            if re.match('^[<>@0-9]+$', message.content[5:37]):
                user, created = Ban.get_or_create(user=message.content[5:37])
                up = Ban.update(bans=Ban.bans + 1).where(Ban.user == message.content[5:37])
                up.execute()
                await client.send_message(message.channel,
                                          'El usuario **{}** ha sido baneado {} veces.'.format(message.content[5:37],
                                                                                               user.bans + 1))


    @client.event
    async def on_ready():
        try:
            log.info('Logged in as:')
            log.info(client.user.name)
            log.info(client.user.id)
            log.info('------')
            await client.change_presence(game=discord.Game(name=config['playing']))
        except Exception as e:
            log.exception(e)
            raise


    log.info('"Alexis Bot" version {}.'.format(__version__))
    log.info('Python {} on {}.'.format(sys.version, sys.platform))
    log.info(platform.uname())
    log.info('SQLite3 support for version {}.'.format(sqlite3.sqlite_version))
    log.info('------')

    try:
        client.loop.create_task(get_reddit_new())
        client.run(config['token'])
    except Exception as e:
        log.exception(e)
        raise
