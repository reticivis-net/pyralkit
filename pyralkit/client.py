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
            raise PKNotAuthorized()

    return wrap


async def _wait_until(dt):
    # sleep until the specified datetime
    now = datetime.datetime.now()
    await asyncio.sleep((dt - now).total_seconds())


class PKClient:
    def __init__(self, token: typing.Optional[str] = None):
        """
        the base class of PyralKit, handling all requests and ratelimiting.
        :param token: optionally authorize requests with a PluralKit token. required for most methods.
        """
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
        """
        close the underlying aiohttp session
        """
        await self._session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        payload: typing.Optional[typing.Union[dict, list, tuple]] = None,
        query_params: typing.Optional[dict] = None,
        return_code: bool = False,
    ):
        # if self._retry_at:
        #     print(f"new request encountering existing wait.")
        #     await wait_until(self._retry_at)
        async with self._limiter:
            async with self._session.request(
                method,
                f"https://api.pluralkit.me/v2/{endpoint}",
                json=payload,
                params=query_params,
            ) as resp:
                data = await resp.read()
                if resp.ok:
                    if return_code:
                        return data, resp.status
                    else:
                        return data
                else:
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
                            http_errors.get(resp.status, PKErrorResponse),
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

    @authorized_only
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
        https://pluralkit.me/api/endpoints/#update-system-settings

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

    @authorized_only
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
        """
        https://pluralkit.me/api/endpoints/#create-member

        :param name:
        :param proxy_tags:
        :param keep_proxy:
        :param color:
        :param privacy:
        :param display_name:
        :param birthday:
        :param pronouns:
        :param avatar_url:
        :param banner:
        :param description:
        :return: a member object
        """
        payload = {"name": name}
        if proxy_tags is not MISSING:
            payload["proxy_tags"] = [
                dataclasses.asdict(tag, dict_factory=custom_asdict_factory)
                for tag in proxy_tags
            ]
        if keep_proxy is not MISSING:
            payload["keep_proxy"] = keep_proxy
        if color is not MISSING:
            payload["color"] = color
        if privacy is not MISSING:
            payload["privacy"] = dataclasses.asdict(
                privacy, dict_factory=custom_asdict_factory
            )
        if display_name is not MISSING:
            payload["display_name"] = display_name
        if birthday is not MISSING:
            payload["birthday"] = birthday.isoformat()
        if pronouns is not MISSING:
            payload["pronouns"] = pronouns
        if avatar_url is not MISSING:
            payload["avatar_url"] = avatar_url
        if banner is not MISSING:
            payload["banner"] = banner
        if description is not MISSING:
            payload["description"] = description

        return parse_bytes_to_obj(
            await self._request("POST", f"members/", payload),
            PKMember,
        )

    async def get_member(self, member_ref: str) -> PKMember:
        """
        https://pluralkit.me/api/endpoints/#get-member

        :param member_ref: can be a member's short (5-character ID) or a member's UUID
        :return: a member object
        """
        return parse_bytes_to_obj(
            await self._request("GET", f"members/{member_ref}"),
            PKMember,
        )

    @authorized_only
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
        """
        https://pluralkit.me/api/endpoints/#update-member

        :param member_ref: can be a member's short (5-character ID) or a member's UUID
        :param name:
        :param proxy_tags:
        :param keep_proxy:
        :param color:
        :param privacy:
        :param display_name:
        :param birthday:
        :param pronouns:
        :param avatar_url:
        :param banner:
        :param description:
        :return: a member object
        """
        payload = {}
        if name is not MISSING:
            payload["name"] = name
        if proxy_tags is not MISSING:
            payload["proxy_tags"] = [
                dataclasses.asdict(tag, dict_factory=custom_asdict_factory)
                for tag in proxy_tags
            ]
        if keep_proxy is not MISSING:
            payload["keep_proxy"] = keep_proxy
        if color is not MISSING:
            payload["color"] = color
        if privacy is not MISSING:
            payload["privacy"] = dataclasses.asdict(
                privacy, dict_factory=custom_asdict_factory
            )
        if display_name is not MISSING:
            payload["display_name"] = display_name
        if birthday is not MISSING:
            payload["birthday"] = birthday.isoformat()
        if pronouns is not MISSING:
            payload["pronouns"] = pronouns
        if avatar_url is not MISSING:
            payload["avatar_url"] = avatar_url
        if banner is not MISSING:
            payload["banner"] = banner
        if description is not MISSING:
            payload["description"] = description

        return parse_bytes_to_obj(
            await self._request("PATCH", f"members/{member_ref}", payload),
            PKMember,
        )

    @authorized_only
    async def delete_member(self, member_ref: str):
        """
        https://pluralkit.me/api/endpoints/#delete-member

        :param member_ref: can be a member's short (5-character ID) or a member's UUID
        """
        ret = await self._request("DELETE", f"members/{member_ref}", return_code=True)
        # i suspect that on fail itll raise a non 2xx code on success but just to be safe
        if ret[1] == 204:
            return
        else:
            raise PKFailed(f"Request failed with code {ret[1]}: {ret[0]}")

    async def get_member_groups(self, member_ref: str) -> typing.List[PKGroup]:
        """
        https://pluralkit.me/api/endpoints/#get-member-groups

        :param member_ref: can be a member's short (5-character ID) or a member's UUID
        :return: list of groups
        """
        return parse_list_bytes_to_obj(
            await self._request("GET", f"members/{member_ref}/groups"),
            PKGroup,
        )

    @authorized_only
    async def add_member_to_groups(self, member_ref: str, *groups: str):
        """
        https://pluralkit.me/api/endpoints/#add-member-to-groups

        :param member_ref: can be a member's short (5-character ID) or a member's UUID
        :param groups: can be a group's short (5-character ID) or a group's UUID
        """
        ret = await self._request(
            "POST", f"members/{member_ref}/groups/add", groups, return_code=True
        )
        # i suspect that on fail itll raise a non 2xx code on success but just to be safe
        if ret[1] == 204:
            return
        else:
            raise PKFailed(f"Request failed with code {ret[1]}: {ret[0]}")

    @authorized_only
    async def remove_member_from_groups(self, member_ref: str, *groups: str):
        """
        https://pluralkit.me/api/endpoints/#remove-member-from-groups
        If you want to remove all groups from a member, consider using overwrite_member_groups() instead.

        :param member_ref: can be a member's short (5-character ID) or a member's UUID
        :param groups: can be a group's short (5-character ID) or a group's UUID
        """
        ret = await self._request(
            "POST", f"members/{member_ref}/groups/remove", groups, return_code=True
        )
        # i suspect that on fail itll raise a non 2xx code on success but just to be safe
        if ret[1] == 204:
            return
        else:
            raise PKFailed(f"Request failed with code {ret[1]}: {ret[0]}")

    @authorized_only
    async def overwrite_member_groups(self, member_ref: str, groups: typing.List[str]):
        """
        https://pluralkit.me/api/endpoints/#overwrite-member-groups

        :param member_ref: can be a member's short (5-character ID) or a member's UUID
        :param groups: can be a group's short (5-character ID) or a group's UUID
        """
        ret = await self._request(
            "POST", f"members/{member_ref}/groups/overwrite", groups, return_code=True
        )
        # i suspect that on fail itll raise a non 2xx code on success but just to be safe
        if ret[1] == 204:
            return
        else:
            raise PKFailed(f"Request failed with code {ret[1]}: {ret[0]}")

    async def get_member_guild_settings(
        self, member_ref: str, guild_id: int
    ) -> PKMemberGuildSettings:
        """
        https://pluralkit.me/api/endpoints/#get-member-guild-settings
        You must already have updated per-guild settings for the target member in the target guild before being able to
        get or update them from the API.

        :param member_ref: can be a member's short (5-character ID) or a member's UUID
        :param guild_id:
        :return: a member guild settings object
        """
        return parse_bytes_to_obj(
            await self._request("GET", f"members/{member_ref}/guilds/{guild_id}"),
            PKMemberGuildSettings,
        )

    @authorized_only
    async def update_member_guild_settings(
        self,
        member_ref: str,
        guild_id: int,
        *,
        display_name: typing.Optional[str] = MISSING,
        avatar_url: typing.Optional[str] = MISSING,
    ) -> PKMemberGuildSettings:
        """
        https://pluralkit.me/api/endpoints/#update-member-guild-settings

        :param member_ref: can be a member's short (5-character ID) or a member's UUID
        :param guild_id:
        :param display_name:
        :param avatar_url:
        :return: a member guild settings object
        """
        payload = {}
        if display_name is not MISSING:
            payload["display_name"] = display_name
        if avatar_url is not MISSING:
            payload["avatar_url"] = avatar_url
        return parse_bytes_to_obj(
            await self._request(
                "PATCH", f"members/{member_ref}/guilds/{guild_id}", payload
            ),
            PKMemberGuildSettings,
        )

    # GROUPS

    async def get_system_groups(
        self, system_ref: typing.Union[str, int] = "@me", with_members: bool = False
    ) -> typing.List[PKGroup]:
        """
        https://pluralkit.me/api/endpoints/#get-system-groups

        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account
            linked to the system, or the string @me to refer to the currently authenticated system.
        :param with_members: includes members key with array of member UUIDs in each group object
        :return: a list of group objects
        """
        return parse_list_bytes_to_obj(
            await self._request(
                "GET",
                f"systems/{system_ref}/groups",
                query_params={"with_members": str(with_members)},
            ),
            PKGroup,
        )

    @authorized_only
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
        """
        https://pluralkit.me/api/endpoints/#create-group

        :param name:
        :param display_name:
        :param description:
        :param icon:
        :param banner:
        :param color:
        :param privacy:
        :return: a group object
        """
        payload = {"name": name}
        if display_name is not MISSING:
            payload["display_name"] = display_name
        if description is not MISSING:
            payload["description"] = description
        if icon is not MISSING:
            payload["icon"] = icon
        if banner is not MISSING:
            payload["banner"] = banner
        if color is not MISSING:
            payload["color"] = color
        if privacy is not MISSING:
            payload["privacy"] = dataclasses.asdict(
                privacy, dict_factory=custom_asdict_factory
            )

        return parse_bytes_to_obj(
            await self._request("POST", f"/groups", payload),
            PKGroup,
        )

    async def get_group(self, group_ref: str) -> PKGroup:
        """
        https://pluralkit.me/api/endpoints/#get-group

        :param group_ref: can be a group's short (5-character ID) or a group's UUID
        :return: a group object
        """
        return parse_bytes_to_obj(
            await self._request("GET", f"/groups/{group_ref}"),
            PKGroup,
        )

    @authorized_only
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
        """
        https://pluralkit.me/api/endpoints/#update-group

        :param group_ref: can be a group's short (5-character ID) or a group's UUID
        :param name:
        :param display_name:
        :param description:
        :param icon:
        :param banner:
        :param color:
        :param privacy:
        :return: a group object
        """
        payload = {}
        if name is not MISSING:
            payload["name"] = name
        if display_name is not MISSING:
            payload["display_name"] = display_name
        if description is not MISSING:
            payload["description"] = description
        if icon is not MISSING:
            payload["icon"] = icon
        if banner is not MISSING:
            payload["banner"] = banner
        if color is not MISSING:
            payload["color"] = color
        if privacy is not MISSING:
            payload["privacy"] = dataclasses.asdict(
                privacy, dict_factory=custom_asdict_factory
            )

        return parse_bytes_to_obj(
            await self._request("PATCH", f"/groups/{group_ref}", payload),
            PKGroup,
        )

    @authorized_only
    async def delete_group(self, group_ref: str):
        """
        https://pluralkit.me/api/endpoints/#delete-group

        :param group_ref: can be a group's short (5-character ID) or a group's UUID
        :return:
        """
        ret = await self._request("DELETE", f"groups/{group_ref}", return_code=True)
        # i suspect that on fail itll raise a non 2xx code on success but just to be safe
        if ret[1] == 204:
            return
        else:
            raise PKFailed(f"Request failed with code {ret[1]}: {ret[0]}")

    async def get_group_members(self, group_ref: str) -> typing.List[PKMember]:
        """
        https://pluralkit.me/api/endpoints/#get-group-members

        :param group_ref: can be a group's short (5-character ID) or a group's UUID
        :return: list of member objects
        """
        return parse_list_bytes_to_obj(
            await self._request("PATCH", f"/groups/{group_ref}/members"),
            PKMember,
        )

    @authorized_only
    async def add_members_to_groups(self, group_ref: str, *members: str):
        """
        https://pluralkit.me/api/endpoints/#add-members-to-group

        :param group_ref: can be a group's short (5-character ID) or a group's UUID
        :param members: list of member references
        """
        ret = await self._request(
            "POST", f"groups/{group_ref}/members/add", members, return_code=True
        )
        # i suspect that on fail itll raise a non 2xx code on success but just to be safe
        if ret[1] == 204:
            return
        else:
            raise PKFailed(f"Request failed with code {ret[1]}: {ret[0]}")

    @authorized_only
    async def remove_members_from_groups(self, group_ref: str, *members: str):
        """
        https://pluralkit.me/api/endpoints/#remove-member-from-group
        If you want to remove all members from a group, consider using overwrite_group_members() endpoint instead.

        :param group_ref: can be a group's short (5-character ID) or a group's UUID
        :param members: list of member references
        """
        ret = await self._request(
            "POST", f"groups/{group_ref}/members/remove", members, return_code=True
        )
        # i suspect that on fail itll raise a non 2xx code on success but just to be safe
        if ret[1] == 204:
            return
        else:
            raise PKFailed(f"Request failed with code {ret[1]}: {ret[0]}")

    @authorized_only
    async def overwrite_group_members(self, group_ref: str, members: typing.List[str]):
        """
        https://pluralkit.me/api/endpoints/#overwrite-group-members

        :param group_ref: can be a group's short (5-character ID) or a group's UUID
        :param members: list of member references
        """
        ret = await self._request(
            "POST", f"groups/{group_ref}/members/overwrite", members, return_code=True
        )
        # i suspect that on fail itll raise a non 2xx code on success but just to be safe
        if ret[1] == 204:
            return
        else:
            raise PKFailed(f"Request failed with code {ret[1]}: {ret[0]}")

    # SWITCHES

    async def get_system_switches(
        self,
        system_ref: typing.Union[str, int] = "@me",
        before: typing.Optional[datetime.datetime] = None,
        limit: int = 100,
    ) -> typing.List[PKSwitch]:
        """
        https://pluralkit.me/api/endpoints/#get-system-switches
        This endpoint returns at most 100 switches. To get more switches, make multiple requests using the before
        parameter for pagination.

        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account
            linked to the system, or the string @me to refer to the currently authenticated system.
        :param before: date to get latest switch from
        :param limit: number of switches to get (defaults to 100)
        :return: a switch object containing a list of IDs
        """
        assert 1 <= limit <= 100, "Limit must be between 1 and 100"
        query_params = {
            "limit": limit,
        }
        if before is not None:
            query_params["before"] = before.isoformat()
        return parse_list_bytes_to_obj(
            await self._request(
                "GET",
                f"/systems/{system_ref}/switches",
                query_params=query_params,
            ),
            PKSwitch,
        )

    async def get_current_system_fronters(
        self, system_ref: typing.Union[str, int] = "@me"
    ) -> typing.Optional[PKSwitch]:
        """
        https://pluralkit.me/api/endpoints/#get-current-system-fronters

        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account
            linked to the system, or the string @me to refer to the currently authenticated system.
        :return: a switch object containing a list of member objects or None if no switches are found.
        """
        data = await self._request(
            "GET",
            f"/systems/{system_ref}/fronters",
        )
        if data:
            return parse_bytes_to_obj(data, PKSwitch)
        else:
            return None

    @authorized_only
    async def create_switch(
        self,
        members: typing.List[str],
        timestamp: typing.Optional[datetime.datetime] = None,
        system_ref: typing.Union[str, int] = "@me",
    ) -> PKSwitch:
        """
        https://pluralkit.me/api/endpoints/#create-switch

        :param members: members present in the switch (or empty list for switch-out). Can be short IDs or UUIDs.
        :param timestamp: when the switch started. Defaults to "now" when missing.
        :param system_ref:
        :return:
        """
        payload = {"members": members}
        if timestamp is not None:
            payload["timestamp"] = timestamp.isoformat()

        return parse_bytes_to_obj(
            await self._request("POST", f"/systems/{system_ref}/switches", payload),
            PKSwitch,
        )

    async def get_switch(
        self, switch_ref: str, system_ref: typing.Union[str, int] = "@me"
    ) -> PKSwitch:
        """
        https://pluralkit.me/api/endpoints/#get-switch

        :param switch_ref: must be a switch's UUID.
        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account linked
            to the system, or the string @me to refer to the currently authenticated system.
        :return: a switch object containing a list of member objects
        """
        return parse_bytes_to_obj(
            await self._request(
                "GET",
                f"/systems/{system_ref}/switches/{switch_ref}",
            ),
            PKSwitch,
        )

    @authorized_only
    async def update_switch(
        self,
        switch_ref: str,
        timestamp: datetime.datetime,
        system_ref: typing.Union[str, int] = "@me",
    ) -> PKSwitch:
        """
        https://pluralkit.me/api/endpoints/#update-switch

        :param switch_ref: must be a switch's UUID.
        :param timestamp: when the switch started
        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account linked
            to the system, or the string @me to refer to the currently authenticated system.
        :return: a switch object containing a list of member objects
        """
        payload = {"timestamp": timestamp.isoformat()}
        return parse_bytes_to_obj(
            await self._request(
                "PATCH", f"/systems/{system_ref}/switches/{switch_ref}", payload
            ),
            PKSwitch,
        )

    @authorized_only
    async def update_switch_members(
        self,
        switch_ref: str,
        members: typing.List[str],
        system_ref: typing.Union[str, int] = "@me",
    ) -> PKSwitch:
        """
        https://pluralkit.me/api/endpoints/#update-switch-members

        :param switch_ref: must be a switch's UUID.
        :param members:  a list of member short IDs or UUIDs
        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account linked
            to the system, or the string @me to refer to the currently authenticated system.
        :return: a switch object containing a list of member objects
        """
        return parse_bytes_to_obj(
            await self._request(
                "PATCH", f"/systems/{system_ref}/switches/{switch_ref}/members", members
            ),
            PKSwitch,
        )

    @authorized_only
    async def delete_switch(
        self, switch_ref: str, system_ref: typing.Union[str, int] = "@me"
    ):
        """
        https://pluralkit.me/api/endpoints/#delete-switch

        :param switch_ref: must be a switch's UUID.
        :param system_ref: can be a system's short (5-character) ID, a system's UUID, the ID of a Discord account linked
            to the system, or the string @me to refer to the currently authenticated system.
        """
        ret = await self._request(
            "DELETE", f"/systems/{system_ref}/switches/{switch_ref}", return_code=True
        )
        # i suspect that on fail itll raise a non 2xx code on success but just to be safe
        if ret[1] == 204:
            return
        else:
            raise PKFailed(f"Request failed with code {ret[1]}: {ret[0]}")

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
