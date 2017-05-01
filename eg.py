import json, requests

response = requests.get('https://api.github.com/repos/frankity/alexis-bot/commits')
data = json.loads(response.text)

print(data[0]['html_url'])