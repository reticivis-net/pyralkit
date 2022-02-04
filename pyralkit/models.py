import datetime
import json
import typing
from dataclasses import dataclass
from enum import Enum

import aiohttp
import dacite
from dateutil.parser import isoparse


@dataclass
class PKProxyTag:
    # https://pluralkit.me/api/models/#proxytag-object
    prefix: typing.Optional[str] = None
    suffix: typing.Optional[str] = None


class PKPrivacy(Enum):
    # https://pluralkit.me/api/models/#models
    public = "public"
    private = "private"


@dataclass
class PKSystemPrivacy:
    # https://pluralkit.me/api/models/#system-model
    description_privacy: PKPrivacy = PKPrivacy.public
    member_list_privacy: PKPrivacy = PKPrivacy.public
    group_list_privacy: PKPrivacy = PKPrivacy.public
    front_privacy: PKPrivacy = PKPrivacy.public
    front_history_privacy: PKPrivacy = PKPrivacy.public


@dataclass
class PKSystem:
    # https://pluralkit.me/api/models/#system-model
    id: str
    uuid: str
    name: str
    tag: str
    created: datetime.datetime
    color: typing.Optional[str] = None
    description: typing.Optional[str] = None
    avatar_url: typing.Optional[str] = None
    banner: typing.Optional[str] = None
    privacy: typing.Optional[PKSystemPrivacy] = None


@dataclass
class PKMemberPrivacy:
    # https://pluralkit.me/api/models/#member-model
    visibility: PKPrivacy = PKPrivacy.public
    name_privacy: PKPrivacy = PKPrivacy.public
    description_privacy: PKPrivacy = PKPrivacy.public
    birthday_privacy: PKPrivacy = PKPrivacy.public
    pronoun_privacy: PKPrivacy = PKPrivacy.public
    avatar_privacy: PKPrivacy = PKPrivacy.public
    metadata_privacy: PKPrivacy = PKPrivacy.public


@dataclass
class PKMember:
    # https://pluralkit.me/api/models/#member-model
    id: str
    uuid: str
    name: str
    created: datetime.datetime
    proxy_tags: typing.List[PKProxyTag]
    keep_proxy: bool
    color: typing.Optional[str] = None
    privacy: typing.Optional[PKMemberPrivacy] = None
    display_name: typing.Optional[str] = None
    birthday: typing.Optional[datetime.date] = None
    pronouns: typing.Optional[str] = None
    avatar_url: typing.Optional[str] = None
    banner: typing.Optional[str] = None
    description: typing.Optional[str] = None


@dataclass
class PKMessage:
    # https://pluralkit.me/api/models/#message-model
    timestamp: datetime.datetime
    id: int
    original: int
    sender: int
    channel: int
    guild: int
    system: typing.Optional[PKSystem] = None
    member: typing.Optional[PKMember] = None


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
