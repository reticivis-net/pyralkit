import asyncio

import pyralkit
from pktoken import pktoken


async def main():
    client = pyralkit.PKClient(pktoken)
    system = await client.get_system_settings("@me")
    print(system)


# Python 3.7+
asyncio.run(main())
