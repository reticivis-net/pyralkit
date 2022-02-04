import json

import aiohttp
import dacite
from dateutil.parser import isoparse

from .models import *

def pk_message_from_dict(d: dict) -> PKMessage:
    return dacite.from_dict(
        data_class=PKMessage,
        data=d,
        config=dacite.Config(
            type_hooks={datetime.datetime: isoparse, datetime.date: isoparse},
            cast=[int],
        ),
    )


async def saveurl(url) -> bytes:
    """
    save a url to bytes
    :param url: web url of a file
    :return: bytes of result
    """
    async with aiohttp.ClientSession(headers={"Connection": "keep-alive"}) as session:
        async with session.get(url) as resp:
            if resp.ok:
                return await resp.read()
            else:
                resp.raise_for_status()


async def pk_message_from_message_id(msg_id: int) -> PKMessage:
    return pk_message_from_dict(
        json.loads(await saveurl(f"https://api.pluralkit.me/v2/messages/{msg_id}"))
    )
