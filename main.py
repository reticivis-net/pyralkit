import asyncio

import pyralkit
from pktoken import pktoken


async def main():
    client = pyralkit.PKClient(pktoken)
    try:
        print(thing := await client.get_current_system_fronters())
        thing
    finally:
        await client.close()


asyncio.get_event_loop().run_until_complete(main())
