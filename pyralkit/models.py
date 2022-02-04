import datetime
import typing
from dataclasses import dataclass
from enum import Enum


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


@dataclass
class PKGroupPrivacy:
    # https://pluralkit.me/api/models/#group-model
    ame_privacy: PKPrivacy = PKPrivacy.public
    description_privacy: PKPrivacy = PKPrivacy.public
    icon_privacy: PKPrivacy = PKPrivacy.public
    list_privacy: PKPrivacy = PKPrivacy.public
    metadata_privacy: PKPrivacy = PKPrivacy.public
    visibility: PKPrivacy = PKPrivacy.public


@dataclass
class PKGroup:
    # https://pluralkit.me/api/models/#group-model
    id: str
    uuid: str
    name: str
    display_name: typing.Optional[str] = None
    description: typing.Optional[str] = None
    icon: typing.Optional[str] = None
    banner: typing.Optional[str] = None
    color: typing.Optional[str] = None
    privacy: typing.Optional[PKGroupPrivacy] = None


@dataclass
class PKSwitch:
    # https://pluralkit.me/api/models/#switch-model
    id: str
    timestamp: datetime.datetime
    members: typing.List[typing.Union[str, PKMember]]


@dataclass
class PKSystemSettings:
    timezone: datetime.timezone
    pings_enabled: bool
    latch_timeout: typing.Optional[int]
    member_default_private: bool
    group_default_private: bool
    show_private_info: bool
    member_limit: int = 1000
    group_limit: int = 250


class PKAutoproxyMode(Enum):
    # https://pluralkit.me/api/models/#autoproxy-mode-enum
    off = "off"
    front = "front"
    latch = "latch"
    member = "member"


@dataclass
class PKSystemGuildSettings:
    # https://pluralkit.me/api/models/#system-guild-settings-model
    guild_id: int
    proxying_enabled: bool
    tag_enabled: bool
    autoproxy_mode: PKAutoproxyMode
    autoproxy_member: typing.Optional[str] = None
    tag: typing.Optional[str] = None


@dataclass
class PKMemberGuildSettings:
    guild_id: int
    display_name: typing.Optional[str] = None
    avatar_url: typing.Optional[str] = None
