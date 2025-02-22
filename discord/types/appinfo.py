"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present Pycord Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from .snowflake import Snowflake
from .team import Team
from .user import User


class BaseAppInfo(TypedDict):
    id: Snowflake
    name: str
    verify_key: str
    icon: str | None
    summary: str
    description: str
    terms_of_service_url: NotRequired[str]
    privacy_policy_url: NotRequired[str]
    hook: NotRequired[bool]
    max_participants: NotRequired[int]


class AppInfo(BaseAppInfo):
    team: NotRequired[Team]
    guild_id: NotRequired[Snowflake]
    primary_sku_id: NotRequired[Snowflake]
    slug: NotRequired[str]
    rpc_origins: list[str]
    owner: User
    bot_public: bool
    bot_require_code_grant: bool


class PartialAppInfo(BaseAppInfo):
    rpc_origins: NotRequired[list[str]]
    cover_image: NotRequired[str]
    flags: NotRequired[int]


class AppInstallParams(TypedDict):
    scopes: list[str]
    permissions: str
