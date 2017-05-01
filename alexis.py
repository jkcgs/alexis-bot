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
import json

__author__ = 'Nicolás Santisteban'
__license__ = 'MIT'
__version__ = '0.0.3'

GOOGLE_URL_SHORTEN_API = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

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

class Commit(peewee.Model):
	id = peewee.CharField()
	sha = peewee.CharField()
	url = peewee.CharField()

	class Meta:
		database = db

try:
	db.connect()
except Exception as e:
	logger.exception(e)
	raise

try:
	db.create_tables([Post, Commit])
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
		commit_id = ''
		await client.wait_until_ready()
		while not client.is_closed:

			commit_id = ''
			response = requests.get('https://api.github.com/repos/'+config['git_user']+'/'+config['git_repo']+'/commits')
			data = json.loads(response.text)

			try:
				c_exists = Commit.select().where(Commit.sha == data[0]['sha']).get()
			except:
				c_exists = False

			if c_exists:
				pass
			if not c_exists:
				await client.send_message(discord.Object(id=config['channel_id'][2]), 'Nuevo commit, '+data[0]['html_url'])
				Commit.create(id=commit_id, sha=data[0]['sha'], url=data[0]['html_url'])

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
							await client.send_message(discord.Object(id=config['channel_id'][ll]), google_url_shorten('https://www.reddit.com{}'.format(j['permalink'])) + ' Post: #' + post_id + ' ' + j['title'] )
							if not exists:
								Post.create(id=post_id, permalink=j['permalink'], over_18=j['over_18'])
								logger.info('Nuevo post: {}'.format(j['permalink']))
				except Exception as e:
					logger.warning(e)
				await asyncio.sleep(60)

	def google_url_shorten(url):
		req_url = 'https://www.googleapis.com/urlshortener/v1/url?key=' + GOOGLE_URL_SHORTEN_API
		payload = {'longUrl': url}
		headers = {'content-type': 'application/json'}
		r = requests.post(req_url, data=json.dumps(payload), headers=headers)
		resp = json.loads(r.text)
		return resp['id']

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
