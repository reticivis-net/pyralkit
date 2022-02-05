import asyncio

import pyralkit
from pktoken import pktoken


async def main():
    client = pyralkit.PKClient(pktoken)
    try:
        await client.update_system("nehqw", name="fdf")
    finally:
        await client.close()


# Python 3.7+
asyncio.run(main())
