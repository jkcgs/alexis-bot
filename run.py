import asyncio
from alexis import Alexis


async def close():
    await ale.close()

if __name__ == '__main__':
    ale = None
    loop = asyncio.get_event_loop()

    try:
        ale = Alexis()
        ale.init()
    finally:
        loop.run_until_complete(close())
        loop.close()
