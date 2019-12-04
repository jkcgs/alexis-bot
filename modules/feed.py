import re
from base64 import b64encode
from discord import Embed

from bot import Command
import feedparser

pat_twitter = re.compile(r'^((https?://)?(www\.)?twitter\.com/|@)[a-zA-Z0-9_]{1,50}$')
pat_reddit_user = re.compile(r'^(https?://(www\.)?reddit.com/u(ser)?/|/?u/)[a-zA-Z0-9_\-]{1,50}$')
pat_reddit_sub = re.compile(r'^(https?://(www\.)?reddit.com)?/?r/[a-zA-Z0-9_\-]{1,50}$')
pat_tumblr = re.compile(r'^(?:https?://)?([a-zA-Z0-9\-]{1,50})\.tumblr\.com/?$')
pat_url = re.compile(r'^https?://[-a-zA-Z0-9@%._+~=]{2,256}\.[a-z]{2,10}\b([-a-zA-Z0-9@:%_+.~#?&/=]*)$')


#
# WIP
#

class Feed(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.default_enabled = False

        self.name = 'feed'
        self.owner_only = True
        self.default_config = {
            'twitter_key': '',
            'twitter_secret': ''
        }

        self.twitter_token = None

    async def handle(self, cmd):
        if cmd.argc == 0:
            await cmd.answer('xd')
            return

        await cmd.typing()
        url, url_type = self.normalize_url(cmd.text)
        self.log.debug('URL: %s', url)

        if url_type == 'twitter':
            if self.twitter_token is None:
                await cmd.answer('Twitter feeds are unavailable.')
                return

            async with self.get_twitter(url) as r:
                data = await r.json()

                # Not a list: probably an error
                if not isinstance(data, list):
                    err = 'unknown error'
                    if 'errors' in data:
                        err = 'Error {}: {}'.format(data['errors'][0]['code'], data['errors'][0]['message'])

                    self.log.debug(data)
                    await cmd.answer(err)
                    return

                if len(data) == 0:
                    await cmd.answer('no tweets found')
                    return

                tweet_url = 'https://twitter.com/{}/status/{}'.format(
                    data[0]['user']['screen_name'], data[0]['id_str'])
                await cmd.answer(tweet_url)
        elif url_type == 'tumblr' or url_type == 'generic':
            async with self.http.get(url) as r:
                p = feedparser.parse(await r.text())
                embed = Embed(title='Feed information')
                embed.description = '**Title**: {}\n**Description**: {}'.format(
                    p['feed']['title'], p['feed']['subtitle']
                )
                await cmd.answer(embed)
        else:
            await cmd.answer('Invalid URL')

    def twitter_url(self, user_url):
        # todo: retrieve account id and store that instead
        if user_url.startswith('@'):
            user = user_url[1:].split(' ')[0].strip()
        elif user_url.startswith('https://twitter.com/'):
            user = user_url[20:]
        elif user_url.startswith('http://twitter.com/'):
            user = user_url[19:]
        elif user_url.startswith('twitter.com/'):
            user = user_url[12:]
        else:
            return None

        u = 'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name={}&count=3&exclude_replies=false'
        return u.format(user)

    def normalize_url(self, url):
        if pat_twitter.match(url):
            return self.twitter_url(url), 'twitter'
        elif pat_reddit_user.match(url):
            url = 'https://reddit.com/user/{}.json'.format(url.split('/')[-1])
            return url, 'reddit'
        elif pat_reddit_sub.match(url):
            url = 'https://reddit.com/r/{}.json'.format(url.split('/')[-1])
            return url, 'reddit'
        elif pat_tumblr.match(url):
            url = 'https://{}.tumblr.com/rss'.format(pat_tumblr.findall(url)[0])
            return url, 'tumblr'
        elif pat_url.match(url):
            return url, 'generic'
        else:
            return None, None

    def get_twitter(self, url):
        return self.http.get(url, headers={'Authorization': 'Bearer ' + self.twitter_token})

    async def on_ready(self):
        if self.bot.config['twitter_key'] == '' or self.bot.config['twitter_secret'] == '':
            self.log.warn('Twitter keys not set up. Twitter feeds will be disabled.')
            return

        auth_key = self.bot.config['twitter_key'] + ':' + self.bot.config['twitter_secret']
        auth_key = 'Basic ' + b64encode(auth_key.encode('ascii')).decode('ascii')
        auth_headers = {'Authorization': auth_key}
        auth_endpoint = 'https://api.twitter.com/oauth2/token?grant_type=client_credentials'

        self.log.info('Retrieving Twitter token...')
        async with self.http.post(auth_endpoint, headers=auth_headers) as r:
            data = await r.json()
            if 'access_token' not in data:
                self.log.debug('unexpected result')
                self.log.debug(data)
                return

            self.twitter_token = data['access_token']
            self.log.info('Twitter token retrieved')
