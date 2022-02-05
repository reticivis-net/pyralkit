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
                        data = json.loads(data)
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
                        data["http_code"] = resp.status
                        raise parse_dict_to_obj(
                            data, http_errors.get(resp.status, ErrorResponse)
                        )
                    resp.raise_for_status()

    async def get_system(self, system_ref: typing.Union[str, int]) -> PKSystem:
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
            system_ref: typing.Union[str, int],
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
            self, system_ref: typing.Union[str, int]
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
    async def get_system_guild_settings(self, guildid: int) -> PKSystemGuildSettings:
        return parse_bytes_to_obj(
            await self._request("GET", f"systems/@me/guilds/{guildid}"),
            PKSystemGuildSettings,
        )
