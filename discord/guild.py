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

import copy
import unicodedata
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Union,
    overload,
)

from . import abc, utils
from .asset import Asset
from .automod import AutoModAction, AutoModRule, AutoModTriggerMetadata
from .channel import *
from .channel import _guild_channel_factory, _threaded_guild_channel_factory
from .colour import Colour
from .emoji import GuildEmoji, PartialEmoji, _EmojiTag
from .enums import (
    AuditLogAction,
    AutoModEventType,
    AutoModTriggerType,
    ChannelType,
    ContentFilter,
    EntitlementOwnerType,
    NotificationLevel,
    NSFWLevel,
    ScheduledEventLocationType,
    ScheduledEventPrivacyLevel,
    VerificationLevel,
    VideoQualityMode,
    VoiceRegion,
    try_enum,
)
from .errors import ClientException, InvalidArgument, InvalidData
from .file import File
from .flags import SystemChannelFlags
from .integrations import Integration, _integration_factory
from .invite import Invite
from .iterators import (
    AuditLogIterator,
    BanIterator,
    EntitlementIterator,
    MemberIterator,
)
from .member import Member, VoiceState
from .mixins import Hashable
from .monetization import Entitlement
from .onboarding import Onboarding
from .permissions import PermissionOverwrite
from .role import Role, RoleColours
from .scheduled_events import ScheduledEvent, ScheduledEventLocation
from .stage_instance import StageInstance
from .sticker import GuildSticker
from .threads import Thread, ThreadMember
from .user import User
from .welcome_screen import WelcomeScreen, WelcomeScreenChannel
from .widget import Widget

__all__ = ("BanEntry", "Guild")

MISSING = utils.MISSING

if TYPE_CHECKING:
    import datetime

    from .abc import Snowflake, SnowflakeTime
    from .channel import (
        CategoryChannel,
        ForumChannel,
        StageChannel,
        TextChannel,
        VoiceChannel,
    )
    from .permissions import Permissions
    from .state import ConnectionState
    from .template import Template
    from .types.guild import Ban as BanPayload
    from .types.guild import Guild as GuildPayload
    from .types.guild import GuildFeature, MFALevel
    from .types.member import Member as MemberPayload
    from .types.threads import Thread as ThreadPayload
    from .types.voice import GuildVoiceState
    from .voice_client import VoiceClient
    from .webhook import Webhook

    VocalGuildChannel = Union[VoiceChannel, StageChannel]
    GuildChannel = Union[
        VoiceChannel, StageChannel, TextChannel, ForumChannel, CategoryChannel
    ]
    ByCategoryItem = Tuple[Optional[CategoryChannel], List[GuildChannel]]


class BanEntry(NamedTuple):
    reason: str | None
    user: User


class _GuildLimit(NamedTuple):
    emoji: int
    stickers: int
    bitrate: float
    filesize: int


class Guild(Hashable):
    """Represents a Discord guild.

    This is referred to as a "server" in the official Discord UI.

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.

    Attributes
    ----------
    name: :class:`str`
        The guild name.
    emojis: Tuple[:class:`GuildEmoji`, ...]
        All emojis that the guild owns.
    stickers: Tuple[:class:`GuildSticker`, ...]
        All stickers that the guild owns.

        .. versionadded:: 2.0
    afk_timeout: :class:`int`
        The timeout to get sent to the AFK channel.
    afk_channel: Optional[:class:`VoiceChannel`]
        The channel that denotes the AFK channel. ``None`` if it doesn't exist.
    id: :class:`int`
        The guild's ID.
    invites_disabled: :class:`bool`
        Indicates if the guild invites are disabled.
    owner_id: :class:`int`
        The guild owner's ID. Use :attr:`Guild.owner` instead.
    unavailable: :class:`bool`
        Indicates if the guild is unavailable. If this is ``True`` then the
        reliability of other attributes outside of :attr:`Guild.id` is slim and they might
        all be ``None``. It is best to not do anything with the guild if it is unavailable.

        Check the :func:`on_guild_unavailable` and :func:`on_guild_available` events.
    max_presences: Optional[:class:`int`]
        The maximum amount of presences for the guild.
    max_members: Optional[:class:`int`]
        The maximum amount of members for the guild.

        .. note::

            This attribute is only available via :meth:`.Client.fetch_guild`.
    max_video_channel_users: Optional[:class:`int`]
        The maximum amount of users in a video channel.

        .. versionadded:: 1.4
    description: Optional[:class:`str`]
        The guild's description.
    mfa_level: :class:`int`
        Indicates the guild's two-factor authorisation level. If this value is 0 then
        the guild does not require 2FA for their administrative members. If the value is
        1 then they do.
    verification_level: :class:`VerificationLevel`
        The guild's verification level.
    explicit_content_filter: :class:`ContentFilter`
        The guild's explicit content filter.
    default_notifications: :class:`NotificationLevel`
        The guild's notification settings.
    features: List[:class:`str`]
        A list of features that the guild has. The features that a guild can have are
        subject to arbitrary change by Discord. You can find a catalog of guild features
        `here <https://github.com/Delitefully/DiscordLists?tab=readme-ov-file#guild-feature-glossary>`_.
    premium_tier: :class:`int`
        The premium tier for this guild. Corresponds to "Nitro Server" in the official UI.
        The number goes from 0 to 3 inclusive.
    premium_subscription_count: :class:`int`
        The number of "boosts" this guild currently has.
    premium_progress_bar_enabled: :class:`bool`
        Indicates if the guild has premium progress bar enabled.

        .. versionadded:: 2.0
    preferred_locale: Optional[:class:`str`]
        The preferred locale for the guild. Used when filtering Server Discovery
        results to a specific language.
    nsfw_level: :class:`NSFWLevel`
        The guild's NSFW level.

        .. versionadded:: 2.0

    approximate_member_count: Optional[:class:`int`]
        The approximate number of members in the guild. This is ``None`` unless the guild is obtained
        using :meth:`Client.fetch_guild` with ``with_counts=True``.

        .. versionadded:: 2.0

    approximate_presence_count: Optional[:class:`int`]
        The approximate number of members currently active in the guild.
        This includes idle, dnd, online, and invisible members. Offline members are excluded.
        This is ``None`` unless the guild is obtained using :meth:`Client.fetch_guild`
        with ``with_counts=True``.

        .. versionadded:: 2.0
    """

    __slots__ = (
        "afk_timeout",
        "afk_channel",
        "name",
        "id",
        "unavailable",
        "owner_id",
        "mfa_level",
        "emojis",
        "stickers",
        "features",
        "verification_level",
        "explicit_content_filter",
        "default_notifications",
        "description",
        "max_presences",
        "max_members",
        "max_video_channel_users",
        "premium_tier",
        "premium_subscription_count",
        "premium_progress_bar_enabled",
        "preferred_locale",
        "nsfw_level",
        "_scheduled_events",
        "_members",
        "_channels",
        "_icon",
        "_banner",
        "_state",
        "_roles",
        "_member_count",
        "_large",
        "_splash",
        "_voice_states",
        "_system_channel_id",
        "_system_channel_flags",
        "_discovery_splash",
        "_rules_channel_id",
        "_public_updates_channel_id",
        "_stage_instances",
        "_threads",
        "approximate_member_count",
        "approximate_presence_count",
    )

    _PREMIUM_GUILD_LIMITS: ClassVar[dict[int | None, _GuildLimit]] = {
        None: _GuildLimit(emoji=50, stickers=5, bitrate=96e3, filesize=10_485_760),
        0: _GuildLimit(emoji=50, stickers=5, bitrate=96e3, filesize=10_485_760),
        1: _GuildLimit(emoji=100, stickers=15, bitrate=128e3, filesize=10_485_760),
        2: _GuildLimit(emoji=150, stickers=30, bitrate=256e3, filesize=52_428_800),
        3: _GuildLimit(emoji=250, stickers=60, bitrate=384e3, filesize=104_857_600),
    }

    def __init__(self, *, data: GuildPayload, state: ConnectionState):
        # NOTE:
        # Adding an attribute here and getting an AttributeError saying
        # the attr doesn't exist? it has something to do with the order
        # of the attr in __slots__

        self._channels: dict[int, GuildChannel] = {}
        self._members: dict[int, Member] = {}
        self._scheduled_events: dict[int, ScheduledEvent] = {}
        self._voice_states: dict[int, VoiceState] = {}
        self._threads: dict[int, Thread] = {}
        self._state: ConnectionState = state
        self._from_data(data)

    def _add_channel(self, channel: GuildChannel, /) -> None:
        self._channels[channel.id] = channel

    def _remove_channel(self, channel: Snowflake, /) -> None:
        self._channels.pop(channel.id, None)

    def _voice_state_for(self, user_id: int, /) -> VoiceState | None:
        return self._voice_states.get(user_id)

    def _add_member(self, member: Member, /) -> None:
        self._members[member.id] = member

    def _get_and_update_member(
        self, payload: MemberPayload, user_id: int, cache_flag: bool, /
    ) -> Member:
        # we always get the member, and we only update if the cache_flag (this cache
        # flag should always be MemberCacheFlag.interaction) is set to True
        if user_id in self._members:
            member = self.get_member(user_id)
            member._update(payload) if cache_flag else None
        else:
            # NOTE:
            # This is a fallback in case the member is not found in the guild's members.
            # If this fallback occurs, multiple aspects of the Member
            # class will be incorrect such as status and activities.
            member = Member(guild=self, state=self._state, data=payload)  # type: ignore
            if cache_flag:
                self._members[user_id] = member
        return member

    def _store_thread(self, payload: ThreadPayload, /) -> Thread:
        thread = Thread(guild=self, state=self._state, data=payload)
        self._threads[thread.id] = thread
        return thread

    def _remove_member(self, member: Snowflake, /) -> None:
        self._members.pop(member.id, None)

    def _add_scheduled_event(self, event: ScheduledEvent, /) -> None:
        self._scheduled_events[event.id] = event

    def _remove_scheduled_event(self, event: Snowflake, /) -> None:
        self._scheduled_events.pop(event.id, None)

    def _scheduled_events_from_list(self, events: list[ScheduledEvent], /) -> None:
        self._scheduled_events.clear()
        for event in events:
            self._scheduled_events[event.id] = event

    def _add_thread(self, thread: Thread, /) -> None:
        self._threads[thread.id] = thread

    def _remove_thread(self, thread: Snowflake, /) -> None:
        self._threads.pop(thread.id, None)

    def _clear_threads(self) -> None:
        self._threads.clear()

    def _remove_threads_by_channel(self, channel_id: int) -> None:
        to_remove = [k for k, t in self._threads.items() if t.parent_id == channel_id]
        for k in to_remove:
            del self._threads[k]

    def _filter_threads(self, channel_ids: set[int]) -> dict[int, Thread]:
        to_remove: dict[int, Thread] = {
            k: t for k, t in self._threads.items() if t.parent_id in channel_ids
        }
        for k in to_remove:
            del self._threads[k]
        return to_remove

    def __str__(self) -> str:
        return self.name or ""

    def __repr__(self) -> str:
        attrs = (
            ("id", self.id),
            ("name", self.name),
            ("shard_id", self.shard_id),
            ("chunked", self.chunked),
            ("member_count", self._member_count),
        )
        inner = " ".join("%s=%r" % t for t in attrs)
        return f"<Guild {inner}>"

    def _update_voice_state(
        self, data: GuildVoiceState, channel_id: int
    ) -> tuple[Member | None, VoiceState, VoiceState]:
        user_id = int(data["user_id"])
        channel = self.get_channel(channel_id)
        try:
            # check if we should remove the voice state from cache
            if channel is None:
                after = self._voice_states.pop(user_id)
            else:
                after = self._voice_states[user_id]

            before = copy.copy(after)
            after._update(data, channel)
        except KeyError:
            # if we're here then we're getting added into the cache
            after = VoiceState(data=data, channel=channel)
            before = VoiceState(data=data, channel=None)
            self._voice_states[user_id] = after

        member = self.get_member(user_id)
        if member is None:
            try:
                member = Member(data=data["member"], state=self._state, guild=self)
            except KeyError:
                member = None

        return member, before, after

    def _add_role(self, role: Role, /) -> None:
        # roles get added to the bottom (position 1, pos 0 is @everyone)
        # so since self.roles has the @everyone role, we can't increment
        # its position because it's stuck at position 0. Luckily x += False
        # is equivalent to adding 0. So we cast the position to a bool and
        # increment it.
        for r in self._roles.values():
            r.position += not r.is_default()

        self._roles[role.id] = role

    def _remove_role(self, role_id: int, /) -> Role:
        # this raises KeyError if it fails.
        role = self._roles.pop(role_id)

        # since it didn't, we can change the positions now
        # basically the same as above except we only decrement
        # the position if we're above the role we deleted.
        for r in self._roles.values():
            r.position -= r.position > role.position

        return role

    def _from_data(self, guild: GuildPayload) -> None:
        member_count = guild.get("member_count")
        # Either the payload includes member_count, or it hasn't been set yet.
        # Prevents valid _member_count from suddenly changing to None
        if member_count is not None or not hasattr(self, "_member_count"):
            self._member_count: int | None = member_count

        self.name: str = guild.get("name")
        self.verification_level: VerificationLevel = try_enum(
            VerificationLevel, guild.get("verification_level")
        )
        self.default_notifications: NotificationLevel = try_enum(
            NotificationLevel, guild.get("default_message_notifications")
        )
        self.explicit_content_filter: ContentFilter = try_enum(
            ContentFilter, guild.get("explicit_content_filter", 0)
        )
        self.afk_timeout: int = guild.get("afk_timeout")
        self._icon: str | None = guild.get("icon")
        self._banner: str | None = guild.get("banner")
        self.unavailable: bool = guild.get("unavailable", False)
        self.id: int = int(guild["id"])
        self._roles: dict[int, Role] = {}
        state = self._state  # speed up attribute access
        for r in guild.get("roles", []):
            role = Role(guild=self, data=r, state=state)
            self._roles[role.id] = role

        self.mfa_level: MFALevel = guild.get("mfa_level")
        self.emojis: tuple[GuildEmoji, ...] = tuple(
            map(lambda d: state.store_emoji(self, d), guild.get("emojis", []))
        )
        self.stickers: tuple[GuildSticker, ...] = tuple(
            map(lambda d: state.store_sticker(self, d), guild.get("stickers", []))
        )
        self.features: list[GuildFeature] = guild.get("features", [])
        self._splash: str | None = guild.get("splash")
        self._system_channel_id: int | None = utils._get_as_snowflake(
            guild, "system_channel_id"
        )
        self.description: str | None = guild.get("description")
        self.max_presences: int | None = guild.get("max_presences")
        self.max_members: int | None = guild.get("max_members")
        self.max_video_channel_users: int | None = guild.get("max_video_channel_users")
        self.premium_tier: int = guild.get("premium_tier", 0)
        self.premium_subscription_count: int = (
            guild.get("premium_subscription_count") or 0
        )
        self.premium_progress_bar_enabled: bool = (
            guild.get("premium_progress_bar_enabled") or False
        )
        self._system_channel_flags: int = guild.get("system_channel_flags", 0)
        self.preferred_locale: str | None = guild.get("preferred_locale")
        self._discovery_splash: str | None = guild.get("discovery_splash")
        self._rules_channel_id: int | None = utils._get_as_snowflake(
            guild, "rules_channel_id"
        )
        self._public_updates_channel_id: int | None = utils._get_as_snowflake(
            guild, "public_updates_channel_id"
        )
        self.nsfw_level: NSFWLevel = try_enum(NSFWLevel, guild.get("nsfw_level", 0))
        self.approximate_presence_count = guild.get("approximate_presence_count")
        self.approximate_member_count = guild.get("approximate_member_count")

        self._stage_instances: dict[int, StageInstance] = {}
        for s in guild.get("stage_instances", []):
            stage_instance = StageInstance(guild=self, data=s, state=state)
            self._stage_instances[stage_instance.id] = stage_instance

        cache_joined = self._state.member_cache_flags.joined
        self_id = self._state.self_id
        for mdata in guild.get("members", []):
            member = Member(data=mdata, guild=self, state=state)
            if cache_joined or member.id == self_id:
                self._add_member(member)

        events = []
        for event in guild.get("guild_scheduled_events", []):
            creator = (
                None
                if not event.get("creator", None)
                else self.get_member(event.get("creator_id"))
            )
            events.append(
                ScheduledEvent(
                    state=self._state, guild=self, creator=creator, data=event
                )
            )
        self._scheduled_events_from_list(events)

        self._sync(guild)
        self._large: bool | None = (
            None if self._member_count is None else self._member_count >= 250
        )

        self.owner_id: int | None = utils._get_as_snowflake(guild, "owner_id")
        self.afk_channel: VoiceChannel | None = self.get_channel(
            utils._get_as_snowflake(guild, "afk_channel_id")
        )  # type: ignore

        for obj in guild.get("voice_states", []):
            self._update_voice_state(obj, int(obj["channel_id"]))

    # TODO: refactor/remove?
    def _sync(self, data: GuildPayload) -> None:
        try:
            self._large = data["large"]
        except KeyError:
            pass

        empty_tuple = ()
        for presence in data.get("presences", []):
            user_id = int(presence["user"]["id"])
            member = self.get_member(user_id)
            if member is not None:
                member._presence_update(presence, empty_tuple)  # type: ignore

        if "channels" in data:
            channels = data["channels"]
            for c in channels:
                factory, ch_type = _guild_channel_factory(c["type"])
                if factory:
                    self._add_channel(factory(guild=self, data=c, state=self._state))  # type: ignore

        if "threads" in data:
            threads = data["threads"]
            for thread in threads:
                self._add_thread(Thread(guild=self, state=self._state, data=thread))

    @property
    def channels(self) -> list[GuildChannel]:
        """A list of channels that belong to this guild."""
        return list(self._channels.values())

    @property
    def threads(self) -> list[Thread]:
        """A list of threads that you have permission to view.

        .. versionadded:: 2.0
        """
        return list(self._threads.values())

    @property
    def jump_url(self) -> str:
        """Returns a URL that allows the client to jump to the guild.

        .. versionadded:: 2.0
        """
        return f"https://discord.com/channels/{self.id}"

    @property
    def large(self) -> bool:
        """Indicates if the guild is a 'large' guild.

        A large guild is defined as having more than ``large_threshold`` count
        members, which for this library is set to the maximum of 250.
        """
        if self._large is None:
            return (self._member_count or len(self._members)) >= 250
        return self._large

    @property
    def voice_channels(self) -> list[VoiceChannel]:
        """A list of voice channels that belong to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, VoiceChannel)]
        r.sort(key=lambda c: (c.position or -1, c.id))
        return r

    @property
    def stage_channels(self) -> list[StageChannel]:
        """A list of stage channels that belong to this guild.

        .. versionadded:: 1.7

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, StageChannel)]
        r.sort(key=lambda c: (c.position or -1, c.id))
        return r

    @property
    def forum_channels(self) -> list[ForumChannel]:
        """A list of forum channels that belong to this guild.

        .. versionadded:: 2.0

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, ForumChannel)]
        r.sort(key=lambda c: (c.position or -1, c.id))
        return r

    @property
    def me(self) -> Member:
        """Similar to :attr:`Client.user` except an instance of :class:`Member`.
        This is essentially used to get the member version of yourself.
        """
        self_id = self._state.user.id
        # The self member is *always* cached
        return self.get_member(self_id)  # type: ignore

    @property
    def voice_client(self) -> VoiceClient | None:
        """Returns the :class:`VoiceClient` associated with this guild, if any."""
        return self._state._get_voice_client(self.id)

    @property
    def text_channels(self) -> list[TextChannel]:
        """A list of text channels that belong to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, TextChannel)]
        r.sort(key=lambda c: (c.position or -1, c.id))
        return r

    @property
    def categories(self) -> list[CategoryChannel]:
        """A list of categories that belong to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, CategoryChannel)]
        r.sort(key=lambda c: (c.position or -1, c.id))
        return r

    def by_category(self) -> list[ByCategoryItem]:
        """Returns every :class:`CategoryChannel` and their associated channels.

        These channels and categories are sorted in the official Discord UI order.

        If the channels do not have a category, then the first element of the tuple is
        ``None``.

        Returns
        -------
        List[Tuple[Optional[:class:`CategoryChannel`], List[:class:`abc.GuildChannel`]]]:
            The categories and their associated channels.
        """
        grouped: dict[int | None, list[GuildChannel]] = {}
        for channel in self._channels.values():
            if isinstance(channel, CategoryChannel):
                grouped.setdefault(channel.id, [])
                continue

            try:
                grouped[channel.category_id].append(channel)
            except KeyError:
                grouped[channel.category_id] = [channel]

        def key(t: ByCategoryItem) -> tuple[tuple[int, int], list[GuildChannel]]:
            k, v = t
            return (k.position or -1, k.id) if k else (-1, -1), v

        _get = self._channels.get
        as_list: list[ByCategoryItem] = [(_get(k), v) for k, v in grouped.items()]  # type: ignore
        as_list.sort(key=key)
        for _, channels in as_list:
            channels.sort(key=lambda c: (c._sorting_bucket, c.position or -1, c.id))
        return as_list

    def _resolve_channel(self, id: int | None, /) -> GuildChannel | Thread | None:
        if id is None:
            return

        return self._channels.get(id) or self._threads.get(id)

    def get_channel_or_thread(self, channel_id: int, /) -> Thread | GuildChannel | None:
        """Returns a channel or thread with the given ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        channel_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[Union[:class:`Thread`, :class:`.abc.GuildChannel`]]
            The returned channel or thread or ``None`` if not found.
        """
        return self._channels.get(channel_id) or self._threads.get(channel_id)

    def get_channel(self, channel_id: int, /) -> GuildChannel | None:
        """Returns a channel with the given ID.

        .. note::

            This does *not* search for threads.

        Parameters
        ----------
        channel_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`.abc.GuildChannel`]
            The returned channel or ``None`` if not found.
        """
        return self._channels.get(channel_id)

    def get_thread(self, thread_id: int, /) -> Thread | None:
        """Returns a thread with the given ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        thread_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Thread`]
            The returned thread or ``None`` if not found.
        """
        return self._threads.get(thread_id)

    @property
    def system_channel(self) -> TextChannel | None:
        """Returns the guild's channel used for system messages.

        If no channel is set, then this returns ``None``.
        """
        channel_id = self._system_channel_id
        return channel_id and self._channels.get(channel_id)  # type: ignore

    @property
    def system_channel_flags(self) -> SystemChannelFlags:
        """Returns the guild's system channel settings."""
        return SystemChannelFlags._from_value(self._system_channel_flags)

    @property
    def rules_channel(self) -> TextChannel | None:
        """Return's the guild's channel used for the rules.
        The guild must be a Community guild.

        If no channel is set, then this returns ``None``.

        .. versionadded:: 1.3
        """
        channel_id = self._rules_channel_id
        return channel_id and self._channels.get(channel_id)  # type: ignore

    @property
    def public_updates_channel(self) -> TextChannel | None:
        """Return's the guild's channel where admins and
        moderators of the guilds receive notices from Discord. The guild must be a
        Community guild.

        If no channel is set, then this returns ``None``.

        .. versionadded:: 1.4
        """
        channel_id = self._public_updates_channel_id
        return channel_id and self._channels.get(channel_id)  # type: ignore

    @property
    def emoji_limit(self) -> int:
        """The maximum number of emoji slots this guild has."""
        more_emoji = 200 if "MORE_EMOJI" in self.features else 50
        return max(more_emoji, self._PREMIUM_GUILD_LIMITS[self.premium_tier].emoji)

    @property
    def sticker_limit(self) -> int:
        """The maximum number of sticker slots this guild has.

        .. versionadded:: 2.0
        """
        more_stickers = 60 if "MORE_STICKERS" in self.features else 0
        return max(
            more_stickers, self._PREMIUM_GUILD_LIMITS[self.premium_tier].stickers
        )

    @property
    def bitrate_limit(self) -> int:
        """The maximum bitrate for voice channels this guild can have."""
        vip_guild = (
            self._PREMIUM_GUILD_LIMITS[1].bitrate
            if "VIP_REGIONS" in self.features
            else 96e3
        )
        return int(
            max(vip_guild, self._PREMIUM_GUILD_LIMITS[self.premium_tier].bitrate)
        )

    @property
    def filesize_limit(self) -> int:
        """The maximum number of bytes files can have when uploaded to this guild."""
        return self._PREMIUM_GUILD_LIMITS[self.premium_tier].filesize

    @property
    def members(self) -> list[Member]:
        """A list of members that belong to this guild."""
        return list(self._members.values())

    def get_member(self, user_id: int, /) -> Member | None:
        """Returns a member with the given ID.

        Parameters
        ----------
        user_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Member`]
            The member or ``None`` if not found.
        """
        return self._members.get(user_id)

    @property
    def premium_subscribers(self) -> list[Member]:
        """A list of members who have "boosted" this guild."""
        return [member for member in self.members if member.premium_since is not None]

    @property
    def roles(self) -> list[Role]:
        """Returns a :class:`list` of the guild's roles in hierarchy order.

        The first element of this list will be the lowest role in the
        hierarchy.
        """
        return sorted(self._roles.values())

    def get_role(self, role_id: int, /) -> Role | None:
        """Returns a role with the given ID.

        Parameters
        ----------
        role_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Role`]
            The role or ``None`` if not found.
        """
        return self._roles.get(role_id)

    @property
    def default_role(self) -> Role:
        """Gets the @everyone role that all members have by default."""
        # The @everyone role is *always* given
        return self.get_role(self.id)  # type: ignore

    @property
    def premium_subscriber_role(self) -> Role | None:
        """Gets the premium subscriber role, AKA "boost" role, in this guild.

        .. versionadded:: 1.6
        """
        for role in self._roles.values():
            if role.is_premium_subscriber():
                return role
        return None

    @property
    def self_role(self) -> Role | None:
        """Gets the role associated with this client's user, if any.

        .. versionadded:: 1.6
        """
        self_id = self._state.self_id
        for role in self._roles.values():
            tags = role.tags
            if tags and tags.bot_id == self_id:
                return role
        return None

    @property
    def stage_instances(self) -> list[StageInstance]:
        """Returns a :class:`list` of the guild's stage instances that
        are currently running.

        .. versionadded:: 2.0
        """
        return list(self._stage_instances.values())

    def get_stage_instance(self, stage_instance_id: int, /) -> StageInstance | None:
        """Returns a stage instance with the given ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        stage_instance_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`StageInstance`]
            The stage instance or ``None`` if not found.
        """
        return self._stage_instances.get(stage_instance_id)

    @property
    def owner(self) -> Member | None:
        """The member that owns the guild."""
        return self.get_member(self.owner_id)  # type: ignore

    @property
    def icon(self) -> Asset | None:
        """Returns the guild's icon asset, if available."""
        if self._icon is None:
            return None
        return Asset._from_guild_icon(self._state, self.id, self._icon)

    @property
    def banner(self) -> Asset | None:
        """Returns the guild's banner asset, if available."""
        if self._banner is None:
            return None
        return Asset._from_guild_image(
            self._state, self.id, self._banner, path="banners"
        )

    @property
    def splash(self) -> Asset | None:
        """Returns the guild's invite splash asset, if available."""
        if self._splash is None:
            return None
        return Asset._from_guild_image(
            self._state, self.id, self._splash, path="splashes"
        )

    @property
    def discovery_splash(self) -> Asset | None:
        """Returns the guild's discovery splash asset, if available."""
        if self._discovery_splash is None:
            return None
        return Asset._from_guild_image(
            self._state, self.id, self._discovery_splash, path="discovery-splashes"
        )

    @property
    def member_count(self) -> int:
        """Returns the true member count regardless of it being loaded fully or not.

        .. warning::

            Due to a Discord limitation, in order for this attribute to remain up-to-date and
            accurate, it requires :attr:`Intents.members` to be specified.
        """
        return self._member_count

    @property
    def chunked(self) -> bool:
        """Returns a boolean indicating if the guild is "chunked".

        A chunked guild means that :attr:`member_count` is equal to the
        number of members stored in the internal :attr:`members` cache.

        If this value returns ``False``, then you should request for
        offline members.
        """
        if self._member_count is None:
            return False
        return self._member_count == len(self._members)

    @property
    def shard_id(self) -> int:
        """Returns the shard ID for this guild if applicable."""
        count = self._state.shard_count
        if count is None:
            return 0
        return (self.id >> 22) % count

    @property
    def created_at(self) -> datetime.datetime:
        """Returns the guild's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def invites_disabled(self) -> bool:
        """Returns a boolean indicating if the guild invites are disabled."""
        return "INVITES_DISABLED" in self.features

    def get_member_named(self, name: str, /) -> Member | None:
        """Returns the first member found that matches the name provided.

        The name can have an optional discriminator argument, e.g. "Jake#0001"
        or "Jake" will both do the lookup. However, the former will give a more
        precise result. Note that the discriminator must have all 4 digits
        for this to work.

        If a nickname is passed, then it is looked up via the nickname. Note
        however, that a nickname + discriminator combo will not look up the nickname
        but rather the username + discriminator combo due to nickname + discriminator
        not being unique.

        If no member is found, ``None`` is returned.

        Parameters
        ----------
        name: :class:`str`
            The name of the member to lookup with an optional discriminator.

        Returns
        -------
        Optional[:class:`Member`]
            The member in this guild with the associated name. If not found
            then ``None`` is returned.
        """

        result = None
        members = self.members
        if len(name) > 5 and name[-5] == "#":
            # The 5 length is checking to see if #0000 is in the string,
            # as a#0000 has a length of 6, the minimum for a potential
            # discriminator lookup.
            potential_discriminator = name[-4:]

            # do the actual lookup and return if found
            # if it isn't found then we'll do a full name lookup below.
            result = utils.get(
                members, name=name[:-5], discriminator=potential_discriminator
            )
            if result is not None:
                return result

        return utils.find(lambda m: name in (m.nick, m.name, m.global_name), members)

    def _create_channel(
        self,
        name: str,
        channel_type: ChannelType,
        overwrites: dict[Role | Member, PermissionOverwrite] = MISSING,
        category: Snowflake | None = None,
        **options: Any,
    ):
        if overwrites is MISSING:
            overwrites = {}
        elif not isinstance(overwrites, dict):
            raise InvalidArgument("overwrites parameter expects a dict.")

        perms = []
        for target, perm in overwrites.items():
            if not isinstance(perm, PermissionOverwrite):
                raise InvalidArgument(
                    f"Expected PermissionOverwrite received {perm.__class__.__name__}"
                )

            allow, deny = perm.pair()
            payload = {
                "allow": allow.value,
                "deny": deny.value,
                "id": target.id,
                "type": (
                    abc._Overwrites.ROLE
                    if isinstance(target, Role)
                    else abc._Overwrites.MEMBER
                ),
            }

            perms.append(payload)

        parent_id = category.id if category else None
        return self._state.http.create_channel(
            self.id,
            channel_type.value,
            name=name,
            parent_id=parent_id,
            permission_overwrites=perms,
            **options,
        )

    async def create_text_channel(
        self,
        name: str,
        *,
        reason: str | None = None,
        category: CategoryChannel | None = None,
        position: int = MISSING,
        topic: str = MISSING,
        slowmode_delay: int = MISSING,
        nsfw: bool = MISSING,
        overwrites: dict[Role | Member, PermissionOverwrite] = MISSING,
    ) -> TextChannel:
        """|coro|

        Creates a :class:`TextChannel` for the guild.

        Note that you need the :attr:`~Permissions.manage_channels` permission
        to create the channel.

        The ``overwrites`` parameter can be used to create a 'secret'
        channel upon creation. This parameter expects a :class:`dict` of
        overwrites with the target (either a :class:`Member` or a :class:`Role`)
        as the key and a :class:`PermissionOverwrite` as the value.

        .. note::

            Creating a channel of a specified position will not update the position of
            other channels to follow suit. A follow-up call to :meth:`~TextChannel.edit`
            will be required to update the position of the channel in the channel list.

        Parameters
        ----------
        name: :class:`str`
            The channel's name.
        overwrites: Dict[Union[:class:`Role`, :class:`Member`, :class:`~discord.abc.Snowflake`], :class:`PermissionOverwrite`]
            The overwrites to apply to the channel. Useful for creating secret channels.
        category: Optional[:class:`CategoryChannel`]
            The category to place the newly created channel under.
            The permissions will be automatically synced to category if no
            overwrites are provided.
        position: :class:`int`
            The position in the channel list. This is a number that starts
            at 0. e.g. the top channel is position 0.
        topic: :class:`str`
            The new channel's topic.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel, in seconds.
            The maximum value possible is `21600`.
        nsfw: :class:`bool`
            To mark the channel as NSFW or not.
        reason: Optional[:class:`str`]
            The reason for creating this channel. Shows up on the audit log.

        Returns
        -------
        :class:`TextChannel`
            The channel that was just created.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Examples
        --------

        Creating a basic channel:

        .. code-block:: python3

            channel = await guild.create_text_channel('cool-channel')

        Creating a "secret" channel:

        .. code-block:: python3

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }

            channel = await guild.create_text_channel('secret', overwrites=overwrites)
        """

        options = {}
        if position is not MISSING:
            options["position"] = position

        if topic is not MISSING:
            options["topic"] = topic

        if slowmode_delay is not MISSING:
            options["rate_limit_per_user"] = slowmode_delay

        if nsfw is not MISSING:
            options["nsfw"] = nsfw

        data = await self._create_channel(
            name,
            overwrites=overwrites,
            channel_type=ChannelType.text,
            category=category,
            reason=reason,
            **options,
        )
        channel = TextChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_voice_channel(
        self,
        name: str,
        *,
        reason: str | None = None,
        category: CategoryChannel | None = None,
        position: int = MISSING,
        bitrate: int = MISSING,
        user_limit: int = MISSING,
        rtc_region: VoiceRegion | None = MISSING,
        video_quality_mode: VideoQualityMode = MISSING,
        overwrites: dict[Role | Member, PermissionOverwrite] = MISSING,
    ) -> VoiceChannel:
        """|coro|

        This is similar to :meth:`create_text_channel` except makes a :class:`VoiceChannel` instead.

        Parameters
        ----------
        name: :class:`str`
            The channel's name.
        overwrites: Dict[Union[:class:`Role`, :class:`Member`, :class:`~discord.abc.Snowflake`], :class:`PermissionOverwrite`]
            The overwrites to apply to the channel. Useful for creating secret channels.
        category: Optional[:class:`CategoryChannel`]
            The category to place the newly created channel under.
            The permissions will be automatically synced to category if no
            overwrites are provided.
        position: :class:`int`
            The position in the channel list. This is a number that starts
            at 0. e.g. the top channel is position 0.
        bitrate: :class:`int`
            The channel's preferred audio bitrate in bits per second.
        user_limit: :class:`int`
            The channel's limit for number of members that can be in a voice channel.
        rtc_region: Optional[:class:`VoiceRegion`]
            The region for the voice channel's voice communication.
            A value of ``None`` indicates automatic voice region detection.

            .. versionadded:: 1.7
        video_quality_mode: :class:`VideoQualityMode`
            The camera video quality for the voice channel's participants.

            .. versionadded:: 2.0
        reason: Optional[:class:`str`]
            The reason for creating this channel. Shows up on the audit log.

        Returns
        -------
        :class:`VoiceChannel`
            The channel that was just created.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.
        """
        options = {}
        if position is not MISSING:
            options["position"] = position

        if bitrate is not MISSING:
            options["bitrate"] = bitrate

        if user_limit is not MISSING:
            options["user_limit"] = user_limit

        if rtc_region is not MISSING:
            options["rtc_region"] = None if rtc_region is None else str(rtc_region)

        if video_quality_mode is not MISSING:
            options["video_quality_mode"] = video_quality_mode.value

        data = await self._create_channel(
            name,
            overwrites=overwrites,
            channel_type=ChannelType.voice,
            category=category,
            reason=reason,
            **options,
        )
        channel = VoiceChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_stage_channel(
        self,
        name: str,
        *,
        topic: str,
        position: int = MISSING,
        overwrites: dict[Role | Member, PermissionOverwrite] = MISSING,
        category: CategoryChannel | None = None,
        reason: str | None = None,
    ) -> StageChannel:
        """|coro|

        This is similar to :meth:`create_text_channel` except makes a :class:`StageChannel` instead.

        .. versionadded:: 1.7

        Parameters
        ----------
        name: :class:`str`
            The channel's name.
        topic: :class:`str`
            The new channel's topic.
        overwrites: Dict[Union[:class:`Role`, :class:`Member`, :class:`~discord.abc.Snowflake`], :class:`PermissionOverwrite`]
            The overwrites to apply to the channel. Useful for creating secret channels.
        category: Optional[:class:`CategoryChannel`]
            The category to place the newly created channel under.
            The permissions will be automatically synced to category if no
            overwrites are provided.
        position: :class:`int`
            The position in the channel list. This is a number that starts
            at 0. e.g. the top channel is position 0.
        reason: Optional[:class:`str`]
            The reason for creating this channel. Shows up on the audit log.

        Returns
        -------
        :class:`StageChannel`
            The channel that was just created.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.
        """

        options: dict[str, Any] = {
            "topic": topic,
        }
        if position is not MISSING:
            options["position"] = position

        data = await self._create_channel(
            name,
            overwrites=overwrites,
            channel_type=ChannelType.stage_voice,
            category=category,
            reason=reason,
            **options,
        )
        channel = StageChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_forum_channel(
        self,
        name: str,
        *,
        reason: str | None = None,
        category: CategoryChannel | None = None,
        position: int = MISSING,
        topic: str = MISSING,
        slowmode_delay: int = MISSING,
        nsfw: bool = MISSING,
        overwrites: dict[Role | Member, PermissionOverwrite] = MISSING,
        default_reaction_emoji: GuildEmoji | int | str = MISSING,
    ) -> ForumChannel:
        """|coro|

        Creates a :class:`ForumChannel` for the guild.

        Note that you need the :attr:`~Permissions.manage_channels` permission
        to create the channel.

        The ``overwrites`` parameter can be used to create a 'secret'
        channel upon creation. This parameter expects a :class:`dict` of
        overwrites with the target (either a :class:`Member` or a :class:`Role`)
        as the key and a :class:`PermissionOverwrite` as the value.

        .. note::

            Creating a channel of a specified position will not update the position of
            other channels to follow suit. A follow-up call to :meth:`~ForumChannel.edit`
            will be required to update the position of the channel in the channel list.

        Parameters
        ----------
        name: :class:`str`
            The channel's name.
        overwrites: Dict[Union[:class:`Role`, :class:`Member`, :class:`~discord.abc.Snowflake`], :class:`PermissionOverwrite`]
            The overwrites to apply to the channel. Useful for creating secret channels.
        category: Optional[:class:`CategoryChannel`]
            The category to place the newly created channel under.
            The permissions will be automatically synced to category if no
            overwrites are provided.
        position: :class:`int`
            The position in the channel list. This is a number that starts
            at 0. e.g. the top channel is position 0.
        topic: :class:`str`
            The new channel's topic.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel, in seconds.
            The maximum value possible is `21600`.
        nsfw: :class:`bool`
            To mark the channel as NSFW or not.
        reason: Optional[:class:`str`]
            The reason for creating this channel. Shows up on the audit log.
        default_reaction_emoji: Optional[:class:`GuildEmoji` | :class:`int` | :class:`str`]
            The default reaction emoji.
            Can be a unicode emoji or a custom emoji in the forms:
            :class:`GuildEmoji`, snowflake ID, string representation (eg. '<a:emoji_name:emoji_id>').

            .. versionadded:: v2.5

        Returns
        -------
        :class:`ForumChannel`
            The channel that was just created.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The argument is not in proper form.

        Examples
        --------

        Creating a basic channel:

        .. code-block:: python3

            channel = await guild.create_forum_channel('cool-channel')

        Creating a "secret" channel:

        .. code-block:: python3

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }

            channel = await guild.create_forum_channel('secret', overwrites=overwrites)
        """

        options = {}
        if position is not MISSING:
            options["position"] = position

        if topic is not MISSING:
            options["topic"] = topic

        if slowmode_delay is not MISSING:
            options["rate_limit_per_user"] = slowmode_delay

        if nsfw is not MISSING:
            options["nsfw"] = nsfw

        if default_reaction_emoji is not MISSING:
            if isinstance(
                default_reaction_emoji, _EmojiTag
            ):  # GuildEmoji, PartialEmoji
                default_reaction_emoji = default_reaction_emoji._to_partial()
            elif isinstance(default_reaction_emoji, int):
                default_reaction_emoji = PartialEmoji(
                    name=None, id=default_reaction_emoji
                )
            elif isinstance(default_reaction_emoji, str):
                default_reaction_emoji = PartialEmoji.from_str(default_reaction_emoji)
            else:
                raise InvalidArgument(
                    "default_reaction_emoji must be of type: GuildEmoji | int | str"
                )

            options["default_reaction_emoji"] = (
                default_reaction_emoji._to_forum_reaction_payload()
            )

        data = await self._create_channel(
            name,
            overwrites=overwrites,
            channel_type=ChannelType.forum,
            category=category,
            reason=reason,
            **options,
        )
        channel = ForumChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_category(
        self,
        name: str,
        *,
        overwrites: dict[Role | Member, PermissionOverwrite] = MISSING,
        reason: str | None = None,
        position: int = MISSING,
    ) -> CategoryChannel:
        """|coro|

        Same as :meth:`create_text_channel` except makes a :class:`CategoryChannel` instead.

        .. note::

            The ``category`` parameter is not supported in this function since categories
            cannot have categories.

        Returns
        -------
        :class:`CategoryChannel`
            The channel that was just created.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.
        """
        options: dict[str, Any] = {}
        if position is not MISSING:
            options["position"] = position

        data = await self._create_channel(
            name,
            overwrites=overwrites,
            channel_type=ChannelType.category,
            reason=reason,
            **options,
        )
        channel = CategoryChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    create_category_channel = create_category

    async def leave(self) -> None:
        """|coro|

        Leaves the guild.

        .. note::

            You cannot leave the guild that you own, you must delete it instead
            via :meth:`delete`.

        Raises
        ------
        HTTPException
            Leaving the guild failed.
        """
        await self._state.http.leave_guild(self.id)

    async def delete(self) -> None:
        """|coro|

        Deletes the guild. You must be the guild owner to delete the
        guild.

        Raises
        ------
        HTTPException
            Deleting the guild failed.
        Forbidden
            You do not have permissions to delete the guild.
        """
        await self._state.http.delete_guild(self.id)

    async def set_mfa_required(self, required: bool, *, reason: str = None) -> None:
        """|coro|

        Set whether it is required to have MFA enabled on your account
        to perform moderation actions. You must be the guild owner to do this.

        Parameters
        ----------
        required: :class:`bool`
            Whether MFA should be required to perform moderation actions.
        reason: :class:`str`
            The reason to show up in the audit log.

        Raises
        ------
        HTTPException
            The operation failed.
        Forbidden
            You are not the owner of the guild.
        """
        await self._state.http.edit_guild_mfa(self.id, required, reason=reason)

    async def edit(
        self,
        *,
        reason: str | None = MISSING,
        name: str = MISSING,
        description: str | None = MISSING,
        icon: bytes | None = MISSING,
        banner: bytes | None = MISSING,
        splash: bytes | None = MISSING,
        discovery_splash: bytes | None = MISSING,
        community: bool = MISSING,
        afk_channel: VoiceChannel | None = MISSING,
        owner: Snowflake = MISSING,
        afk_timeout: int = MISSING,
        default_notifications: NotificationLevel = MISSING,
        verification_level: VerificationLevel = MISSING,
        explicit_content_filter: ContentFilter = MISSING,
        system_channel: TextChannel | None = MISSING,
        system_channel_flags: SystemChannelFlags = MISSING,
        preferred_locale: str = MISSING,
        rules_channel: TextChannel | None = MISSING,
        public_updates_channel: TextChannel | None = MISSING,
        premium_progress_bar_enabled: bool = MISSING,
        disable_invites: bool = MISSING,
        discoverable: bool = MISSING,
        disable_raid_alerts: bool = MISSING,
        enable_activity_feed: bool = MISSING,
    ) -> Guild:
        r"""|coro|

        Edits the guild.

        You must have the :attr:`~Permissions.manage_guild` permission
        to edit the guild.

        .. versionchanged:: 1.4
            The `rules_channel` and `public_updates_channel` keyword-only parameters were added.

        .. versionchanged:: 2.0
            The `discovery_splash` and `community` keyword-only parameters were added.

        .. versionchanged:: 2.0
            The newly updated guild is returned.

        Parameters
        ----------
        name: :class:`str`
            The new name of the guild.
        description: Optional[:class:`str`]
            The new description of the guild. Could be ``None`` for no description.
            This is only available to guilds that contain ``PUBLIC`` in :attr:`Guild.features`.
        icon: :class:`bytes`
            A :term:`py:bytes-like object` representing the icon. Only PNG/JPEG is supported.
            GIF is only available to guilds that contain ``ANIMATED_ICON`` in :attr:`Guild.features`.
            Could be ``None`` to denote removal of the icon.
        banner: :class:`bytes`
            A :term:`py:bytes-like object` representing the banner.
            Could be ``None`` to denote removal of the banner. This is only available to guilds that contain
            ``BANNER`` in :attr:`Guild.features`.
        splash: :class:`bytes`
            A :term:`py:bytes-like object` representing the invite splash.
            Only PNG/JPEG supported. Could be ``None`` to denote removing the
            splash. This is only available to guilds that contain ``INVITE_SPLASH``
            in :attr:`Guild.features`.
        discovery_splash: :class:`bytes`
            A :term:`py:bytes-like object` representing the discovery splash.
            Only PNG/JPEG supported. Could be ``None`` to denote removing the
            splash. This is only available to guilds that contain ``DISCOVERABLE``
            in :attr:`Guild.features`.
        community: :class:`bool`
            Whether the guild should be a Community guild. If set to ``True``\, both ``rules_channel``
            and ``public_updates_channel`` parameters are required.
        afk_channel: Optional[:class:`VoiceChannel`]
            The new channel that is the AFK channel. Could be ``None`` for no AFK channel.
        afk_timeout: :class:`int`
            The number of seconds until someone is moved to the AFK channel.
        owner: :class:`Member`
            The new owner of the guild to transfer ownership to. Note that you must
            be owner of the guild to do this.
        verification_level: :class:`VerificationLevel`
            The new verification level for the guild.
        default_notifications: :class:`NotificationLevel`
            The new default notification level for the guild.
        explicit_content_filter: :class:`ContentFilter`
            The new explicit content filter for the guild.
        system_channel: Optional[:class:`TextChannel`]
            The new channel that is used for the system channel. Could be ``None`` for no system channel.
        system_channel_flags: :class:`SystemChannelFlags`
            The new system channel settings to use with the new system channel.
        preferred_locale: :class:`str`
            The new preferred locale for the guild. Used as the primary language in the guild.
            If set, this must be an ISO 639 code, e.g. ``en-US`` or ``ja`` or ``zh-CN``.
        rules_channel: Optional[:class:`TextChannel`]
            The new channel that is used for rules. This is only available to
            guilds that contain ``PUBLIC`` in :attr:`Guild.features`. Could be ``None`` for no rules
            channel.
        public_updates_channel: Optional[:class:`TextChannel`]
            The new channel that is used for public updates from Discord. This is only available to
            guilds that contain ``PUBLIC`` in :attr:`Guild.features`. Could be ``None`` for no
            public updates channel.
        premium_progress_bar_enabled: :class:`bool`
            Whether the guild should have premium progress bar enabled.
        disable_invites: :class:`bool`
            Whether the guild should have server invites enabled or disabled.
        discoverable: :class:`bool`
            Whether the guild should be discoverable in the discover tab.
        disable_raid_alerts: :class:`bool`
            Whether activity alerts for the guild should be disabled.
        enable_activity_feed: class:`bool`
            Whether the guild's user activity feed should be enabled.
        reason: Optional[:class:`str`]
            The reason for editing this guild. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to edit the guild.
        HTTPException
            Editing the guild failed.
        InvalidArgument
            The image format passed in to ``icon`` is invalid. It must be
            PNG or JPG. This is also raised if you are not the owner of the
            guild and request an ownership transfer.

        Returns
        --------
        :class:`Guild`
            The newly updated guild. Note that this has the same limitations as
            mentioned in :meth:`Client.fetch_guild` and may not have full data.
        """

        http = self._state.http

        fields: dict[str, Any] = {}
        if name is not MISSING:
            fields["name"] = name

        if description is not MISSING:
            fields["description"] = description

        if preferred_locale is not MISSING:
            fields["preferred_locale"] = preferred_locale

        if afk_timeout is not MISSING:
            fields["afk_timeout"] = afk_timeout

        if icon is not MISSING:
            fields["icon"] = icon if icon is None else utils._bytes_to_base64_data(icon)
        if banner is not MISSING:
            if banner is None:
                fields["banner"] = banner
            else:
                fields["banner"] = utils._bytes_to_base64_data(banner)

        if splash is not MISSING:
            if splash is None:
                fields["splash"] = splash
            else:
                fields["splash"] = utils._bytes_to_base64_data(splash)

        if discovery_splash is not MISSING:
            if discovery_splash is None:
                fields["discovery_splash"] = discovery_splash
            else:
                fields["discovery_splash"] = utils._bytes_to_base64_data(
                    discovery_splash
                )

        if default_notifications is not MISSING:
            if not isinstance(default_notifications, NotificationLevel):
                raise InvalidArgument(
                    "default_notifications field must be of type NotificationLevel"
                )
            fields["default_message_notifications"] = default_notifications.value

        if afk_channel is not MISSING:
            if afk_channel is None:
                fields["afk_channel_id"] = afk_channel
            else:
                fields["afk_channel_id"] = afk_channel.id

        if system_channel is not MISSING:
            if system_channel is None:
                fields["system_channel_id"] = system_channel
            else:
                fields["system_channel_id"] = system_channel.id

        if rules_channel is not MISSING:
            if rules_channel is None:
                fields["rules_channel_id"] = rules_channel
            else:
                fields["rules_channel_id"] = rules_channel.id

        if public_updates_channel is not MISSING:
            if public_updates_channel is None:
                fields["public_updates_channel_id"] = public_updates_channel
            else:
                fields["public_updates_channel_id"] = public_updates_channel.id

        if owner is not MISSING:
            if self.owner_id != self._state.self_id:
                raise InvalidArgument(
                    "To transfer ownership you must be the owner of the guild."
                )

            fields["owner_id"] = owner.id

        if verification_level is not MISSING:
            if not isinstance(verification_level, VerificationLevel):
                raise InvalidArgument(
                    "verification_level field must be of type VerificationLevel"
                )

            fields["verification_level"] = verification_level.value

        if explicit_content_filter is not MISSING:
            if not isinstance(explicit_content_filter, ContentFilter):
                raise InvalidArgument(
                    "explicit_content_filter field must be of type ContentFilter"
                )

            fields["explicit_content_filter"] = explicit_content_filter.value

        if system_channel_flags is not MISSING:
            if not isinstance(system_channel_flags, SystemChannelFlags):
                raise InvalidArgument(
                    "system_channel_flags field must be of type SystemChannelFlags"
                )

            fields["system_channel_flags"] = system_channel_flags.value

        if premium_progress_bar_enabled is not MISSING:
            fields["premium_progress_bar_enabled"] = premium_progress_bar_enabled

        features: list[GuildFeature] = self.features.copy()

        if community is not MISSING:
            if community:
                if (
                    "rules_channel_id" in fields
                    and "public_updates_channel_id" in fields
                ):
                    if "COMMUNITY" not in features:
                        features.append("COMMUNITY")
                else:
                    raise InvalidArgument(
                        "community field requires both rules_channel and public_updates_channel fields to be provided"
                    )
            else:
                if "COMMUNITY" in features:
                    if "rules_channel_id" in fields:
                        fields["rules_channel_id"] = None
                    if "public_updates_channel_id" in fields:
                        fields["public_updates_channel_id"] = None
                    features.remove("COMMUNITY")

        if disable_invites is not MISSING:
            if disable_invites:
                if "INVITES_DISABLED" not in features:
                    features.append("INVITES_DISABLED")
            else:
                if "INVITES_DISABLED" in features:
                    features.remove("INVITES_DISABLED")

        if discoverable is not MISSING:
            if discoverable:
                if "DISCOVERABLE" not in features:
                    features.append("DISCOVERABLE")
            else:
                if "DISCOVERABLE" in features:
                    features.remove("DISCOVERABLE")

        if disable_raid_alerts is not MISSING:
            if disable_raid_alerts:
                if "RAID_ALERTS_DISABLED" not in features:
                    features.append("RAID_ALERTS_DISABLED")
            else:
                if "RAID_ALERTS_DISABLED" in features:
                    features.remove("RAID_ALERTS_DISABLED")

        if enable_activity_feed is not MISSING:
            if enable_activity_feed:
                if "ACTIVITY_FEED_ENABLED_BY_USER" not in features:
                    features.append("ACTIVITY_FEED_ENABLED_BY_USER")
                if "ACTIVITY_FEED_DISABLED_BY_USER" in features:
                    features.remove("ACTIVITY_FEED_DISABLED_BY_USER")
            else:
                if "ACTIVITY_FEED_ENABLED_BY_USER" in features:
                    features.remove("ACTIVITY_FEED_ENABLED_BY_USER")
                if "ACTIVITY_FEED_DISABLED_BY_USER" not in features:
                    features.append("ACTIVITY_FEED_DISABLED_BY_USER")

        if self.features != features:
            fields["features"] = features

        data = await http.edit_guild(self.id, reason=reason, **fields)
        return Guild(data=data, state=self._state)

    async def fetch_channels(self) -> Sequence[GuildChannel]:
        """|coro|

        Retrieves all :class:`abc.GuildChannel` that the guild has.

        .. note::

            This method is an API call. For general usage, consider :attr:`channels` instead.

        .. versionadded:: 1.2

        Returns
        -------
        Sequence[:class:`abc.GuildChannel`]
            All channels in the guild.

        Raises
        ------
        InvalidData
            An unknown channel type was received from Discord.
        HTTPException
            Retrieving the channels failed.
        """
        data = await self._state.http.get_all_guild_channels(self.id)

        def convert(d):
            factory, ch_type = _guild_channel_factory(d["type"])
            if factory is None:
                raise InvalidData(
                    "Unknown channel type {type} for channel ID {id}.".format_map(d)
                )

            channel = factory(guild=self, state=self._state, data=d)
            return channel

        return [convert(d) for d in data]

    async def active_threads(self) -> list[Thread]:
        """|coro|

        Returns a list of active :class:`Thread` that the client can access.

        This includes both private and public threads.

        .. versionadded:: 2.0

        Returns
        -------
        List[:class:`Thread`]
            The active threads

        Raises
        ------
        HTTPException
            The request to get the active threads failed.
        """
        data = await self._state.http.get_active_threads(self.id)
        threads = [
            Thread(guild=self, state=self._state, data=d)
            for d in data.get("threads", [])
        ]
        thread_lookup: dict[int, Thread] = {thread.id: thread for thread in threads}
        for member in data.get("members", []):
            thread = thread_lookup.get(int(member["id"]))
            if thread is not None:
                thread._add_member(ThreadMember(parent=thread, data=member))

        return threads

    # TODO: Remove Optional typing here when async iterators are refactored
    def fetch_members(
        self, *, limit: int | None = 1000, after: SnowflakeTime | None = None
    ) -> MemberIterator:
        """Retrieves an :class:`.AsyncIterator` that enables receiving the guild's members. In order to use this,
        :meth:`Intents.members` must be enabled.

        .. note::

            This method is an API call. For general usage, consider :attr:`members` instead.

        .. versionadded:: 1.3

        All parameters are optional.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of members to retrieve. Defaults to 1000.
            Pass ``None`` to fetch all members. Note that this is potentially slow.
        after: Optional[Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve members after this date or object.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.

        Yields
        ------
        :class:`.Member`
            The member with the member data parsed.

        Raises
        ------
        ClientException
            The members intent is not enabled.
        HTTPException
            Getting the members failed.

        Examples
        --------

        Usage ::

            async for member in guild.fetch_members(limit=150):
                print(member.name)

        Flattening into a list ::

            members = await guild.fetch_members(limit=150).flatten()
            # members is now a list of Member...
        """

        if not self._state._intents.members:
            raise ClientException("Intents.members must be enabled to use this.")

        return MemberIterator(self, limit=limit, after=after)

    async def search_members(self, query: str, *, limit: int = 1000) -> list[Member]:
        """Search for guild members whose usernames or nicknames start with the query string. Unlike :meth:`fetch_members`, this does not require :meth:`Intents.members`.

        .. note::

            This method is an API call. For general usage, consider filtering :attr:`members` instead.

        .. versionadded:: 2.6

        Parameters
        ----------
        query: :class:`str`
            Searches for usernames and nicknames that start with this string, case-insensitive.
        limit: :class:`int`
            The maximum number of members to retrieve, up to 1000.

        Returns
        -------
        List[:class:`Member`]
            The list of members that have matched the query.

        Raises
        ------
        HTTPException
            Getting the members failed.
        """

        data = await self._state.http.search_members(self.id, query, limit)
        return [Member(data=m, guild=self, state=self._state) for m in data]

    async def fetch_member(self, member_id: int, /) -> Member:
        """|coro|

        Retrieves a :class:`Member` from a guild ID, and a member ID.

        .. note::

            This method is an API call. If you have :attr:`Intents.members` and
            member cache enabled, consider :meth:`get_member` instead.

        Parameters
        ----------
        member_id: :class:`int`
            The member's ID to fetch from.

        Returns
        -------
        :class:`Member`
            The member from the member ID.

        Raises
        ------
        Forbidden
            You do not have access to the guild.
        HTTPException
            Fetching the member failed.
        """
        data = await self._state.http.get_member(self.id, member_id)
        return Member(data=data, state=self._state, guild=self)

    async def fetch_ban(self, user: Snowflake) -> BanEntry:
        """|coro|

        Retrieves the :class:`BanEntry` for a user.

        You must have the :attr:`~Permissions.ban_members` permission
        to get this information.

        Parameters
        ----------
        user: :class:`abc.Snowflake`
            The user to get ban information from.

        Returns
        -------
        :class:`BanEntry`
            The :class:`BanEntry` object for the specified user.

        Raises
        ------
        Forbidden
            You do not have proper permissions to get the information.
        NotFound
            This user is not banned.
        HTTPException
            An error occurred while fetching the information.
        """
        data: BanPayload = await self._state.http.get_ban(user.id, self.id)
        return BanEntry(
            user=User(state=self._state, data=data["user"]), reason=data["reason"]
        )

    async def fetch_channel(self, channel_id: int, /) -> GuildChannel | Thread:
        """|coro|

        Retrieves a :class:`.abc.GuildChannel` or :class:`.Thread` with the specified ID.

        .. note::

            This method is an API call. For general usage, consider :meth:`get_channel_or_thread` instead.

        .. versionadded:: 2.0

        Returns
        -------
        Union[:class:`.abc.GuildChannel`, :class:`.Thread`]
            The channel from the ID.

        Raises
        ------
        InvalidData
            An unknown channel type was received from Discord
            or the guild the channel belongs to is not the same
            as the one in this object points to.
        HTTPException
            Retrieving the channel failed.
        NotFound
            Invalid Channel ID.
        Forbidden
            You do not have permission to fetch this channel.
        """
        data = await self._state.http.get_channel(channel_id)

        factory, ch_type = _threaded_guild_channel_factory(data["type"])
        if factory is None:
            raise InvalidData(
                "Unknown channel type {type} for channel ID {id}.".format_map(data)
            )

        if ch_type in (ChannelType.group, ChannelType.private):
            raise InvalidData("Channel ID resolved to a private channel")

        guild_id = int(data["guild_id"])
        if self.id != guild_id:
            raise InvalidData("Guild ID resolved to a different guild")

        channel: GuildChannel = factory(guild=self, state=self._state, data=data)  # type: ignore
        return channel

    def bans(
        self,
        limit: int | None = None,
        before: Snowflake | None = None,
        after: Snowflake | None = None,
    ) -> BanIterator:
        """|coro|

        Retrieves an :class:`.AsyncIterator` that enables receiving the guild's bans. In order to use this, you must
        have the :attr:`~Permissions.ban_members` permission.
        Users will always be returned in ascending order sorted by user ID.
        If both the ``before`` and ``after`` parameters are provided, only before is respected.

        .. versionchanged:: 2.5
            The ``before``. and ``after`` parameters were changed. They are now of the type :class:`.abc.Snowflake` instead of
            `SnowflakeTime` to comply with the discord api.

        .. versionchanged:: 2.0
            The ``limit``, ``before``. and ``after`` parameters were added. Now returns a :class:`.BanIterator` instead
            of a list of ``BanEntry`` objects.

        All parameters are optional.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of bans to retrieve. Defaults to 1000.
        before: Optional[:class:`.abc.Snowflake`]
            Retrieve bans before the given user.
        after: Optional[:class:`.abc.Snowflake`]
            Retrieve bans after the given user.

        Yields
        ------
        :class:`.BanEntry`
            The ban entry for the ban.

        Raises
        ------
        Forbidden
            You do not have proper permissions to get the information.
        HTTPException
            An error occurred while fetching the information.

        Examples
        --------

        Usage ::

            async for ban in guild.bans(limit=150):
                print(ban.user.name)

        Flattening into a list ::

            bans = await guild.bans(limit=150).flatten()
            # bans is now a list of BanEntry...
        """

        return BanIterator(self, limit=limit, before=before, after=after)

    async def prune_members(
        self,
        *,
        days: int,
        compute_prune_count: bool = True,
        roles: list[Snowflake] = MISSING,
        reason: str | None = None,
    ) -> int | None:
        r"""|coro|

        Prunes the guild from its inactive members.

        The inactive members are denoted if they have not logged on in
        ``days`` number of days and have no roles.

        You must have the :attr:`~Permissions.kick_members` permission
        to use this.

        To check how many members you would prune without actually pruning,
        see the :meth:`estimate_pruned_members` function.

        To prune members that have specific roles see the ``roles`` parameter.

        .. versionchanged:: 1.4
            The ``roles`` keyword-only parameter was added.

        Parameters
        -----------
        days: :class:`int`
            The number of days before counting as inactive.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.
        compute_prune_count: :class:`bool`
            Whether to compute the prune count. This defaults to ``True``
            which makes it prone to timeouts in very large guilds. In order
            to prevent timeouts, you must set this to ``False``. If this is
            set to ``False``\, then this function will always return ``None``.
        roles: List[:class:`abc.Snowflake`]
            A list of :class:`abc.Snowflake` that represent roles to include in the pruning process. If a member
            has a role that is not specified, they'll be excluded.

        Raises
        -------
        Forbidden
            You do not have permissions to prune members.
        HTTPException
            An error occurred while pruning members.
        InvalidArgument
            An integer was not passed for ``days``.

        Returns
        ---------
        Optional[:class:`int`]
            The number of members pruned. If ``compute_prune_count`` is ``False``
            then this returns ``None``.
        """

        if not isinstance(days, int):
            raise InvalidArgument(
                "Expected int for ``days``, received"
                f" {days.__class__.__name__} instead."
            )

        role_ids = [str(role.id) for role in roles] if roles else []
        data = await self._state.http.prune_members(
            self.id,
            days,
            compute_prune_count=compute_prune_count,
            roles=role_ids,
            reason=reason,
        )
        return data["pruned"]

    async def templates(self) -> list[Template]:
        """|coro|

        Gets the list of templates from this guild.

        Requires :attr:`~.Permissions.manage_guild` permissions.

        .. versionadded:: 1.7

        Returns
        -------
        List[:class:`Template`]
            The templates for this guild.

        Raises
        ------
        Forbidden
            You don't have permissions to get the templates.
        """
        from .template import Template

        data = await self._state.http.guild_templates(self.id)
        return [Template(data=d, state=self._state) for d in data]

    async def webhooks(self) -> list[Webhook]:
        """|coro|

        Gets the list of webhooks from this guild.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        Returns
        -------
        List[:class:`Webhook`]
            The webhooks for this guild.

        Raises
        ------
        Forbidden
            You don't have permissions to get the webhooks.
        """

        from .webhook import Webhook

        data = await self._state.http.guild_webhooks(self.id)
        return [Webhook.from_state(d, state=self._state) for d in data]

    async def estimate_pruned_members(
        self, *, days: int, roles: list[Snowflake] = MISSING
    ) -> int:
        """|coro|

        Similar to :meth:`prune_members` except instead of actually
        pruning members, it returns how many members it would prune
        from the guild had it been called.

        Parameters
        ----------
        days: :class:`int`
            The number of days before counting as inactive.
        roles: List[:class:`abc.Snowflake`]
            A list of :class:`abc.Snowflake` that represent roles to include in the estimate. If a member
            has a role that is not specified, they'll be excluded.

            .. versionadded:: 1.7

        Returns
        -------
        :class:`int`
            The number of members estimated to be pruned.

        Raises
        ------
        Forbidden
            You do not have permissions to prune members.
        HTTPException
            An error occurred while fetching the prune members estimate.
        InvalidArgument
            An integer was not passed for ``days``.
        """

        if not isinstance(days, int):
            raise InvalidArgument(
                "Expected int for ``days``, received"
                f" {days.__class__.__name__} instead."
            )

        role_ids = [str(role.id) for role in roles] if roles else []
        data = await self._state.http.estimate_pruned_members(self.id, days, role_ids)
        return data["pruned"]

    async def invites(self) -> list[Invite]:
        """|coro|

        Returns a list of all active instant invites from the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to get
        this information.

        Returns
        -------
        List[:class:`Invite`]
            The list of invites that are currently active.

        Raises
        ------
        Forbidden
            You do not have proper permissions to get the information.
        HTTPException
            An error occurred while fetching the information.
        """

        data = await self._state.http.invites_from(self.id)
        result = []
        for invite in data:
            channel = self.get_channel(int(invite["channel"]["id"]))
            result.append(
                Invite(state=self._state, data=invite, guild=self, channel=channel)
            )

        return result

    async def create_template(
        self, *, name: str, description: str = MISSING
    ) -> Template:
        """|coro|

        Creates a template for the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        .. versionadded:: 1.7

        Parameters
        ----------
        name: :class:`str`
            The name of the template.
        description: :class:`str`
            The description of the template.
        """
        from .template import Template

        payload = {"name": name}

        if description:
            payload["description"] = description

        data = await self._state.http.create_template(self.id, payload)

        return Template(state=self._state, data=data)

    async def create_integration(self, *, type: str, id: int) -> None:
        """|coro|

        Attaches an integration to the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        .. versionadded:: 1.4

        Parameters
        ----------
        type: :class:`str`
            The integration type (e.g. Twitch).
        id: :class:`int`
            The integration ID.

        Raises
        ------
        Forbidden
            You do not have permission to create the integration.
        HTTPException
            The account could not be found.
        """
        await self._state.http.create_integration(self.id, type, id)

    async def integrations(self) -> list[Integration]:
        """|coro|

        Returns a list of all integrations attached to the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        .. versionadded:: 1.4

        Returns
        -------
        List[:class:`Integration`]
            The list of integrations that are attached to the guild.

        Raises
        ------
        Forbidden
            You do not have permission to create the integration.
        HTTPException
            Fetching the integrations failed.
        """
        data = await self._state.http.get_all_integrations(self.id)

        def convert(d):
            factory, _ = _integration_factory(d["type"])
            if factory is None:
                raise InvalidData(
                    "Unknown integration type {type!r} for integration ID {id}".format_map(
                        d
                    )
                )
            return factory(guild=self, data=d)

        return [convert(d) for d in data]

    async def fetch_stickers(self) -> list[GuildSticker]:
        r"""|coro|

        Retrieves a list of all :class:`Sticker`\s for the guild.

        .. versionadded:: 2.0

        .. note::

            This method is an API call. For general usage, consider :attr:`stickers` instead.

        Raises
        ---------
        HTTPException
            An error occurred fetching the stickers.

        Returns
        --------
        List[:class:`GuildSticker`]
            The retrieved stickers.
        """
        data = await self._state.http.get_all_guild_stickers(self.id)
        return [GuildSticker(state=self._state, data=d) for d in data]

    async def fetch_sticker(self, sticker_id: int, /) -> GuildSticker:
        """|coro|

        Retrieves a custom :class:`Sticker` from the guild.

        .. versionadded:: 2.0

        .. note::

            This method is an API call.
            For general usage, consider iterating over :attr:`stickers` instead.

        Parameters
        ----------
        sticker_id: :class:`int`
            The sticker's ID.

        Returns
        -------
        :class:`GuildSticker`
            The retrieved sticker.

        Raises
        ------
        NotFound
            The sticker requested could not be found.
        HTTPException
            An error occurred fetching the sticker.
        """
        data = await self._state.http.get_guild_sticker(self.id, sticker_id)
        return GuildSticker(state=self._state, data=data)

    async def create_sticker(
        self,
        *,
        name: str,
        description: str | None = None,
        emoji: str,
        file: File,
        reason: str | None = None,
    ) -> GuildSticker:
        """|coro|

        Creates a :class:`Sticker` for the guild.

        You must have :attr:`~Permissions.manage_emojis_and_stickers` permission to
        do this.

        .. versionadded:: 2.0

        Parameters
        ----------
        name: :class:`str`
            The sticker name. Must be 2 to 30 characters.
        description: Optional[:class:`str`]
            The sticker's description. If used, must be 2 to 100 characters.
        emoji: :class:`str`
            The name of a unicode emoji that represents the sticker's expression.
        file: :class:`File`
            The file of the sticker to upload.
        reason: :class:`str`
            The reason for creating this sticker. Shows up on the audit log.

        Returns
        -------
        :class:`GuildSticker`
            The created sticker.

        Raises
        ------
        Forbidden
            You are not allowed to create stickers.
        HTTPException
            An error occurred creating a sticker.
        TypeError
            The parameters for the sticker are not correctly formatted.
        """
        if not (2 <= len(name) <= 30):
            raise TypeError('"name" parameter must be 2 to 30 characters long.')

        if description and not (2 <= len(description) <= 100):
            raise TypeError('"description" parameter must be 2 to 200 characters long.')

        payload = {"name": name, "description": description or ""}

        try:
            emoji = unicodedata.name(emoji)
        except TypeError:
            pass
        else:
            emoji = emoji.replace(" ", "_")

        payload["tags"] = emoji

        data = await self._state.http.create_guild_sticker(
            self.id, payload, file, reason
        )
        return self._state.store_sticker(self, data)

    async def delete_sticker(
        self, sticker: Snowflake, *, reason: str | None = None
    ) -> None:
        """|coro|

        Deletes the custom :class:`Sticker` from the guild.

        You must have :attr:`~Permissions.manage_emojis_and_stickers` permission to
        do this.

        .. versionadded:: 2.0

        Parameters
        ----------
        sticker: :class:`abc.Snowflake`
            The sticker you are deleting.
        reason: Optional[:class:`str`]
            The reason for deleting this sticker. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You are not allowed to delete stickers.
        HTTPException
            An error occurred deleting the sticker.
        """
        await self._state.http.delete_guild_sticker(self.id, sticker.id, reason)

    async def fetch_emojis(self) -> list[GuildEmoji]:
        r"""|coro|

        Retrieves all custom :class:`GuildEmoji`\s from the guild.

        .. note::

            This method is an API call. For general usage, consider :attr:`emojis` instead.

        Raises
        ---------
        HTTPException
            An error occurred fetching the emojis.

        Returns
        --------
        List[:class:`GuildEmoji`]
            The retrieved emojis.
        """
        data = await self._state.http.get_all_custom_emojis(self.id)
        return [GuildEmoji(guild=self, state=self._state, data=d) for d in data]

    async def fetch_emoji(self, emoji_id: int, /) -> GuildEmoji:
        """|coro|

        Retrieves a custom :class:`GuildEmoji` from the guild.

        .. note::

            This method is an API call.
            For general usage, consider iterating over :attr:`emojis` instead.

        Parameters
        ----------
        emoji_id: :class:`int`
            The emoji's ID.

        Returns
        -------
        :class:`GuildEmoji`
            The retrieved emoji.

        Raises
        ------
        NotFound
            The emoji requested could not be found.
        HTTPException
            An error occurred fetching the emoji.
        """
        data = await self._state.http.get_custom_emoji(self.id, emoji_id)
        return GuildEmoji(guild=self, state=self._state, data=data)

    async def create_custom_emoji(
        self,
        *,
        name: str,
        image: bytes,
        roles: list[Role] = MISSING,
        reason: str | None = None,
    ) -> GuildEmoji:
        r"""|coro|

        Creates a custom :class:`GuildEmoji` for the guild.

        There is currently a limit of 50 static and animated emojis respectively per guild,
        unless the guild has the ``MORE_EMOJI`` feature which extends the limit to 200.

        You must have the :attr:`~Permissions.manage_emojis` permission to
        do this.

        Parameters
        -----------
        name: :class:`str`
            The emoji name. Must be at least 2 characters.
        image: :class:`bytes`
            The :term:`py:bytes-like object` representing the image data to use.
            Only JPG, PNG and GIF images are supported.
        roles: List[:class:`Role`]
            A :class:`list` of :class:`Role`\s that can use this emoji. Leave empty to make it available to everyone.
        reason: Optional[:class:`str`]
            The reason for creating this emoji. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You are not allowed to create emojis.
        HTTPException
            An error occurred creating an emoji.

        Returns
        --------
        :class:`GuildEmoji`
            The created emoji.
        """

        img = utils._bytes_to_base64_data(image)
        role_ids = [role.id for role in roles] if roles else []
        data = await self._state.http.create_custom_emoji(
            self.id, name, img, roles=role_ids, reason=reason
        )
        return self._state.store_emoji(self, data)

    async def delete_emoji(
        self, emoji: Snowflake, *, reason: str | None = None
    ) -> None:
        """|coro|

        Deletes the custom :class:`GuildEmoji` from the guild.

        You must have :attr:`~Permissions.manage_emojis` permission to
        do this.

        Parameters
        ----------
        emoji: :class:`abc.Snowflake`
            The emoji you are deleting.
        reason: Optional[:class:`str`]
            The reason for deleting this emoji. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You are not allowed to delete emojis.
        HTTPException
            An error occurred deleting the emoji.
        """

        await self._state.http.delete_custom_emoji(self.id, emoji.id, reason=reason)

    async def fetch_roles(self) -> list[Role]:
        """|coro|

        Retrieves all :class:`Role` that the guild has.

        .. note::

            This method is an API call. For general usage, consider :attr:`roles` instead.

        .. versionadded:: 1.3

        Returns
        -------
        List[:class:`Role`]
            All roles in the guild.

        Raises
        ------
        HTTPException
            Retrieving the roles failed.
        """
        data = await self._state.http.get_roles(self.id)
        return [Role(guild=self, state=self._state, data=d) for d in data]

    async def fetch_role(self, role_id: int) -> Role:
        """|coro|

        Retrieves a :class:`Role` that the guild has.

        .. note::

            This method is an API call. For general usage, consider using :attr:`get_role` instead.

        .. versionadded:: 2.7

        Returns
        -------
        :class:`Role`
            The role in the guild with the specified ID.

        Raises
        ------
        HTTPException
            Retrieving the role failed.
        """
        data = await self._state.http.get_role(self.id, role_id)
        return Role(guild=self, state=self._state, data=data)

    async def _fetch_role(self, role_id: int) -> Role:
        """|coro|

        Retrieves a :class:`Role` that the guild has.

        .. note::

            This method is an API call. For general usage, consider using :attr:`get_role` instead.

        .. versionadded:: 2.0

        Parameters
        ----------
        role_id: :class:`int`
            The role ID to fetch from the guild.

        Returns
        -------
        Optional[:class:`Role`]
            The role in the guild with the specified ID.
            Returns ``None`` if not found.

        Raises
        ------
        HTTPException
            Retrieving the role failed.
        """
        roles = await self.fetch_roles()
        for role in roles:
            if role.id == role_id:
                return role

    @overload
    async def create_role(
        self,
        *,
        reason: str | None = ...,
        name: str = ...,
        permissions: Permissions = ...,
        colour: Colour | int = ...,
        colours: RoleColours = ...,
        holographic: bool = ...,
        hoist: bool = ...,
        mentionable: bool = ...,
        icon: bytes | None = MISSING,
        unicode_emoji: str | None = MISSING,
    ) -> Role: ...

    @overload
    async def create_role(
        self,
        *,
        reason: str | None = ...,
        name: str = ...,
        permissions: Permissions = ...,
        color: Colour | int = ...,
        colors: RoleColours = ...,
        holographic: bool = ...,
        hoist: bool = ...,
        mentionable: bool = ...,
        icon: bytes | None = ...,
        unicode_emoji: str | None = ...,
    ) -> Role: ...

    async def create_role(
        self,
        *,
        name: str = MISSING,
        permissions: Permissions = MISSING,
        color: Colour | int = MISSING,
        colour: Colour | int = MISSING,
        colors: RoleColours = MISSING,
        colours: RoleColours = MISSING,
        holographic: bool = MISSING,
        hoist: bool = MISSING,
        mentionable: bool = MISSING,
        reason: str | None = None,
        icon: bytes | None = MISSING,
        unicode_emoji: str | None = MISSING,
    ) -> Role:
        """|coro|

        Creates a :class:`Role` for the guild.

        All fields are optional.

        You must have the :attr:`~Permissions.manage_roles` permission to
        do this.

        .. versionchanged:: 1.6
            Can now pass ``int`` to ``colour`` keyword-only parameter.

        Parameters
        ----------
        name: :class:`str`
            The role name. Defaults to 'new role'.
        permissions: :class:`Permissions`
            The permissions to have. Defaults to no permissions.
        colour: Union[:class:`Colour`, :class:`int`]
            The colour for the role. Defaults to :meth:`Colour.default`.
            This is aliased to ``color`` as well.
        hoist: :class:`bool`
            Indicates if the role should be shown separately in the member list.
            Defaults to ``False``.
        mentionable: :class:`bool`
            Indicates if the role should be mentionable by others.
            Defaults to ``False``.
        reason: Optional[:class:`str`]
            The reason for creating this role. Shows up on the audit log.
        icon: Optional[:class:`bytes`]
            A :term:`py:bytes-like object` representing the icon. Only PNG/JPEG/WebP is supported.
            If this argument is passed, ``unicode_emoji`` is set to None.
            Only available to guilds that contain ``ROLE_ICONS`` in :attr:`Guild.features`.
        unicode_emoji: Optional[:class:`str`]
            The role's unicode emoji. If this argument is passed, ``icon`` is set to None.
            Only available to guilds that contain ``ROLE_ICONS`` in :attr:`Guild.features`.

        Returns
        -------
        :class:`Role`
            The newly created role.

        Raises
        ------
        Forbidden
            You do not have permissions to create the role.
        HTTPException
            Creating the role failed.
        InvalidArgument
            An invalid keyword argument was given.
        """
        fields: dict[str, Any] = {}
        if permissions is not MISSING:
            fields["permissions"] = str(permissions.value)
        else:
            fields["permissions"] = "0"

        actual_colour = colour if colour not in (MISSING, None) else color

        if isinstance(actual_colour, int):
            actual_colour = Colour(actual_colour)

        if actual_colour not in (MISSING, None):
            utils.warn_deprecated("colour", "colours", "2.7")
            actual_colours = RoleColours(primary=actual_colour)
        elif holographic:
            actual_colours = RoleColours.holographic()
        else:
            actual_colours = colours or colors or RoleColours.default()

        if isinstance(actual_colours, RoleColours):
            if "ENHANCED_ROLE_COLORS" not in self.features:
                actual_colours.secondary = None
                actual_colours.tertiary = None
            fields["colors"] = actual_colours._to_dict()
        else:
            raise InvalidArgument(
                "colours parameter must be of type RoleColours, not {0.__class__.__name__}".format(
                    actual_colours
                )
            )

        if hoist is not MISSING:
            fields["hoist"] = hoist

        if mentionable is not MISSING:
            fields["mentionable"] = mentionable

        if name is not MISSING:
            fields["name"] = name

        if icon is not MISSING:
            if icon is None:
                fields["icon"] = None
            else:
                fields["icon"] = utils._bytes_to_base64_data(icon)
                fields["unicode_emoji"] = None

        if unicode_emoji is not MISSING:
            fields["unicode_emoji"] = unicode_emoji
            fields["icon"] = None

        data = await self._state.http.create_role(self.id, reason=reason, **fields)
        role = Role(guild=self, data=data, state=self._state)

        # TODO: add to cache
        return role

    async def edit_role_positions(
        self, positions: dict[Snowflake, int], *, reason: str | None = None
    ) -> list[Role]:
        """|coro|

        Bulk edits a list of :class:`Role` in the guild.

        You must have the :attr:`~Permissions.manage_roles` permission to
        do this.

        .. versionadded:: 1.4

        Example:

        .. code-block:: python3

            positions = {
                bots_role: 1, # penultimate role
                tester_role: 2,
                admin_role: 6
            }

            await guild.edit_role_positions(positions=positions)

        Parameters
        ----------
        positions: Dict[:class:`Role`, :class:`int`]
            A :class:`dict` of :class:`Role` to :class:`int` to change the positions
            of each given role.
        reason: Optional[:class:`str`]
            The reason for editing the role positions. Shows up on the audit log.

        Returns
        -------
        List[:class:`Role`]
            A list of all the roles in the guild.

        Raises
        ------
        Forbidden
            You do not have permissions to move the roles.
        HTTPException
            Moving the roles failed.
        InvalidArgument
            An invalid keyword argument was given.
        """
        if not isinstance(positions, dict):
            raise InvalidArgument("positions parameter expects a dict.")

        role_positions: list[dict[str, Any]] = []
        for role, position in positions.items():
            payload = {"id": role.id, "position": position}

            role_positions.append(payload)

        data = await self._state.http.move_role_position(
            self.id, role_positions, reason=reason
        )
        roles: list[Role] = []
        for d in data:
            role = Role(guild=self, data=d, state=self._state)
            roles.append(role)
            self._roles[role.id] = role

        return roles

    async def kick(self, user: Snowflake, *, reason: str | None = None) -> None:
        """|coro|

        Kicks a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.kick_members` permission to
        do this.

        Parameters
        ----------
        user: :class:`abc.Snowflake`
            The user to kick from their guild.
        reason: Optional[:class:`str`]
            The reason the user got kicked.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to kick.
        HTTPException
            Kicking failed.
        """
        await self._state.http.kick(user.id, self.id, reason=reason)

    async def ban(
        self,
        user: Snowflake,
        *,
        delete_message_seconds: int | None = None,
        reason: str | None = None,
    ) -> None:
        """|coro|

        Bans a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.ban_members` permission to
        do this.

        Parameters
        ----------
        user: :class:`abc.Snowflake`
            The user to ban from their guild.
        delete_message_seconds: Optional[:class:`int`]
            The number of seconds worth of messages to delete from
            the user in the guild. The minimum is 0 and the maximum
            is 604800 (i.e. 7 days). The default is 0.
        reason: Optional[:class:`str`]
            The reason the user got banned.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to ban.
        HTTPException
            Banning failed.
        """

        if delete_message_seconds is not None and not (
            0 <= delete_message_seconds <= 604800
        ):
            raise TypeError(
                "delete_message_seconds must be between 0 and 604800 seconds."
            )

        await self._state.http.ban(
            user.id, self.id, delete_message_seconds, reason=reason
        )

    async def bulk_ban(
        self,
        *users: Snowflake,
        delete_message_seconds: int | None = None,
        reason: str | None = None,
    ) -> tuple[list[Snowflake], list[Snowflake]]:
        r"""|coro|

        Bulk ban users from the guild.

        The users must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.ban_members` permission to
        do this.

        Example Usage: ::

            # Ban multiple users
            successes, failures = await guild.bulk_ban(user1, user2, user3, ..., reason="Raid")

            # Ban a list of users
            successes, failures = await guild.bulk_ban(*users)

        Parameters
        ----------
        \*users: :class:`abc.Snowflake`
            An argument list of users to ban from the guild, up to 200.
        delete_message_seconds: Optional[:class:`int`]
            The number of seconds worth of messages to delete from
            the user in the guild. The minimum is 0 and the maximum
            is 604800 (i.e. 7 days). The default is 0.
        reason: Optional[:class:`str`]
            The reason the users were banned.

        Returns
        -------
        Tuple[List[:class:`abc.Snowflake`], List[:class:`abc.Snowflake`]]
            Returns two lists: the first contains members that were successfully banned, while the second is members that could not be banned.

        Raises
        ------
        ValueError
            You tried to ban more than 200 users.
        Forbidden
            You do not have the proper permissions to ban.
        HTTPException
            No users were banned.
        """

        if delete_message_seconds is not None and not (
            0 <= delete_message_seconds <= 604800
        ):
            raise TypeError(
                "delete_message_seconds must be between 0 and 604800 seconds."
            )

        if len(users) > 200 or len(users) < 1:
            raise ValueError(
                "The number of users to be banned must be between 1 and 200."
            )

        data = await self._state.http.bulk_ban(
            [u.id for u in users],
            self.id,
            delete_message_seconds,
            reason=reason,
        )
        banned = [u for u in users if str(u.id) in data["banned_users"]]
        failed = [u for u in users if str(u.id) in data["failed_users"]]
        return banned, failed

    async def unban(self, user: Snowflake, *, reason: str | None = None) -> None:
        """|coro|

        Unbans a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.ban_members` permission to
        do this.

        Parameters
        ----------
        user: :class:`abc.Snowflake`
            The user to unban.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to unban.
        HTTPException
            Unbanning failed.
        """
        await self._state.http.unban(user.id, self.id, reason=reason)

    async def vanity_invite(self) -> Invite | None:
        """|coro|

        Returns the guild's special vanity invite.

        The guild must have ``VANITY_URL`` in :attr:`~Guild.features`.

        You must have the :attr:`~Permissions.manage_guild` permission to use
        this as well.

        Returns
        -------
        Optional[:class:`Invite`]
            The special vanity invite. If ``None`` then the guild does not
            have a vanity invite set.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to get this.
        HTTPException
            Retrieving the vanity invite failed.
        """

        # we start with { code: abc }
        payload = await self._state.http.get_vanity_code(self.id)
        if not payload["code"]:
            return None

        # get the vanity URL channel since default channels aren't
        # reliable or a thing anymore
        data = await self._state.http.get_invite(payload["code"])

        channel = self.get_channel(int(data["channel"]["id"]))
        payload["revoked"] = False
        payload["temporary"] = False
        payload["max_uses"] = 0
        payload["max_age"] = 0
        payload["uses"] = payload.get("uses", 0)
        return Invite(state=self._state, data=payload, guild=self, channel=channel)

    # TODO: use MISSING when async iterators get refactored
    def audit_logs(
        self,
        *,
        limit: int | None = 100,
        before: SnowflakeTime | None = None,
        after: SnowflakeTime | None = None,
        user: Snowflake = None,
        action: AuditLogAction = None,
    ) -> AuditLogIterator:
        """Returns an :class:`AsyncIterator` that enables receiving the guild's audit logs.

        You must have the :attr:`~Permissions.view_audit_log` permission to use this.

        See `API documentation <https://discord.com/developers/docs/resources/audit-log#get-guild-audit-log>`_
        for more information about the `before` and `after` parameters.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of entries to retrieve. If ``None`` retrieve all entries.
        before: Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]
            Retrieve entries before this date or entry.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]
            Retrieve entries after this date or entry.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        user: :class:`abc.Snowflake`
            The moderator to filter entries from.
        action: :class:`AuditLogAction`
            The action to filter with.

        Yields
        ------
        :class:`AuditLogEntry`
            The audit log entry.

        Raises
        ------
        Forbidden
            You are not allowed to fetch audit logs
        HTTPException
            An error occurred while fetching the audit logs.

        Examples
        --------

        Getting the first 100 entries: ::

            async for entry in guild.audit_logs(limit=100):
                print(f'{entry.user} did {entry.action} to {entry.target}')

        Getting entries for a specific action: ::

            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban):
                print(f'{entry.user} banned {entry.target}')

        Getting entries made by a specific user: ::

            entries = await guild.audit_logs(limit=None, user=guild.me).flatten()
            await channel.send(f'I made {len(entries)} moderation actions.')
        """
        user_id = user.id if user is not None else None
        if action:
            action = action.value

        return AuditLogIterator(
            self,
            before=before,
            after=after,
            limit=limit,
            user_id=user_id,
            action_type=action,
        )

    async def widget(self) -> Widget:
        """|coro|

        Returns the widget of the guild.

        .. note::

            The guild must have the widget enabled to get this information.

        Returns
        -------
        :class:`Widget`
            The guild's widget.

        Raises
        ------
        Forbidden
            The widget for this guild is disabled.
        HTTPException
            Retrieving the widget failed.
        """
        data = await self._state.http.get_widget(self.id)

        return Widget(state=self._state, data=data)

    async def edit_widget(
        self, *, enabled: bool = MISSING, channel: Snowflake | None = MISSING
    ) -> None:
        """|coro|

        Edits the widget of the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        use this

        .. versionadded:: 2.0

        Parameters
        ----------
        enabled: :class:`bool`
            Whether to enable the widget for the guild.
        channel: Optional[:class:`~discord.abc.Snowflake`]
            The new widget channel. ``None`` removes the widget channel.

        Raises
        ------
        Forbidden
            You do not have permission to edit the widget.
        HTTPException
            Editing the widget failed.
        """
        payload = {}
        if channel is not MISSING:
            payload["channel_id"] = None if channel is None else channel.id
        if enabled is not MISSING:
            payload["enabled"] = enabled

        await self._state.http.edit_widget(self.id, payload=payload)

    async def chunk(self, *, cache: bool = True) -> None:
        """|coro|

        Requests all members that belong to this guild. In order to use this,
        :meth:`Intents.members` must be enabled.

        This is a websocket operation and can be slow.

        .. versionadded:: 1.5

        Parameters
        ----------
        cache: :class:`bool`
            Whether to cache the members as well.

        Raises
        ------
        ClientException
            The members intent is not enabled.
        """

        if not self._state._intents.members:
            raise ClientException("Intents.members must be enabled to use this.")

        if not self._state.is_guild_evicted(self):
            return await self._state.chunk_guild(self, cache=cache)

    async def query_members(
        self,
        query: str | None = None,
        *,
        limit: int | None = 5,
        user_ids: list[int] | None = None,
        presences: bool = False,
        cache: bool = True,
    ) -> list[Member]:
        """|coro|

        Request members that belong to this guild whose username starts with
        the query given.

        This is a websocket operation and can be slow.

        .. versionadded:: 1.3

        Parameters
        ----------
        query: Optional[:class:`str`]
            The string that the username's start with.
        user_ids: Optional[List[:class:`int`]]
            List of user IDs to search for. If the user ID is not in the guild then it won't be returned.

            .. versionadded:: 1.4
        limit: Optional[:class:`int`]
            The maximum number of members to send back. If no query is passed, passing ``None`` returns all members.
            If a ``query`` or ``user_ids`` is passed, must be between 1 and 100. Defaults to 5.
        presences: Optional[:class:`bool`]
            Whether to request for presences to be provided. This defaults
            to ``False``.

            .. versionadded:: 1.6

        cache: :class:`bool`
            Whether to cache the members internally. This makes operations
            such as :meth:`get_member` work for those that matched. Defaults to ``True``.

        Returns
        -------
        List[:class:`Member`]
            The list of members that have matched the query.

        Raises
        ------
        asyncio.TimeoutError
            The query timed out waiting for the members.
        ValueError
            Invalid parameters were passed to the function
        ClientException
            The presences intent is not enabled.
        """

        if presences and not self._state._intents.presences:
            raise ClientException("Intents.presences must be enabled to use this.")

        if not limit or limit > 100 or limit < 1:
            if query or user_ids:
                raise ValueError(
                    "limit must be between 1 and 100 when using query or user_ids"
                )
            if not limit:
                query = ""
                limit = 0

        if query is None:
            if user_ids is None:
                raise ValueError("Must pass query or user_ids, or set limit to None")

        if user_ids is not None and query is not None:
            raise ValueError("Cannot pass both query and user_ids")

        if user_ids is not None and not user_ids:
            raise ValueError("user_ids must contain at least 1 value")

        return await self._state.query_members(
            self,
            query=query,
            limit=limit,
            user_ids=user_ids,
            presences=presences,
            cache=cache,
        )

    async def change_voice_state(
        self,
        *,
        channel: VocalGuildChannel | None,
        self_mute: bool = False,
        self_deaf: bool = False,
    ):
        """|coro|

        Changes client's voice state in the guild.

        .. versionadded:: 1.4

        Parameters
        ----------
        channel: Optional[Union[:class:`VoiceChannel`, :class:`StageChannel`]]
            Channel the client wants to join. Use ``None`` to disconnect.
        self_mute: :class:`bool`
            Indicates if the client should be self-muted.
        self_deaf: :class:`bool`
            Indicates if the client should be self-deafened.
        """
        ws = self._state._get_websocket(self.id)
        channel_id = channel.id if channel else None
        await ws.voice_state(self.id, channel_id, self_mute, self_deaf)

    async def welcome_screen(self):
        """|coro|

        Returns the :class:`WelcomeScreen` of the guild.

        The guild must have ``COMMUNITY`` in :attr:`~Guild.features`.

        You must have the :attr:`~Permissions.manage_guild` permission in order to get this.

        .. versionadded:: 2.0

        Returns
        -------
        :class:`WelcomeScreen`
            The welcome screen of guild.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to get this.
        HTTPException
            Retrieving the welcome screen failed somehow.
        NotFound
            The guild doesn't have a welcome screen or community feature is disabled.
        """
        data = await self._state.http.get_welcome_screen(self.id)
        return WelcomeScreen(data=data, guild=self)

    @overload
    async def edit_welcome_screen(
        self,
        *,
        description: str | None = ...,
        welcome_channels: list[WelcomeScreenChannel] | None = ...,
        enabled: bool | None = ...,
    ) -> WelcomeScreen: ...

    @overload
    async def edit_welcome_screen(self) -> None: ...

    async def edit_welcome_screen(self, **options):
        """|coro|

        A shorthand for :attr:`WelcomeScreen.edit` without fetching the welcome screen.

        You must have the :attr:`~Permissions.manage_guild` permission in the
        guild to do this.

        The guild must have ``COMMUNITY`` in :attr:`Guild.features`

        Parameters
        ----------
        description: Optional[:class:`str`]
            The new description of welcome screen.
        welcome_channels: Optional[List[:class:`WelcomeScreenChannel`]]
            The welcome channels. The order of the channels would be same as the passed list order.
        enabled: Optional[:class:`bool`]
            Whether the welcome screen should be displayed.
        reason: Optional[:class:`str`]
            The reason that shows up on audit log.

        Returns
        -------
        :class:`WelcomeScreen`
            The edited welcome screen.

        Raises
        ------
        HTTPException
            Editing the welcome screen failed somehow.
        Forbidden
            You don't have permissions to edit the welcome screen.
        NotFound
            This welcome screen does not exist.
        """

        welcome_channels = options.get("welcome_channels", [])
        welcome_channels_data = []

        for channel in welcome_channels:
            if not isinstance(channel, WelcomeScreenChannel):
                raise TypeError(
                    "welcome_channels parameter must be a list of WelcomeScreenChannel."
                )

            welcome_channels_data.append(channel.to_dict())

        options["welcome_channels"] = welcome_channels_data

        if options:
            new = await self._state.http.edit_welcome_screen(
                self.id, options, reason=options.get("reason")
            )
            return WelcomeScreen(data=new, guild=self)

    async def fetch_scheduled_events(
        self, *, with_user_count: bool = True
    ) -> list[ScheduledEvent]:
        """|coro|

        Returns a list of :class:`ScheduledEvent` in the guild.

        .. note::

            This method is an API call. For general usage, consider :attr:`scheduled_events` instead.

        Parameters
        ----------
        with_user_count: Optional[:class:`bool`]
            If the scheduled event should be fetched with the number of
            users that are interested in the events.
            Defaults to ``True``.

        Returns
        -------
        List[:class:`ScheduledEvent`]
            The fetched scheduled events.

        Raises
        ------
        ClientException
            The scheduled events intent is not enabled.
        HTTPException
            Getting the scheduled events failed.
        """
        data = await self._state.http.get_scheduled_events(
            self.id, with_user_count=with_user_count
        )
        result = []
        for event in data:
            creator = (
                None
                if not event.get("creator", None)
                else self.get_member(event.get("creator_id"))
            )
            result.append(
                ScheduledEvent(
                    state=self._state, guild=self, creator=creator, data=event
                )
            )

        self._scheduled_events_from_list(result)
        return result

    async def fetch_scheduled_event(
        self, event_id: int, /, *, with_user_count: bool = True
    ) -> ScheduledEvent | None:
        """|coro|

        Retrieves a :class:`ScheduledEvent` from event ID.

        .. note::

            This method is an API call. If you have :attr:`Intents.scheduled_events`,
            consider :meth:`get_scheduled_event` instead.

        Parameters
        ----------
        event_id: :class:`int`
            The event's ID to fetch with.
        with_user_count: Optional[:class:`bool`]
            If the scheduled vent should be fetched with the number of
            users that are interested in the event.
            Defaults to ``True``.

        Returns
        -------
        Optional[:class:`ScheduledEvent`]
            The scheduled event from the event ID.

        Raises
        ------
        HTTPException
            Fetching the event failed.
        NotFound
            Event not found.
        """
        data = await self._state.http.get_scheduled_event(
            guild_id=self.id, event_id=event_id, with_user_count=with_user_count
        )
        creator = (
            None
            if not data.get("creator", None)
            else self.get_member(data.get("creator_id"))
        )
        event = ScheduledEvent(
            state=self._state, guild=self, creator=creator, data=data
        )

        old_event = self._scheduled_events.get(event.id)
        if old_event:
            self._scheduled_events[event.id] = event
        else:
            self._add_scheduled_event(event)

        return event

    def get_scheduled_event(self, event_id: int, /) -> ScheduledEvent | None:
        """Returns a Scheduled Event with the given ID.

        Parameters
        ----------
        event_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`ScheduledEvent`]
            The scheduled event or ``None`` if not found.
        """
        return self._scheduled_events.get(event_id)

    async def create_scheduled_event(
        self,
        *,
        name: str,
        description: str = MISSING,
        start_time: datetime,
        end_time: datetime = MISSING,
        location: str | int | VoiceChannel | StageChannel | ScheduledEventLocation,
        privacy_level: ScheduledEventPrivacyLevel = ScheduledEventPrivacyLevel.guild_only,
        reason: str | None = None,
        image: bytes = MISSING,
    ) -> ScheduledEvent | None:
        """|coro|
        Creates a scheduled event.

        Parameters
        ----------
        name: :class:`str`
            The name of the scheduled event.
        description: Optional[:class:`str`]
            The description of the scheduled event.
        start_time: :class:`datetime.datetime`
            A datetime object of when the scheduled event is supposed to start.
        end_time: Optional[:class:`datetime.datetime`]
            A datetime object of when the scheduled event is supposed to end.
        location: :class:`ScheduledEventLocation`
            The location of where the event is happening.
        privacy_level: :class:`ScheduledEventPrivacyLevel`
            The privacy level of the event. Currently, the only possible value
            is :attr:`ScheduledEventPrivacyLevel.guild_only`, which is default,
            so there is no need to change this parameter.
        reason: Optional[:class:`str`]
            The reason to show in the audit log.
        image: Optional[:class:`bytes`]
            The cover image of the scheduled event

        Returns
        -------
        Optional[:class:`ScheduledEvent`]
            The created scheduled event.

        Raises
        ------
        Forbidden
            You do not have the Manage Events permission.
        HTTPException
            The operation failed.
        """
        payload: dict[str, str | int] = {
            "name": name,
            "scheduled_start_time": start_time.isoformat(),
            "privacy_level": int(privacy_level),
        }

        if not isinstance(location, ScheduledEventLocation):
            location = ScheduledEventLocation(state=self._state, value=location)

        payload["entity_type"] = location.type.value

        if location.type == ScheduledEventLocationType.external:
            payload["channel_id"] = None
            payload["entity_metadata"] = {"location": location.value}
        else:
            payload["channel_id"] = location.value.id
            payload["entity_metadata"] = None

        if description is not MISSING:
            payload["description"] = description

        if end_time is not MISSING:
            payload["scheduled_end_time"] = end_time.isoformat()

        if image is not MISSING:
            payload["image"] = utils._bytes_to_base64_data(image)

        data = await self._state.http.create_scheduled_event(
            guild_id=self.id, reason=reason, **payload
        )
        event = ScheduledEvent(
            state=self._state, guild=self, creator=self.me, data=data
        )
        self._add_scheduled_event(event)
        return event

    @property
    def scheduled_events(self) -> list[ScheduledEvent]:
        """A list of scheduled events in this guild."""
        return list(self._scheduled_events.values())

    async def fetch_auto_moderation_rules(self) -> list[AutoModRule]:
        """|coro|

        Retrieves a list of auto moderation rules for this guild.

        Returns
        -------
        List[:class:`AutoModRule`]
            The auto moderation rules for this guild.

        Raises
        ------
        HTTPException
            Getting the auto moderation rules failed.
        Forbidden
            You do not have the Manage Guild permission.
        """
        data = await self._state.http.get_auto_moderation_rules(self.id)
        return [AutoModRule(state=self._state, data=rule) for rule in data]

    async def fetch_auto_moderation_rule(self, id: int) -> AutoModRule:
        """|coro|

        Retrieves a :class:`AutoModRule` from rule ID.

        Returns
        -------
        :class:`AutoModRule`
            The requested auto moderation rule.

        Raises
        ------
        HTTPException
            Getting the auto moderation rule failed.
        Forbidden
            You do not have the Manage Guild permission.
        """
        data = await self._state.http.get_auto_moderation_rule(self.id, id)
        return AutoModRule(state=self._state, data=data)

    async def create_auto_moderation_rule(
        self,
        *,
        name: str,
        event_type: AutoModEventType,
        trigger_type: AutoModTriggerType,
        trigger_metadata: AutoModTriggerMetadata,
        actions: list[AutoModAction],
        enabled: bool = False,
        exempt_roles: list[Snowflake] = None,
        exempt_channels: list[Snowflake] = None,
        reason: str | None = None,
    ) -> AutoModRule:
        """
        Creates an auto moderation rule.

        Parameters
        ----------
        name: :class:`str`
            The name of the auto moderation rule.
        event_type: :class:`AutoModEventType`
            The type of event that triggers the rule.
        trigger_type: :class:`AutoModTriggerType`
            The rule's trigger type.
        trigger_metadata: :class:`AutoModTriggerMetadata`
            The rule's trigger metadata.
        actions: List[:class:`AutoModAction`]
            The actions to take when the rule is triggered.
        enabled: :class:`bool`
            Whether the rule is enabled.
        exempt_roles: List[:class:`.abc.Snowflake`]
            A list of roles that are exempt from the rule.
        exempt_channels: List[:class:`.abc.Snowflake`]
            A list of channels that are exempt from the rule.
        reason: Optional[:class:`str`]
            The reason for creating the rule. Shows up in the audit log.

        Returns
        -------
        :class:`AutoModRule`
            The new auto moderation rule.

        Raises
        ------
        HTTPException
            Creating the auto moderation rule failed.
        Forbidden
            You do not have the Manage Guild permission.
        """
        payload = {
            "name": name,
            "event_type": event_type.value,
            "trigger_type": trigger_type.value,
            "trigger_metadata": trigger_metadata.to_dict(),
            "actions": [a.to_dict() for a in actions],
            "enabled": enabled,
        }

        if exempt_roles:
            payload["exempt_roles"] = [r.id for r in exempt_roles]

        if exempt_channels:
            payload["exempt_channels"] = [c.id for c in exempt_channels]

        data = await self._state.http.create_auto_moderation_rule(
            self.id, payload, reason=reason
        )
        return AutoModRule(state=self._state, data=data)

    async def onboarding(self):
        """|coro|

        Returns the :class:`Onboarding` flow for the guild.

        .. versionadded:: 2.5

        Returns
        -------
        :class:`Onboarding`
            The onboarding flow for the guild.

        Raises
        ------
        HTTPException
            Retrieving the onboarding flow failed somehow.
        """
        data = await self._state.http.get_onboarding(self.id)
        return Onboarding(data=data, guild=self)

    async def edit_onboarding(
        self,
        *,
        prompts: list[OnboardingPrompt] | None = MISSING,
        default_channels: list[Snowflake] | None = MISSING,
        enabled: bool | None = MISSING,
        mode: OnboardingMode | None = MISSING,
        reason: str | None = MISSING,
    ) -> Onboarding:
        """|coro|

        A shorthand for :attr:`Onboarding.edit` without fetching the onboarding flow.

        You must have the :attr:`~Permissions.manage_guild` and :attr:`~Permissions.manage_roles` permissions in the
        guild to do this.

        Parameters
        ----------

        prompts: Optional[List[:class:`OnboardingPrompt`]]
            The new list of prompts for this flow.
        default_channels: Optional[List[:class:`Snowflake`]]
            The new default channels that users are opted into.
        enabled: Optional[:class:`bool`]
            Whether onboarding should be enabled. Setting this to ``True`` requires
            the guild to have ``COMMUNITY`` in :attr:`~Guild.features` and at
            least 7 ``default_channels``.
        mode: Optional[:class:`OnboardingMode`]
            The new onboarding mode.
        reason: Optional[:class:`str`]
            The reason that shows up on Audit log.

        Returns
        -------
        :class:`Onboarding`
            The updated onboarding flow.

        Raises
        ------

        HTTPException
            Editing the onboarding flow failed somehow.
        Forbidden
            You don't have permissions to edit the onboarding flow.
        """

        fields: dict[str, Any] = {}
        if prompts is not MISSING:
            fields["prompts"] = [prompt.to_dict() for prompt in prompts]

        if default_channels is not MISSING:
            fields["default_channel_ids"] = [channel.id for channel in default_channels]

        if enabled is not MISSING:
            fields["enabled"] = enabled

        if mode is not MISSING:
            fields["mode"] = mode.value

        new = await self._state.http.edit_onboarding(self.id, fields, reason=reason)
        return Onboarding(data=new, guild=self)

    async def delete_auto_moderation_rule(
        self,
        id: int,
        *,
        reason: str | None = None,
    ) -> None:
        """
        Deletes an auto moderation rule.

        Parameters
        ----------
        id: :class:`int`
            The ID of the auto moderation rule.
        reason: Optional[:class:`str`]
            The reason for deleting the rule. Shows up in the audit log.

        Raises
        ------
        HTTPException
            Deleting the auto moderation rule failed.
        Forbidden
            You do not have the Manage Guild permission.
        """

        await self._state.http.delete_auto_moderation_rule(self.id, id, reason=reason)

    async def create_test_entitlement(self, sku: Snowflake) -> Entitlement:
        """|coro|

        Creates a test entitlement for the guild.

        Parameters
        ----------
        sku: :class:`Snowflake`
            The SKU to create a test entitlement for.

        Returns
        -------
        :class:`Entitlement`
            The created entitlement.
        """
        payload = {
            "sku_id": sku.id,
            "owner_id": self.id,
            "owner_type": EntitlementOwnerType.guild.value,
        }
        data = await self._state.http.create_test_entitlement(
            self._state.application_id, payload
        )
        return Entitlement(data=data, state=self._state)

    def entitlements(
        self,
        skus: list[Snowflake] | None = None,
        before: SnowflakeTime | None = None,
        after: SnowflakeTime | None = None,
        limit: int | None = 100,
        exclude_ended: bool = False,
    ) -> EntitlementIterator:
        """Returns an :class:`.AsyncIterator` that enables fetching the guild's entitlements.

        This is identical to :meth:`Client.entitlements` with the ``guild`` parameter.

        .. versionadded:: 2.6

        Parameters
        ----------
        skus: list[:class:`.abc.Snowflake`] | None
            Limit the fetched entitlements to entitlements that are for these SKUs.
        before: :class:`.abc.Snowflake` | :class:`datetime.datetime` | None
            Retrieves guilds before this date or object.
            If a datetime is provided, it is recommended to use a UTC-aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: :class:`.abc.Snowflake` | :class:`datetime.datetime` | None
            Retrieve guilds after this date or object.
            If a datetime is provided, it is recommended to use a UTC-aware datetime.
            If the datetime is naive, it is assumed to be local time.
        limit: Optional[:class:`int`]
            The number of entitlements to retrieve.
            If ``None``, retrieves every entitlement, which may be slow.
            Defaults to ``100``.
        exclude_ended: :class:`bool`
            Whether to limit the fetched entitlements to those that have not ended.
            Defaults to ``False``.

        Yields
        ------
        :class:`.Entitlement`
            The application's entitlements.

        Raises
        ------
        :exc:`HTTPException`
            Retrieving the entitlements failed.
        """
        return EntitlementIterator(
            self._state,
            sku_ids=[sku.id for sku in skus] if skus else None,
            before=before,
            after=after,
            limit=limit,
            guild_id=self.id,
            exclude_ended=exclude_ended,
        )
