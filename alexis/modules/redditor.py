import asyncio
import html
import re

import discord
import peewee
from discord import Embed

from alexis.base.command import Command
from alexis.base.database import BaseModel


class RedditorCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'redditor'
        self.help = 'Muestra la cantidad de posts (registrados por el bot) hechos por un redditor'
        self.run_task = True
        self.db_models = [Redditor, Post]

        if 'subreddit' not in self.bot.config:
            self.bot.config['subreddit'] = []

    async def handle(self, message, cmd):
        user = cmd.args[0]

        if user.startswith('/u/'):
            user = user[3:]
        if not re.match('^[a-zA-Z0-9_-]*$', user):
            return

        redditor, _ = Redditor.get_or_create(name=user.lower())

        if redditor.posts > 0:
            suffix = 'post' if redditor.posts == 1 else 'posts'
            text = '**/u/{name}** ha creado **{num}** {suffix}.'
            text = text.format(name=user, num=redditor.posts, suffix=suffix)
            await cmd.answer(text)
        else:
            text = '**/u/{name}** no ha creado ningún post.'
            text = text.format(name=user)
            await cmd.answer(text)

    async def task(self):
        post_id = ''
        await self.bot.wait_until_ready()
        try:
            for subconfig in self.bot.config['subreddit']:
                subconfig = subconfig.split('@')
                if len(subconfig) < 2:
                    if 'default_channel' in self.bot.config and self.bot.config['default_channel'] != '':
                        subconfig.append(self.bot.config['default_channel'])
                    else:
                        continue

                subname = subconfig[0]
                subchannels = subconfig[1].split(',')
                posts = await get_posts(self.bot, subname)

                if len(posts) == 0:
                    continue

                data = posts[0]

                try:
                    exists = Post.get(Post.id == data['id'])
                except Post.DoesNotExist:
                    exists = False

                redditor, _ = Redditor.get_or_create(name=data['author'].lower())

                while data['id'] != post_id and not exists:
                    message = 'Nuevo post en **/r/{}**'.format(data['subreddit'])
                    embed = Embed()
                    embed.title = data['title']
                    embed.set_author(name='/u/' + data['author'], url='https://www.reddit.com/user/' + data['author'])
                    embed.url = 'https://www.reddit.com' + data['permalink']

                    if data['is_self']:
                        if len(data['selftext']) > 2048:
                            embed.description = data['selftext'][:2044] + '...'
                        else:
                            embed.description = data['selftext']
                    elif data['media']:
                        if 'preview' in data:
                            embed.set_image(url=html.unescape(data['preview']['images'][0]['source']['url']))
                        else:
                            embed.set_thumbnail(url=html.unescape(data['thumbnail']))
                        embed.description = "Link del multimedia: " + data['url']
                    elif 'preview' in data:
                        embed.set_image(url=html.unescape(data['preview']['images'][0]['source']['url']))
                    elif data['thumbnail'] != '':
                        embed.set_thumbnail(url=html.unescape(data['thumbnail']))

                    for channel in subchannels:
                        await self.bot.send_message(discord.Object(id=channel), content=message, embed=embed)

                    post_id = data['id']
                    if not exists:
                        Post.create(id=post_id, permalink=data['permalink'], over_18=data['over_18'])
                        self.bot.log.info('Nuevo post en /r/{subreddit}: {permalink}'.format(
                            subreddit=data['subreddit'], permalink=data['permalink']))

                        Redditor.update(posts=Redditor.posts + 1).where(
                            Redditor.name == data['author'].lower()).execute()
                        self.bot.log.info(
                            '/u/{author} ha sumado un nuevo post, quedando en {num}.'.format(author=data['author'],
                                                                                             num=redditor.posts + 1))

        except Exception as e:
            if isinstance(e, RuntimeError):
                pass
            self.bot.log.exception(e)
        finally:
            await asyncio.sleep(60)

        if not self.bot.is_closed:
            self.bot.loop.create_task(self.task())


async def get_posts(bot, sub, since=0):
    url = 'https://www.reddit.com/r/{}/new/.json'.format(sub)
    async with bot.http_session.get(url, headers={'User-agent': 'Alexis'}) as r:
        if not r.status == 200:
            return []

        posts = []
        data = await r.json()
        for post in data['data']['children']:
            if since < post['data']['created']:
                posts.append(post['data'])

        return posts


class Post(BaseModel):
    id = peewee.CharField()
    permalink = peewee.CharField(null=True)
    over_18 = peewee.BooleanField(default=False)


class Redditor(BaseModel):
    name = peewee.TextField()
    posts = peewee.IntegerField(default=0)
