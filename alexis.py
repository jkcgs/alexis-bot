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

__author__ = 'Nicolás Santisteban'
__license__ = 'MIT'
__version__ = '0.0.3'

client = discord.Client()
db = peewee.SqliteDatabase('database.db')

logger = logging.getLogger('Vector')
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


try:
	db.connect()
except Exception as e:
	logger.exception(e)
	raise

try:
	db.create_tables([Post])
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
			for ll in range(0,1):
				try:
					r = requests.get('https://www.reddit.com/r/{}/new/.json'.format(config['subreddit'][ll]), headers = {'User-agent': 'Alexis2'})
					if r.status_code == 200:
						try:
							exists = Post.select().where(Post.id == r.json()['data']['children'][0]['data']['id']).get()
						except:
							exists = False

						while r.json()['data']['children'][0]['data']['id'] != post_id and not exists:
							j = r.json()['data']['children'][0]['data']
							post_id = j['id']
							await client.send_message(discord.Object(id=config['channel_id'][ll]), 'https://www.reddit.com{}'.format(j['permalink']))
							if not exists:
								Post.create(id=post_id, permalink=j['permalink'], over_18=j['over_18'])
								logger.info('Nuevo post: {}'.format(j['permalink']))
				except Exception as e:
					logger.warning(e)
				await asyncio.sleep(60)


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

	# aqui inician los comandos para el cliente 
	@client.event
	async def on_message(message):
		if message.content.startswith('!link'):
			msg = await client.send_message(message.channel, 'Este discord https://discord.gg/jwUcm')
		
	logger.info('"Vector Bot" version {}.'.format(__version__))
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
