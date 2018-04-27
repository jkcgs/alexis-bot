import asyncio
from bot.bot import AlexisBot


async def close():
    await ale.close()

if __name__ == '__main__':
    try:
        ale = AlexisBot()
        ale.init()
    except asyncio.CancelledError:
        pass
