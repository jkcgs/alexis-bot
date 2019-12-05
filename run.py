import asyncio

from bot import AlexisBot


if __name__ == '__main__':
    ale = None

    try:
        ale = AlexisBot()
        ale.init()
    except asyncio.CancelledError:
        pass
    except Exception:
        ale.manager.close_http()
        raise
