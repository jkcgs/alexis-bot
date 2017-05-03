#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import discord
import asyncio
import requests
import os
import logging
import datetime
import peewee
import yaml
import sys
import platform
import sqlite3
import re

__author__ = 'Nicolás Santisteban'
__license__ = 'MIT'
__version__ = '0.0.3'

client = discord.Client()
db = peewee.SqliteDatabase('database.db')

logger = logging.getLogger('Alexis')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', '%d-%m-%Y %H:%M:%S')
stdout_logger = logging.StreamHandler()
stdout_logger.setLevel(logging.DEBUG)
stdout_logger.setFormatter(formatter)
logger.addHandler(stdout_logger)


try:
	if not os.path.isdir('logs/'):
		os.makedirs('logs/')
	file_logger = logging.FileHandler('logs/{}.log'.format(datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S')), encoding='utf-8')
	file_logger.setLevel(logging.DEBUG)
	file_logger.setFormatter(formatter)
	logger.addHandler(file_logger)
except Exception as e:
	logger.exception(e)
	raise


class Post(peewee.Model):
	id = peewee.CharField()
	permalink = peewee.CharField()
	over_18 = peewee.BooleanField()

	class Meta:
		database = db

class Ban(peewee.Model):
	user = peewee.TextField()
	bans = peewee.IntegerField(default=0)
	server = peewee.TextField(null=True)

	class Meta:
		database = db


try:
	db.connect()
except Exception as e:
	logger.exception(e)
	raise

try:
	db.create_tables([Post, Ban])
except:
	pass


try:
	with open('config.yml', 'r') as f:
		config = yaml.safe_load(f)
except Exception as e:
	logger.exception(e)
	raise


if __name__ == '__main__':
	async def get_reddit_new():
		post_id = ''
		await client.wait_until_ready()
		while not client.is_closed:
			try:
				for subreddit in config['subreddit']:
					r = requests.get('https://www.reddit.com/r/{}/new/.json'.format(subreddit), headers = {'User-agent': 'Alexis'})
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
								await client.send_message(discord.Object(id=channel), 'Nuevo post en **/r/{subreddit}** por **/u/{autor}**: https://www.reddit.com{permalink}'.format(subreddit=j['subreddit'], autor=j['author'], permalink=j['permalink']))

							if not exists:
								Post.create(id=post_id, permalink=j['permalink'], over_18=j['over_18'])
								logger.info('Nuevo post en /r/{}: {}'.format(j['subreddit'], j['permalink']))
			except Exception as e:
				logger.warning(e)
			await asyncio.sleep(60)


	@client.event
	async def on_message(message):
		if message.content == '!ping':
			await client.send_message(message.channel, 'pong!')
		elif message.content.startswith('!ban'):
			mentions = message.mentions
			for mention in mentions:
				user, created = Ban.get_or_create(user=mention, server=message.server)
				up = Ban.update(bans=Ban.bans + 1).where(Ban.user == mention, Ban.server == message.server)
				up.execute()
				await client.send_message(message.channel, 'El usuario **{}** ha sido baneado {} veces en este server.'.format(mention.name, user.bans + 1))


	@client.event
	async def on_ready():
		try:
			logger.info('Logged in as:')
			logger.info(client.user.name)
			logger.info(client.user.id)
			logger.info('------')
			await client.change_presence(game=discord.Game(name=config['playing']))
		except Exception as e:
			logger.exception(e)
			raise


	logger.info('"Alexis Bot" version {}.'.format(__version__))
	logger.info('Python {} on {}.'.format(sys.version, sys.platform))
	logger.info(platform.uname())
	logger.info('SQLite3 support for version {}.'.format(sqlite3.sqlite_version))
	logger.info('------')


	try:
		client.loop.create_task(get_reddit_new())
		client.run(config['token'])
	except Exception as e:
		logger.exception(e)
		raise
