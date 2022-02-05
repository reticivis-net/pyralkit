import asyncio
import dataclasses
import functools
from dataclasses import MISSING

import aiohttp
from aiolimiter import AsyncLimiter

from .errors import *
from .utils import *


def authorized_only(func):
    @functools.wraps(func)
    async def wrap(self, *args, **kwargs):
        if self._authenticated:
            return await func(self, *args, **kwargs)
        else:
            raise NotAuthorized()

    return wrap


async def wait_until(dt):
    # sleep until the specified datetime
    now = datetime.datetime.now()
    await asyncio.sleep((dt - now).total_seconds())


class PKClient:
    def __init__(self, token: typing.Optional[str] = None):
        headers = {"Connection": "keep-alive", "Content-Type": "application/json"}
        self._authenticated = token is not None
        if self._authenticated:
            headers["Authorization"] = token
        self._session = aiohttp.ClientSession(
            headers=headers,
        )
        # https://pluralkit.me/api/#rate-limiting
        self._limiter = AsyncLimiter(2, 1)
        # limit concurrency to handle 429s
        # self._retry_at: typing.Optional[datetime.datetime] = None

    async def close(self):
        await self._session.close()

    async def _request(
        self, method: str, endpoint: str, payload: typing.Optional[dict] = None
    ):
        # if self._retry_at:
        #     print(f"new request encountering existing wait.")
        #     await wait_until(self._retry_at)
        async with self._limiter:
            async with self._session.request(
                method, f"https://api.pluralkit.me/v2/{endpoint}", json=payload
            ) as resp:
                if resp.ok:
                    return await resp.read()
                else:
                    data = await resp.read()
                    if data:
                        if resp.status == 429:
                            # dev says despite the 429 docs existing there is no actual rate limiting besides default
                            # nginx limiting which has no retry-after handler
                            resp.raise_for_status()
                        # if resp.status == 429:
                        #     self._retry_at = (
                        #         datetime.datetime.utcnow()
                        #         + datetime.timedelta(
                        #             milliseconds=data["retry_after"]
                        #         )
                        #     )
                        #     print(
                        #         f"got 429, retrying in {data['retry_after']/1000}s"
                        #     )
                        #     await wait_until(self._retry_at)
                        #     continue  # all is wrapped in while loop, will try again
                        raise parse_bytes_to_obj(
                            data,
                            http_errors.get(resp.status, ErrorResponse),
                            {"http_code": resp.status},
                        )
                    resp.raise_for_status()

    # SYSTEM

    async def get_system(self, system_ref: typing.Union[str, int] = "@me") -> PKSystem:
        """
        https://pluralkit.me/api/endpoints/#get-system

        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account
            linked to the system, or the string @me to refer to the currently authenticated system.
        :return: A system object
        """
        return parse_bytes_to_obj(
            await self._request("GET", f"systems/{system_ref}"), PKSystem
        )

    @authorized_only
    async def update_system(
        self,
        system_ref: typing.Union[str, int] = "@me",
        *,
        name: typing.Optional[str] = MISSING,
        tag: typing.Optional[str] = MISSING,
        color: typing.Optional[str] = MISSING,
        description: typing.Optional[str] = MISSING,
        avatar_url: typing.Optional[str] = MISSING,
        banner: typing.Optional[str] = MISSING,
        privacy: typing.Optional[PKSystemPrivacy] = MISSING,
    ) -> PKSystem:
        """
        https://pluralkit.me/api/endpoints/#update-system
        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account
            linked to the system, or the string @me to refer to the currently authenticated system.
        :param name: system's name
        :param tag: system's tag
        :param color: 6-character hex code, no # at the beginning
        :param description: system's description. 1000-character limit
        :param avatar_url: 256-character limit, must be a publicly-accessible URL
        :param banner: 256-character limit, must be a publicly-accessible URL
        :param privacy: system's privacy setting
        """
        payload = {}
        if name is not MISSING:
            payload["name"] = name
        if tag is not MISSING:
            payload["tag"] = tag
        if color is not MISSING:
            payload["color"] = color
        if description is not MISSING:
            payload["description"] = description
        if avatar_url is not MISSING:
            payload["avatar_url"] = avatar_url
        if banner is not MISSING:
            payload["banner"] = banner
        if privacy is not MISSING:
            payload["privacy"] = dataclasses.asdict(
                privacy, dict_factory=custom_asdict_factory
            )

        return parse_bytes_to_obj(
            await self._request("PATCH", f"systems/{system_ref}", payload), PKSystem
        )

    async def get_system_settings(
        self, system_ref: typing.Union[str, int] = "@me"
    ) -> PKSystemSettings:
        """
        https://pluralkit.me/api/endpoints/#get-system-settings

        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account
            linked to the system, or the string @me to refer to the currently authenticated system.
        :return: A system settings object
        """
        return parse_bytes_to_obj(
            await self._request("GET", f"systems/{system_ref}/settings"),
            PKSystemSettings,
        )

    async def update_system_settings(
        self,
        system_ref: typing.Union[str, int] = "@me",
        *,
        timezone: str = MISSING,
        pings_enabled: bool = MISSING,
        latch_timeout: typing.Optional[int] = MISSING,
        member_default_private: bool = MISSING,
        group_default_private: bool = MISSING,
        show_private_info: bool = MISSING,
    ) -> PKSystemSettings:
        """

        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account
            linked to the system, or the string @me to refer to the currently authenticated system.
        :param timezone: system's IANA timezone
        :param pings_enabled: if reaction pings are enabled
        :param latch_timeout: The latch timeout duration for your system.
        :param member_default_private: whether members created through the bot have privacy settings set to private by
            default
        :param group_default_private: whether groups created through the bot have privacy settings set to private by
            default
        :param show_private_info: whether the bot shows the system's own private information without a -private flag
        :return: a system settings object
        """
        payload = {}
        if timezone is not MISSING:
            payload["timezone"] = timezone
        if pings_enabled is not MISSING:
            payload["pings_enabled"] = pings_enabled
        if latch_timeout is not MISSING:
            payload["latch_timeout"] = latch_timeout
        if member_default_private is not MISSING:
            payload["member_default_private"] = member_default_private
        if group_default_private is not MISSING:
            payload["group_default_private"] = group_default_private
        if show_private_info is not MISSING:
            payload["show_private_info"] = show_private_info
        return parse_bytes_to_obj(
            await self._request("PATCH", f"systems/{system_ref}/settings", payload),
            PKSystemSettings,
        )

    @authorized_only
    async def get_system_guild_settings(
        self, guild_id: int, system_ref: typing.Union[str, int] = "@me"
    ) -> typing.Optional[PKSystemGuildSettings]:
        """
        https://pluralkit.me/api/endpoints/#get-system-guild-settings

        You must already have updated per-guild settings for your system in the target guild before being able to get
        or update them from the API.
        :param guild_id: ID of guild
        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account
            linked to the system, or the string @me to refer to the currently authenticated system.
        :return: a system guild settings object or None if not found
        """
        try:
            return parse_bytes_to_obj(
                await self._request("GET", f"systems/{system_ref}/guilds/{guild_id}"),
                PKSystemGuildSettings,
                {"guild_id": guild_id},
            )
        except PKNotFound:
            return None

    @authorized_only
    async def update_system_guild_settings(
        self,
        guild_id: int,
        system_ref: typing.Union[str, int] = "@me",
        *,
        proxying_enabled: bool = MISSING,
        tag_enabled: bool = MISSING,
        autoproxy_mode: PKAutoproxyMode = MISSING,
        autoproxy_member: typing.Optional[str] = MISSING,
        tag: typing.Optional[str] = MISSING,
    ) -> typing.Optional[PKSystemGuildSettings]:
        """
        https://pluralkit.me/api/endpoints/#update-system-guild-settings

        You must already have updated per-guild settings for your system in the target guild before being able to get
        or update them from the API.
        :param guild_id: ID of guild
        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account
            linked to the system, or the string @me to refer to the currently authenticated system.
        :param proxying_enabled:
        :param tag_enabled:
        :param autoproxy_mode:
        :param autoproxy_member:
        :param tag:
        :return: a system guild settings object or None if not found
        """
        payload = {}
        if proxying_enabled is not MISSING:
            payload["proxying_enabled"] = proxying_enabled
        if tag_enabled is not MISSING:
            payload["tag_enabled"] = tag_enabled
        if autoproxy_mode is not MISSING:
            payload["autoproxy_mode"] = autoproxy_mode
        if autoproxy_member is not MISSING:
            payload["autoproxy_member"] = autoproxy_member
        if tag is not MISSING:
            payload["tag"] = tag

        return parse_bytes_to_obj(
            await self._request(
                "PATCH", f"systems/{system_ref}/guilds/{guild_id}", payload
            ),
            PKSystemGuildSettings,
            {"guild_id": guild_id},
        )

    # MEMBERS

    async def get_system_members(
        self, system_ref: typing.Union[str, int] = "@me"
    ) -> typing.List[PKMember]:
        """
        https://pluralkit.me/api/endpoints/#get-system-members

        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account
            linked to the system, or the string @me to refer to the currently authenticated system.
        :return: A list of member objects
        """
        return parse_list_bytes_to_obj(
            await self._request("GET", f"systems/{system_ref}/members"), PKMember
        )

    async def create_member(
        self,
        name: str,
        *,
        proxy_tags: typing.List[PKProxyTag] = MISSING,
        keep_proxy: bool = MISSING,
        color: typing.Optional[str] = MISSING,
        privacy: typing.Optional[PKMemberPrivacy] = MISSING,
        display_name: typing.Optional[str] = MISSING,
        birthday: typing.Optional[datetime.date] = MISSING,
        pronouns: typing.Optional[str] = MISSING,
        avatar_url: typing.Optional[str] = MISSING,
        banner: typing.Optional[str] = MISSING,
        description: typing.Optional[str] = MISSING,
    ) -> PKMember:
        raise NotImplementedError

    async def get_member(self, member_ref: str) -> PKMember:
        raise NotImplementedError

    async def update_member(
        self,
        member_ref: str,
        *,
        name: str = MISSING,
        proxy_tags: typing.List[PKProxyTag] = MISSING,
        keep_proxy: bool = MISSING,
        color: typing.Optional[str] = MISSING,
        privacy: typing.Optional[PKMemberPrivacy] = MISSING,
        display_name: typing.Optional[str] = MISSING,
        birthday: typing.Optional[datetime.date] = MISSING,
        pronouns: typing.Optional[str] = MISSING,
        avatar_url: typing.Optional[str] = MISSING,
        banner: typing.Optional[str] = MISSING,
        description: typing.Optional[str] = MISSING,
    ):
        raise NotImplementedError

    async def delete_member(self, member_ref: str):
        raise NotImplementedError

    async def get_member_groups(self, member_ref: str) -> typing.List[PKGroup]:
        raise NotImplementedError

    async def add_member_to_groups(self, member_ref: str, *groups: str):
        raise NotImplementedError

    async def remove_member_from_groups(self, member_ref: str, *groups: str):
        raise NotImplementedError

    async def overwrite_member_groups(self, member_ref: str, groups: typing.List[str]):
        raise NotImplementedError

    async def get_member_guild_settings(
        self, member_ref: str, guild_id: int
    ) -> PKMemberGuildSettings:
        raise NotImplementedError

    async def update_member_guild_settings(
        self,
        member_ref: str,
        guild_id: int,
        *,
        display_name: typing.Optional[str] = MISSING,
        avatar_url: typing.Optional[str] = MISSING,
    ) -> PKMemberGuildSettings:
        raise NotImplementedError

    # GROUPS

    async def get_system_groups(
        self, system_ref: typing.Union[str, int] = "@me", with_members: bool = False
    ) -> typing.List[PKGroup]:
        raise NotImplementedError

    async def create_group(
        self,
        name: str,
        *,
        display_name: typing.Optional[str] = MISSING,
        description: typing.Optional[str] = MISSING,
        icon: typing.Optional[str] = MISSING,
        banner: typing.Optional[str] = MISSING,
        color: typing.Optional[str] = MISSING,
        privacy: typing.Optional[PKGroupPrivacy] = MISSING,
    ) -> PKGroup:
        raise NotImplementedError

    async def get_group(self, group_ref: str) -> PKGroup:
        raise NotImplementedError

    async def update_group(
        self,
        group_ref: str,
        *,
        name: str = MISSING,
        display_name: typing.Optional[str] = MISSING,
        description: typing.Optional[str] = MISSING,
        icon: typing.Optional[str] = MISSING,
        banner: typing.Optional[str] = MISSING,
        color: typing.Optional[str] = MISSING,
        privacy: typing.Optional[PKGroupPrivacy] = MISSING,
    ) -> PKGroup:
        raise NotImplementedError

    async def delete_group(self, group_ref: str):
        raise NotImplementedError

    async def get_group_members(self, group_ref: str) -> typing.List[PKMember]:
        raise NotImplementedError

    async def add_members_to_groups(self, group_ref: str, *members: str):
        raise NotImplementedError

    async def remove_members_from_groups(self, group_ref: str, *members: str):
        raise NotImplementedError

    async def overwrite_group_members(self, group_ref: str, members: typing.List[str]):
        raise NotImplementedError

    # SWITCHES

    async def get_system_switches(
        self,
        system_ref: typing.Union[str, int] = "@me",
        before: typing.Optional[datetime.datetime] = None,
        limit: typing.Optional[int] = None,
    ) -> PKSwitch:
        raise NotImplementedError

    async def get_current_system_fronters(
        self, system_ref: typing.Union[str, int] = "@me"
    ) -> typing.List[PKMember]:
        raise NotImplementedError

    async def create_switch(
        self,
        members: typing.List[str],
        system_ref: typing.Union[str, int] = "@me",
        timestamp: typing.Optional[datetime.datetime] = None,
    ) -> PKSwitch:
        raise NotImplementedError

    async def get_switch(
        self, switch_ref: str, system_ref: typing.Union[str, int] = "@me"
    ) -> PKSwitch:
        raise NotImplementedError

    async def update_switch(
        self,
        switch_ref: str,
        timestamp: datetime.datetime,
        system_ref: typing.Union[str, int] = "@me",
    ) -> PKSwitch:
        raise NotImplementedError

    async def update_switch_members(
        self,
        switch_ref: str,
        members: typing.List[str],
        system_ref: typing.Union[str, int] = "@me",
    ) -> PKSwitch:
        raise NotImplementedError

    async def delete_switch(
        self, switch_ref: str, system_ref: typing.Union[str, int] = "@me"
    ):
        raise NotImplementedError

    # MISC

    async def get_proxied_message_information(
        self, messageid: int
    ) -> typing.Optional[PKMessage]:
        """
        https://pluralkit.me/api/endpoints/#misc
        :param messageid: the ID of a proxied message, or the ID of the message that sent the proxy.
        :return: message object or None if not found.
        """
        try:
            return parse_bytes_to_obj(
                await self._request("GET", f"messages/{messageid}"), PKMessage
            )
        except PKNotFound:
            return None
