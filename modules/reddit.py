import html

import discord
import peewee
from discord import Embed

from bot import Command, BaseModel, categories
from bot.utils import text_cut, auto_int
from bot.regex import pat_channel, pat_subreddit


class RedditLastPost(BaseModel):
    post_id = peewee.CharField()
    subreddit = peewee.CharField()
    timestamp = peewee.IntegerField(default=0)


class ChannelFollow(BaseModel):
    subreddit = peewee.TextField()
    serverid = peewee.TextField()
    channelid = peewee.TextField()


class RedditFollow(Command):
    __author__ = 'makzk'
    __version__ = '1.2.2'
    db_models = [RedditLastPost, ChannelFollow]

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

        if cmd.args[0] == 'reload' and cmd.bot_owner:
            self.load_channels()
            await cmd.answer('$[reddit-reloaded]')
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

                    self.chans[chan.subreddit].append(chan.channelid)
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
        for (subname, subchannels) in self.chans.items():
            post = await self.get_last_post(subname)
            if not post:
                self.log.warning('Error fetching post from r/%s', subname)
                continue

            ins, updated = RedditLastPost.get_or_create(subreddit=subname, defaults={
                'post_id': post['id'], 'timestamp': post['created']})

            if not updated and ins.post_id != post['id'] and ins.timestamp < post['created']:
                ins.post_id = post['id']
                ins.timestamp = post['created']
                ins.save()
                updated = True

            if updated:
                embed = self.post_to_embed(post)

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

    async def get_last_post(self, sub):
        url = 'https://www.reddit.com/r/{}/new.json?limit=1'.format(sub)
        async with self.http.get(url) as r:
            if not r.status == 200:
                return None

            data = await r.json()
            posts = data['data']['children']
            return posts[0]['data'] if len(posts) > 0 else None

    def load_channels(self):
        self.chans = {}

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

    @staticmethod
    def post_to_embed(post):
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
