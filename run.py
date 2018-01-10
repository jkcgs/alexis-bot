import asyncio
from alexis import Alexis


async def close():
    await ale.close()

if __name__ == '__main__':
    try:
        ale = Alexis()
        ale.init()
    except asyncio.CancelledError:
        pass
