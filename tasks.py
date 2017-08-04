import asyncio
import discord
import html
from subreddit import get_posts
from models import Post, Redditor

async def posts_loop(bot):
    post_id = ''
    await bot.wait_until_ready()
    try:
        for subconfig in bot.config['subreddit']:
            subconfig = subconfig.split('@')
            if len(subconfig) < 2:
                continue

            subname = subconfig[0]
            subchannels = subconfig[1].split(',')
            posts = get_posts(subname)

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
                embed = discord.Embed()
                embed.title = data['title']
                embed.set_author(name='/u/' + data['author'], url='https://www.reddit.com/user/' + data['author'])
                embed.url = 'https://reddit.com' + data['permalink']

                if data['is_self']:
                    embed.description = data['selftext']
                elif 'preview' in data and len(data['preview']['images']) > 0:
                    embed.set_image(url=html.unescape(data['preview']['images'][0]['source']['url']))
                else:
                    embed.set_thumbnail(url=html.unescape(data['thumbnail']))

                for channel in subchannels:
                    await bot.send_message(discord.Object(id=channel), content=message, embed=embed)

                post_id = data['id']
                if not exists:
                    Post.create(id=post_id, permalink=data['permalink'], over_18=data['over_18'])
                    bot.log.info('Nuevo post en /r/{subreddit}: {permalink}'.format(subreddit=data['subreddit'],
                                                                                    permalink=data['permalink']))

                    Redditor.update(posts=Redditor.posts + 1).where(Redditor.name == data['author'].lower()).execute()
                    bot.log.info('/u/{author} ha sumado un nuevo post, quedando en {num}.'.format(author=data['author'],
                                                                                                  num=redditor.posts + 1))

    except Exception as e:
        bot.log.exception(e)
    finally:
        await asyncio.sleep(60)

    if not bot.is_closed:
        bot.loop.create_task(posts_loop(bot))
