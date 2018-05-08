import asyncio
import discord

from bot.bot import AlexisBot


if __name__ == '__main__':
    ale = None

    try:
        ale = AlexisBot()
        ale.init()
    except discord.errors.LoginFailure:
        if ale is not None:
            ale.close()
    except asyncio.CancelledError:
        pass
