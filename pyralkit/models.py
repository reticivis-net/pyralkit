import datetime
import typing
from dataclasses import dataclass
from enum import Enum


class PKModel:
    """base class for all models"""

    pass


@dataclass
class PKProxyTag(PKModel):
    """
    https://pluralkit.me/api/models/#proxytag-object
    Note: prefix + "text" + suffix must be shorter than 100 characters in total.

    :param prefix: text before your message to trigger the proxy
    :param suffix: text after your message to trigger the proxy
    """

    prefix: typing.Optional[str] = None
    suffix: typing.Optional[str] = None


class PKPrivacy(PKModel, Enum):
    """https://pluralkit.me/api/models/#models"""

    public = "public"
    private = "private"


@dataclass
class PKSystemPrivacy(PKModel):
    """
    https://pluralkit.me/api/models/#system-model

    :param description_privacy: System description
    :param member_list_privacy: Member list
    :param group_list_privacy: Group list
    :param front_privacy: Current fronter
    :param front_history_privacy: Front history
    """

    description_privacy: PKPrivacy
    member_list_privacy: PKPrivacy
    group_list_privacy: PKPrivacy
    front_privacy: PKPrivacy
    front_history_privacy: PKPrivacy

    @classmethod
    def all_public(cls):
        """Initialize class with all privacy values set to public"""
        return cls(*([PKPrivacy.public] * 5))

    @classmethod
    def all_private(cls):
        """Initialize class with all privacy values set to private"""
        return cls(*([PKPrivacy.private] * 5))


@dataclass
class PKSystem(PKModel):
    """
    https://pluralkit.me/api/models/#system-model

    :param id: a short (5-character) ID. The short ID is unique across the resource (a member can have the same short
        ID as a system, for example)
    :param uuid: a longer UUID. the UUID is consistent for the lifetime of the entity and globally unique across the
        bot.
    :param created: datetime of creation
    :param name: system name
    :param tag: a little snippet of text that'll be added to the end of all proxied messages
    :param color: system color
    :param description: system description
    :param avatar_url: System avatar url
    :param banner: System banner url
    :param privacy: System privacy settings
    """
    id: str
    uuid: str
    created: datetime.datetime
    name: typing.Optional[str] = None
    tag: typing.Optional[str] = None
    color: typing.Optional[str] = None
    description: typing.Optional[str] = None
    avatar_url: typing.Optional[str] = None
    banner: typing.Optional[str] = None
    privacy: typing.Optional[PKSystemPrivacy] = None


@dataclass
class PKMemberPrivacy(PKModel):
    # https://pluralkit.me/api/models/#member-model
    visibility: PKPrivacy
    name_privacy: PKPrivacy
    description_privacy: PKPrivacy
    birthday_privacy: PKPrivacy
    pronoun_privacy: PKPrivacy
    avatar_privacy: PKPrivacy
    metadata_privacy: PKPrivacy

    @classmethod
    def all_public(cls):
        """Initialize class with all privacy values set to public"""
        return cls(*([PKPrivacy.public] * 7))

    @classmethod
    def all_private(cls):
        """Initialize class with all privacy values set to private"""
        return cls(*([PKPrivacy.private] * 7))


@dataclass
class PKMember(PKModel):
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
class PKMessage(PKModel):
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
class PKGroupPrivacy(PKModel):
    # https://pluralkit.me/api/models/#group-model
    name_privacy: PKPrivacy
    description_privacy: PKPrivacy
    icon_privacy: PKPrivacy
    list_privacy: PKPrivacy
    metadata_privacy: PKPrivacy
    visibility: PKPrivacy

    @classmethod
    def all_public(cls):
        """Initialize class with all privacy values set to public"""
        return cls(*([PKPrivacy.public] * 6))

    @classmethod
    def all_private(cls):
        """Initialize class with all privacy values set to private"""
        return cls(*([PKPrivacy.private] * 6))


@dataclass
class PKGroup(PKModel):
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
    # https://pluralkit.me/api/endpoints/#get-system-groups
    members: typing.Optional[typing.List[str]] = None


@dataclass
class PKSwitch(PKModel):
    # https://pluralkit.me/api/models/#switch-model
    id: str
    timestamp: datetime.datetime
    members: typing.List[typing.Union[str, PKMember]]


@dataclass
class PKSystemSettings(PKModel):
    # https://pluralkit.me/api/models/#system-settings-model
    timezone: str
    pings_enabled: bool
    latch_timeout: typing.Optional[int]
    member_default_private: bool
    group_default_private: bool
    show_private_info: bool
    member_limit: int = 1000
    group_limit: int = 250


class PKAutoproxyMode(PKModel, Enum):
    # https://pluralkit.me/api/models/#autoproxy-mode-enum
    off = "off"
    front = "front"
    latch = "latch"
    member = "member"


@dataclass
class PKSystemGuildSettings(PKModel):
    # https://pluralkit.me/api/models/#system-guild-settings-model
    guild_id: int
    proxying_enabled: bool
    tag_enabled: bool
    autoproxy_mode: PKAutoproxyMode
    autoproxy_member: typing.Optional[str] = None
    tag: typing.Optional[str] = None


@dataclass
class PKMemberGuildSettings(PKModel):
    # https://pluralkit.me/api/models/#member-guild-settings-model
    guild_id: int
    display_name: typing.Optional[str] = None
    avatar_url: typing.Optional[str] = None
