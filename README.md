## Alexis Bot

This is a Discord bot that aims to deliver tools for all Discord users, with moderation
and fun commands, including tools for automate tasks on servers. It is also easy to mantain,
thanks to its modular design. Built on top of the [discord.py](https://discordpy.readthedocs.io) library.

### Quick start

#### Self-host
Yes, of course you can self-host this bot. To do this, you can follow the following instructions:

1. You need **Python 3.5 or Python 3.6** with `pip` installed. The `virtualenv` tool is optional but recommended.
2. Clone this repo and change to the project directory (e.g., `cd alexis-bot`).
3. Make a virtualenv with `virtualenv .venv` (if you have it) and activate it.
4. Install dependencies: `pip install -r requirements.txt`
5. Copy the `config.yml.example` to `config.yml`
6. Open the `config.yml` file and add your bot token to the right of the `token: ` line.
7. Add yourself as the bot owner by adding your user ID to the `bot_owners` line (change the current ID)
8. Edit other values to your liking on the configuration file, then save and close it.
9. Run the bot with `python run.py`

#### Server owners, administrators, moderators, and staff in general

You can add the bot with [this link](https://discordapp.com/oauth2/authorize?client_id=397855139005988864&scope=bot).
The bot will provide you with tools to administrate your server, like invite filters, auto-roles, mute commands, etc.
Check out [this guide](https://github.com/jkcgs/alexis-bot/wiki/Administration-and-moderation-tools) for more information.

#### Users

This bot has a lot of """funny""" and useful commands, for example, providing random cats, displaying
the current weather, fetch a term definition on Urban Dictionary, and more. Check out [this page](https://discord.cl/commands) for more
details about all the available commands.

### Development

As mentioned before, this bot tries to be as modular as possible, by making it easy to create and maintain command
modules. For example, if you want to add a `!ping` command, create a file inside the `modules` folder and add this
content:

```python
from bot import Command

class Ping(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ping'
        self.help = 'Answers to the *ping* command'

    async def handle(self, cmd):
       await cmd.answer('Pong!')
```

The following picture shows the complete form of the [`ping.py`](https://github.com/jkcgs/alexis-bot/blob/dev/modules/ping.py)
script:

![](https://i.imgur.com/NX94fva.jpg)

In another example, you can make the bot greet new users, by using event handlers:

```python
from bot import Command

class Welcome(Command):
    def __init__(self, bot):
        super().__init__(bot)

    async def on_member_join(self, member):
        chan = self.bot.get_channel('<channel_id>')
        await self.bot.send_message(chan, 'Welcome to our server, {}!'.format(member.display_name))
```

You can see a more elaborated example in the [`greeting.py`](https://github.com/jkcgs/alexis-bot/blob/dev/modules/owners/greeting.py)
script.

More options and more documentation about the modules API can be found [here](https://github.com/jkcgs/alexis-bot/wiki/Modules-development).

### Special thanks
I want to thank all the people that has collaborated with this project, specially the code contributors:
[jvicu2001](https://github.com/jvicu2001), [AnEpicName](https://github.com/AnEpicName) and 
[HenryDelMal](https://github.com/HenryDelMal). My most special thanks goes to [santisteban](https://github.com/santisteban)
(a.k.a. *ibk*) for creating this project. Sadly, the code has been so heavily modified and none of his code can be found
in the current status.

### License
This project is licensed under the [MIT license](LICENSE).

