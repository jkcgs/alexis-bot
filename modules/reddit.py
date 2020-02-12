import html

import discord
import peewee
from discord import Embed

from bot import Command, BaseModel, categories
from bot.utils import text_cut, auto_int
from bot.regex import pat_channel, pat_subreddit


class Post(BaseModel):
    id = peewee.CharField()
    permalink = peewee.CharField(null=True)
    over_18 = peewee.BooleanField(default=False)


class ChannelFollow(BaseModel):
    subreddit = peewee.TextField()
    serverid = peewee.TextField()
    channelid = peewee.TextField()


class RedditFollow(Command):
    __author__ = 'makzk'
    __version__ = '1.1.5'
    db_models = [Post, ChannelFollow]

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reddit'
        self.aliases = ['redditor']
        self.help = '$[reddit-help]'
        self.format = '$[reddit-format]'
        self.chans = {}
        self.allow_pm = False
        self.owner_only = True
        self.category = categories.STAFF
        self.schedule = (self.load_task, 15)

    def on_loaded(self):
        self.load_channels()

    async def handle(self, cmd):
        if cmd.argc < 1:
            await cmd.answer('$[format]: $[reddit-format]')
            return

        if cmd.args[0] in ['set', 'follow', 'remove', 'unfollow']:
            if cmd.argc < 2:
                await cmd.answer('$[format]: $[reddit-format-set]')
                return
            else:
                if not pat_subreddit.match(cmd.args[1]):
                    await cmd.answer('$[reddit-error-sub-name]')
                    return

                if cmd.argc > 2:
                    chan_match = pat_channel.match(cmd.args[2])
                    if not chan_match:
                        await cmd.answer('$[format]: $[reddit-format-set]')
                        return

                    chan_id = auto_int(chan_match.group(1))
                    channel = cmd.message.guild.get_channel(chan_id)
                    if channel is None:
                        await cmd.answer('$[reddit-error-channel-not-found]')
                        return
                else:
                    channel = cmd.message.channel

            if cmd.args[0] in ['set', 'follow']:
                chan, created = ChannelFollow.get_or_create(
                    subreddit=cmd.args[1], serverid=cmd.message.guild.id, channelid=channel.id)

                if created:
                    msg = '$[reddit-sub-added-here]' if channel.id == cmd.channel.id else '$[reddit-sub-added]'
                    await cmd.answer(msg, locales={'sub': cmd.args[1]})
                    if chan.subreddit not in self.chans:
                        self.chans[chan.subreddit] = []

                    self.chans[chan.subreddit].append((chan.serverid, chan.channelid))
                    return
                else:
                    await cmd.answer('$[reddit-error-sub-already-added]')
                    return
            else:
                try:
                    asd = ChannelFollow.get(ChannelFollow.subreddit == cmd.args[1],
                                            ChannelFollow.serverid == cmd.message.guild.id,
                                            ChannelFollow.channelid == channel.id)
                    asd.delete_instance()

                    if cmd.args[1] in self.chans:
                        for tup in self.chans[cmd.args[1]]:
                            if tup == (cmd.message.guild.id, channel.id):
                                self.chans[cmd.args[1]].remove(tup)
                                break
                        if len(self.chans[cmd.args[1]]) == 0:
                            del self.chans[cmd.args[1]]

                    await cmd.answer('$[reddit-sub-removed]')
                    return
                except ChannelFollow.DoesNotExist:
                    await cmd.answer('$[reddit-error-not-followed]')
                    return
        elif cmd.args[0] == 'list':
            res = ChannelFollow.select().where(ChannelFollow.serverid == cmd.message.guild.id)
            resp = []
            for chan in res:
                resp.append('- **{}** ➡ <#{}>'.format(chan.subreddit, chan.channelid))

            if len(res) == 0:
                await cmd.answer('$[reddit-no-following-subs]')
            else:
                await cmd.answer('$[reddit-feeds-title]:\n{}'.format('\n'.join(resp)))
        else:
            await cmd.answer('$[format]: $[reddit-format]')

    async def load_task(self):
        post_id = ''
        for (subname, subchannels) in self.chans.items():
            posts = await self.get_posts(subname)

            if len(posts) == 0:
                continue

            data = posts[0]

            try:
                exists = Post.get(Post.id == data['id'])
            except Post.DoesNotExist:
                exists = False

            while data['id'] != post_id and not exists:
                subname = data.get('subreddit') or data.get('display_name')
                embed = self.post_to_embed(data)
                if embed is None:
                    break

                for channel in subchannels:
                    chan = self.bot.get_channel(auto_int(channel))
                    if chan is not None:
                        try:
                            await self.bot.send_message(chan, content='$[reddit-message-title]', embed=embed,
                                                        locales={'sub': subname})
                        except discord.Forbidden:
                            self.log.debug('Could not sent a r/%s post to %s (%s) #%s (%s) due to missing permissions',
                                           subname, chan.guild.name, chan.guild.id, chan.name, chan.id)
                    else:
                        self.log.warning('Channel ID %s not found for subreddit subscription r/%s, removing',
                                         channel, subname)
                        to_del = ChannelFollow.get_or_none(
                            ChannelFollow.subreddit == subname, ChannelFollow.channelid == channel)
                        if to_del is not None:
                            to_del.delete_instance()
                            self.chans[subname].remove(channel)

                post_id = data['id']
                if not exists:
                    with self.bot.db.atomic():
                        Post.create(id=post_id, permalink=data['permalink'], over_18=data['over_18'])

    def load_channels(self):
        for chan in ChannelFollow.select():
            if chan.subreddit not in self.chans:
                self.chans[chan.subreddit] = []

            self.chans[chan.subreddit].append(chan.channelid)

    async def get_posts(self, sub, since=0):
        url = 'https://www.reddit.com/r/{}/new.json'.format(sub)
        async with self.http.get(url) as r:
            if not r.status == 200:
                return []

            posts = []
            data = await r.json()
            for post in data['data']['children']:
                if since < post['data']['created']:
                    posts.append(post['data'])

            return posts

    def post_to_embed(self, post):
        author = '($[])'
        author_url = 'https://www.reddit.com/'
        if 'author' in post:
            author = '/u/' + post['author']
            author_url += 'user/' + post['author']

        if 'permalink' not in post:
            return None

        embed = Embed()
        embed.title = text_cut(post['title'], 256)
        embed.url = 'https://www.reddit.com' + post['permalink']
        embed.set_author(name=author, url=author_url)

        if post['is_self']:
            embed.description = text_cut(post['selftext'], 2048)
        elif post['media']:
            if 'preview' in post:
                embed.set_image(url=html.unescape(post['preview']['images'][0]['source']['url']))
            elif post['thumbnail'] != 'default' and post['thumbnail'].startswith('http'):
                embed.set_thumbnail(url=html.unescape(post['thumbnail']))
            embed.description = "$[reddit-media-link]: " + post['url']
        elif 'preview' in post:
            embed.set_image(url=html.unescape(post['preview']['images'][0]['source']['url']))
        elif post['thumbnail'] != '' and post['thumbnail'] != 'default' and post['thumbnail'].startswith('http'):
            embed.set_thumbnail(url=html.unescape(post['thumbnail']))

        return embed
