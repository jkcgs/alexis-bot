import requests


def get_posts(sub, since=0):
    url = 'https://www.reddit.com/r/{}/new/.json'.format(sub)
    r = requests.get(url, headers={'User-agent': 'Alexis'})

    if not r.status_code == 200:
        return []

    posts = []
    for post in r.json()['data']['children']:
        if since < post['data']['created']:
            posts.append(post['data'])

    return posts
