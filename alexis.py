#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import discord
import asyncio
import requests
import yaml
import sys
import platform
import sqlite3

import logger
from models import *

__author__ = 'Nicolás Santisteban, Jonathan Gutiérrez'
__license__ = 'MIT'
__version__ = '0.1.0'

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
                    if not r.status_code == 200:
                        continue

                    data = r.json()['data']['children'][0]['data']

                    try:
                        exists = Post.select().where(Post.id == data['id']).get()
                    except:
                        exists = False

                    while data['id'] != post_id and not exists:
                        post_id = data['id']
                        channels = config['channel_nsfw'] if data['over_18'] else config['channel_id']

                        for channel in channels:
                            d = 'Nuevo post en **/r/{subreddit}** por **/u/{autor}**: https://www.reddit.com{permalink}'
                            text = d.format(subreddit=data['subreddit'],
                                            autor=data['author'],
                                            permalink=data['permalink'])
                            await client.send_message(discord.Object(id=channel), text)

                        if not exists:
                            Post.create(id=post_id, permalink=data['permalink'], over_18=data['over_18'])
                            log.info('Nuevo post en /r/{}: {}'.format(data['subreddit'], data['permalink']))
            except Exception as e:
                log.warning(e)
            await asyncio.sleep(60)


    @client.event
    async def on_message(message):
        if message.content == '!ping':
            await client.send_message(message.channel, 'pong!')
        elif message.content.startswith('!ban'):
            if message.is_private:
                return

            mentions = message.mentions
            for mention in mentions:
                user, created = Ban.get_or_create(user=mention, server=message.server)
                up = Ban.update(bans=Ban.bans + 1).where(Ban.user == mention, Ban.server == message.server)
                up.execute()

                text = 'El usuario **{}** ha sido baneado {} veces.'.format(mention.name, user.bans + 1)
                await client.send_message(message.channel, text)


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
