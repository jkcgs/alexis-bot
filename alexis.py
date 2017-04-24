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

__author__ = 'Nicolás Santisteban'
__version__ = '0.0.1'

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
			try:
				r = requests.get('https://www.reddit.com/r/chile/new/.json', headers = {'User-agent': 'Alexis'})
				if r.status_code == 200:
					try:
						exists = Post.select().where(Post.id == r.json()['data']['children'][0]['data']['id']).get()
					except:
						exists = False

					while r.json()['data']['children'][0]['data']['id'] != post_id and not exists:
						j = r.json()['data']['children'][0]['data']
						post_id = j['id']
						await client.send_message(discord.Object(id=config['channel_id']), 'https://www.reddit.com{}'.format(j['permalink']))
						if not exists:
							Post.create(id=post_id, permalink=j['permalink'], over_18=j['over_18'])
							logger.info('Nuevo post: {}'.format(j['permalink']))
			except Exception as e:
				logger.warning(e)
			await asyncio.sleep(60)


	@client.event
	async def on_ready():
		logger.info('Logged in as')
		logger.info(client.user.name)
		logger.info(client.user.id)
		logger.info('------')
		await client.change_presence(game=discord.Game(name='/r/chile'))


	client.loop.create_task(get_reddit_new())
	client.run(config['token'])
