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

import datetime
import io
import re
from os import PathLike
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Sequence,
    TypeVar,
    Union,
    overload,
)
from urllib.parse import parse_qs, urlparse

from . import utils
from .channel import PartialMessageable
from .components import _component_factory
from .embeds import Embed
from .emoji import AppEmoji, GuildEmoji
from .enums import ChannelType, MessageReferenceType, MessageType, try_enum
from .errors import InvalidArgument
from .file import File
from .flags import AttachmentFlags, MessageFlags
from .guild import Guild
from .member import Member
from .mixins import Hashable
from .object import Object
from .partial_emoji import PartialEmoji
from .poll import Poll
from .reaction import Reaction
from .sticker import StickerItem
from .threads import Thread
from .utils import MISSING, escape_mentions

if TYPE_CHECKING:
    from .abc import (
        GuildChannel,
        MessageableChannel,
        PartialMessageableChannel,
        Snowflake,
    )
    from .channel import TextChannel
    from .components import Component
    from .interactions import MessageInteraction
    from .mentions import AllowedMentions
    from .role import Role
    from .state import ConnectionState
    from .types.components import Component as ComponentPayload
    from .types.embed import Embed as EmbedPayload
    from .types.member import Member as MemberPayload
    from .types.member import UserWithMember as UserWithMemberPayload
    from .types.message import Attachment as AttachmentPayload
    from .types.message import ForwardedMessage as ForwardedMessagePayload
    from .types.message import Message as MessagePayload
    from .types.message import MessageActivity as MessageActivityPayload
    from .types.message import MessageApplication as MessageApplicationPayload
    from .types.message import MessageCall as MessageCallPayload
    from .types.message import MessageReference as MessageReferencePayload
    from .types.message import MessageSnapshot as MessageSnapshotPayload
    from .types.message import Reaction as ReactionPayload
    from .types.poll import Poll as PollPayload
    from .types.snowflake import SnowflakeList
    from .types.threads import ThreadArchiveDuration
    from .types.user import User as UserPayload
    from .ui.view import View
    from .user import User

    MR = TypeVar("MR", bound="MessageReference")
    EmojiInputType = Union[GuildEmoji, AppEmoji, PartialEmoji, str]

__all__ = (
    "Attachment",
    "Message",
    "PartialMessage",
    "MessageReference",
    "MessageCall",
    "DeletedReferencedMessage",
    "ForwardedMessage",
)


def convert_emoji_reaction(emoji):
    if isinstance(emoji, Reaction):
        emoji = emoji.emoji

    if isinstance(emoji, (GuildEmoji, AppEmoji)):
        return f"{emoji.name}:{emoji.id}"
    if isinstance(emoji, PartialEmoji):
        return emoji._as_reaction()
    if isinstance(emoji, str):
        # Reactions can be in :name:id format, but not <:name:id>.
        # No existing emojis have <> in them, so this should be okay.
        return emoji.strip("<>")

    raise InvalidArgument(
        "emoji argument must be str, GuildEmoji, AppEmoji, or Reaction not"
        f" {emoji.__class__.__name__}."
    )


class Attachment(Hashable):
    """Represents an attachment from Discord.

    .. container:: operations

        .. describe:: str(x)

            Returns the URL of the attachment.

        .. describe:: x == y

            Checks if the attachment is equal to another attachment.

        .. describe:: x != y

            Checks if the attachment is not equal to another attachment.

        .. describe:: hash(x)

            Returns the attachment's unique identifier.

            This is equivalent to :attr:`id`.

    .. versionchanged:: 1.7
        Attachment can now be cast to :class:`str` and is hashable.

    Attributes
    ----------
    id: :class:`int`
        The attachment ID.
    size: :class:`int`
        The attachment size in bytes.
    height: Optional[:class:`int`]
        The attachment's height, in pixels. Only applicable to images and videos.
    width: Optional[:class:`int`]
        The attachment's width, in pixels. Only applicable to images and videos.
    filename: :class:`str`
        The attachment's filename.
    title: Optional[:class:`str`]
        The attachment's title. This is equal to the original :attr:`filename` (without an extension)
        if special characters were filtered from it.

        .. versionadded:: 2.6
    url: :class:`str`
        The attachment URL. If the message this attachment was attached
        to is deleted, then this will 404.
    proxy_url: :class:`str`
        The proxy URL. This is a cached version of the :attr:`~Attachment.url` in the
        case of images. When the message is deleted, this URL might be valid for a few
        minutes or not valid at all.
    content_type: Optional[:class:`str`]
        The attachment's `media type <https://en.wikipedia.org/wiki/Media_type>`_.
    ephemeral: :class:`bool`
        Whether the attachment is ephemeral or not.

        .. versionadded:: 1.7

    description: Optional[:class:`str`]
        The attachment's description.

        .. versionadded:: 2.0

    duration_secs: Optional[:class:`float`]
        The duration of the audio file (currently for voice messages).

        .. versionadded:: 2.5

    waveform: Optional[:class:`str`]
        The base64 encoded bytearray representing a sampled waveform (currently for voice messages).

        .. versionadded:: 2.5

    flags: :class:`AttachmentFlags`
        Extra attributes of the attachment.

        .. versionadded:: 2.5

    hm: :class:`str`
        The unique signature of this attachment's instance.

        .. versionadded:: 2.5
    """

    __slots__ = (
        "id",
        "size",
        "height",
        "width",
        "filename",
        "url",
        "proxy_url",
        "_http",
        "content_type",
        "ephemeral",
        "description",
        "duration_secs",
        "waveform",
        "flags",
        "_ex",
        "_is",
        "hm",
        "title",
    )

    def __init__(self, *, data: AttachmentPayload, state: ConnectionState):
        self.id: int = int(data["id"])
        self.size: int = data["size"]
        self.height: int | None = data.get("height")
        self.width: int | None = data.get("width")
        self.filename: str = data["filename"]
        self.title: str | None = data.get("title")
        self.url: str = data.get("url")
        self.proxy_url: str = data.get("proxy_url")
        self._http = state.http
        self.content_type: str | None = data.get("content_type")
        self.ephemeral: bool = data.get("ephemeral", False)
        self.description: str | None = data.get("description")
        self.duration_secs: float | None = data.get("duration_secs")
        self.waveform: str | None = data.get("waveform")
        self.flags: AttachmentFlags = AttachmentFlags._from_value(data.get("flags", 0))
        self._ex: str | None = None
        self._is: str | None = None
        self.hm: str | None = None

        query = urlparse(self.url).query
        extras = ["_ex", "_is", "hm"]
        if query_params := parse_qs(query):
            for attr in extras:
                value = "".join(query_params.get(attr.replace("_", ""), []))
                if value:
                    setattr(self, attr, value)

    @property
    def expires_at(self) -> datetime.datetime | None:
        """This attachment URL's expiry time in UTC."""
        if not self._ex:
            return None
        return datetime.datetime.utcfromtimestamp(int(self._ex, 16))

    @property
    def issued_at(self) -> datetime.datetime | None:
        """The attachment URL's issue time in UTC."""
        if not self._is:
            return None
        return datetime.datetime.utcfromtimestamp(int(self._is, 16))

    def is_spoiler(self) -> bool:
        """Whether this attachment contains a spoiler."""
        return self.filename.startswith("SPOILER_")

    def __repr__(self) -> str:
        return f"<Attachment id={self.id} filename={self.filename!r} url={self.url!r}>"

    def __str__(self) -> str:
        return self.url or ""

    async def save(
        self,
        fp: io.BufferedIOBase | PathLike,
        *,
        seek_begin: bool = True,
        use_cached: bool = False,
    ) -> int:
        """|coro|

        Saves this attachment into a file-like object.

        Parameters
        ----------
        fp: Union[:class:`io.BufferedIOBase`, :class:`os.PathLike`]
            The file-like object to save this attachment to or the filename
            to use. If a filename is passed then a file is created with that
            filename and used instead.
        seek_begin: :class:`bool`
            Whether to seek to the beginning of the file after saving is
            successfully done.
        use_cached: :class:`bool`
            Whether to use :attr:`proxy_url` rather than :attr:`url` when downloading
            the attachment. This will allow attachments to be saved after deletion
            more often, compared to the regular URL which is generally deleted right
            after the message is deleted. Note that this can still fail to download
            deleted attachments if too much time has passed, and it does not work
            on some types of attachments.

        Returns
        -------
        :class:`int`
            The number of bytes written.

        Raises
        ------
        HTTPException
            Saving the attachment failed.
        NotFound
            The attachment was deleted.
        """
        data = await self.read(use_cached=use_cached)
        if isinstance(fp, io.BufferedIOBase):
            written = fp.write(data)
            if seek_begin:
                fp.seek(0)
            return written
        else:
            with open(fp, "wb") as f:
                return f.write(data)

    async def read(self, *, use_cached: bool = False) -> bytes:
        """|coro|

        Retrieves the content of this attachment as a :class:`bytes` object.

        .. versionadded:: 1.1

        Parameters
        ----------
        use_cached: :class:`bool`
            Whether to use :attr:`proxy_url` rather than :attr:`url` when downloading
            the attachment. This will allow attachments to be saved after deletion
            more often, compared to the regular URL which is generally deleted right
            after the message is deleted. Note that this can still fail to download
            deleted attachments if too much time has passed, and it does not work
            on some types of attachments.

        Returns
        -------
        :class:`bytes`
            The contents of the attachment.

        Raises
        ------
        HTTPException
            Downloading the attachment failed.
        Forbidden
            You do not have permissions to access this attachment
        NotFound
            The attachment was deleted.
        """
        url = self.proxy_url if use_cached else self.url
        data = await self._http.get_from_cdn(url)
        return data

    async def to_file(self, *, use_cached: bool = False, spoiler: bool = False) -> File:
        """|coro|

        Converts the attachment into a :class:`File` suitable for sending via
        :meth:`abc.Messageable.send`.

        .. versionadded:: 1.3

        Parameters
        ----------
        use_cached: :class:`bool`
            Whether to use :attr:`proxy_url` rather than :attr:`url` when downloading
            the attachment. This will allow attachments to be saved after deletion
            more often, compared to the regular URL which is generally deleted right
            after the message is deleted. Note that this can still fail to download
            deleted attachments if too much time has passed, and it does not work
            on some types of attachments.

            .. versionadded:: 1.4
        spoiler: :class:`bool`
            Whether the file is a spoiler.

            .. versionadded:: 1.4

        Returns
        -------
        :class:`File`
            The attachment as a file suitable for sending.

        Raises
        ------
        HTTPException
            Downloading the attachment failed.
        Forbidden
            You do not have permissions to access this attachment
        NotFound
            The attachment was deleted.
        """

        data = await self.read(use_cached=use_cached)
        return File(
            io.BytesIO(data),
            filename=self.filename,
            spoiler=spoiler,
            description=self.description,
        )

    def to_dict(self) -> AttachmentPayload:
        result: AttachmentPayload = {
            "filename": self.filename,
            "id": self.id,
            "proxy_url": self.proxy_url,
            "size": self.size,
            "url": self.url,
            "spoiler": self.is_spoiler(),
        }
        if self.height:
            result["height"] = self.height
        if self.width:
            result["width"] = self.width
        if self.content_type:
            result["content_type"] = self.content_type
        if self.description:
            result["description"] = self.description
        return result


class DeletedReferencedMessage:
    """A special sentinel type that denotes whether the
    resolved message referenced message had since been deleted.

    The purpose of this class is to separate referenced messages that could not be
    fetched and those that were previously fetched but have since been deleted.

    .. versionadded:: 1.6
    """

    __slots__ = ("_parent",)

    def __init__(self, parent: MessageReference):
        self._parent: MessageReference = parent

    def __repr__(self) -> str:
        return (
            "<DeletedReferencedMessage"
            f" id={self.id} channel_id={self.channel_id} guild_id={self.guild_id!r}>"
        )

    @property
    def id(self) -> int:
        """The message ID of the deleted referenced message."""
        # the parent's message id won't be None here
        return self._parent.message_id  # type: ignore

    @property
    def channel_id(self) -> int:
        """The channel ID of the deleted referenced message."""
        return self._parent.channel_id

    @property
    def guild_id(self) -> int | None:
        """The guild ID of the deleted referenced message."""
        return self._parent.guild_id


class MessageReference:
    """Represents a reference to a :class:`~discord.Message`.

    .. versionadded:: 1.5

    .. versionchanged:: 1.6
        This class can now be constructed by users.

    Attributes
    ----------
    type: Optional[:class:`~discord.MessageReferenceType`]
        The type of message reference. If this is not provided, assume the default behavior (i.e., reply).

        .. versionadded:: 2.7

    message_id: Optional[:class:`int`]
        The id of the message referenced.
    channel_id: :class:`int`
        The channel id of the message referenced.
    guild_id: Optional[:class:`int`]
        The guild id of the message referenced.
    fail_if_not_exists: :class:`bool`
        Whether replying to the referenced message should raise :class:`HTTPException`
        if the message no longer exists or Discord could not fetch the message.

        .. versionadded:: 1.7

    resolved: Optional[Union[:class:`Message`, :class:`DeletedReferencedMessage`]]
        The message that this reference resolved to. If this is ``None``
        then the original message was not fetched either due to the Discord API
        not attempting to resolve it or it not being available at the time of creation.
        If the message was resolved at a prior point but has since been deleted then
        this will be of type :class:`DeletedReferencedMessage`.

        Currently, this is mainly the replied to message when a user replies to a message.

        .. versionadded:: 1.6
    """

    __slots__ = (
        "message_id",
        "channel_id",
        "guild_id",
        "fail_if_not_exists",
        "resolved",
        "type",
        "_state",
    )

    def __init__(
        self,
        *,
        message_id: int,
        channel_id: int,
        guild_id: int | None = None,
        fail_if_not_exists: bool = True,
        type: MessageReferenceType = MessageReferenceType.default,
    ):
        self._state: ConnectionState | None = None
        self.resolved: Message | DeletedReferencedMessage | None = None
        self.type: MessageReferenceType = type
        self.message_id: int | None = message_id
        self.channel_id: int = channel_id
        self.guild_id: int | None = guild_id
        self.fail_if_not_exists: bool = fail_if_not_exists

    @classmethod
    def with_state(
        cls: type[MR], state: ConnectionState, data: MessageReferencePayload
    ) -> MR:
        self = cls.__new__(cls)
        self.type = (
            try_enum(MessageReferenceType, data.get("type"))
            or MessageReferenceType.default
        )
        self.message_id = utils._get_as_snowflake(data, "message_id")
        self.channel_id = utils._get_as_snowflake(data, "channel_id")
        self.guild_id = utils._get_as_snowflake(data, "guild_id")
        self.fail_if_not_exists = data.get("fail_if_not_exists", True)
        self._state = state
        self.resolved = None
        return self

    @classmethod
    def from_message(
        cls: type[MR],
        message: Message,
        *,
        fail_if_not_exists: bool = True,
        type: MessageReferenceType = MessageReferenceType.default,
    ) -> MR:
        """Creates a :class:`MessageReference` from an existing :class:`~discord.Message`.

        .. versionadded:: 1.6

        Parameters
        ----------
        message: :class:`~discord.Message`
            The message to be converted into a reference.
        fail_if_not_exists: :class:`bool`
            Whether replying to the referenced message should raise :class:`HTTPException`
            if the message no longer exists or Discord could not fetch the message.

            .. versionadded:: 1.7

        type: Optional[:class:`~discord.MessageReferenceType`]
            The type of reference to create. Defaults to :attr:`MessageReferenceType.default` (reply).

            .. versionadded:: 2.7

        Returns
        -------
        :class:`MessageReference`
            A reference to the message.
        """
        self = cls(
            message_id=message.id,
            channel_id=message.channel.id,
            guild_id=getattr(message.guild, "id", None),
            fail_if_not_exists=fail_if_not_exists,
            type=type,
        )
        self._state = message._state
        return self

    @property
    def cached_message(self) -> Message | None:
        """The cached message, if found in the internal message cache."""
        return self._state and self._state._get_message(self.message_id)

    @property
    def jump_url(self) -> str:
        """Returns a URL that allows the client to jump to the referenced message.

        .. versionadded:: 1.7
        """
        guild_id = self.guild_id if self.guild_id is not None else "@me"
        return f"https://discord.com/channels/{guild_id}/{self.channel_id}/{self.message_id}"

    def __repr__(self) -> str:
        return (
            f"<MessageReference message_id={self.message_id!r}"
            f" channel_id={self.channel_id!r} guild_id={self.guild_id!r}"
            f" type={self.type!r}>"
        )

    def to_dict(self) -> MessageReferencePayload:
        result: MessageReferencePayload = (
            {"message_id": self.message_id} if self.message_id is not None else {}
        )
        result["channel_id"] = self.channel_id
        result["type"] = self.type and self.type.value
        if self.guild_id is not None:
            result["guild_id"] = self.guild_id
        if self.fail_if_not_exists is not None:
            result["fail_if_not_exists"] = self.fail_if_not_exists
        return result

    to_message_reference_dict = to_dict


class MessageCall:
    """Represents information about a call in a private channel.

    .. versionadded:: 2.6
    """

    def __init__(self, state: ConnectionState, data: MessageCallPayload):
        self._state: ConnectionState = state
        self._participants: SnowflakeList = data.get("participants", [])
        self._ended_timestamp: datetime.datetime | None = utils.parse_time(
            data["ended_timestamp"]
        )

    @property
    def participants(self) -> list[User | Object]:
        """A list of :class:`User` that participated in this call.

        If a user is not found in the client's cache,
        then it will be returned as an :class:`Object`.
        """
        return [self._state.get_user(int(i)) or Object(i) for i in self._participants]

    @property
    def ended_at(self) -> datetime.datetime | None:
        """An aware timestamp of when the call ended."""
        return self._ended_timestamp


class ForwardedMessage:
    """Represents the snapshotted contents from a forwarded message. Forwarded messages are immutable; any updates to the original message will not be reflected.

    .. versionadded:: 2.7

    Attributes
    ----------
    type: :class:`MessageType`
        The type of the original message. In most cases this should not be checked, but it is helpful
        in cases where it might be a system message for :attr:`system_content`.
    original_message: Optional[Union[:class:`Message`, :class:`PartialMessage`]]
        The original message that was forwarded, if available.
    channel: Union[:class:`TextChannel`, :class:`Thread`, :class:`DMChannel`, :class:`GroupChannel`, :class:`PartialMessageable`]
        The :class:`TextChannel` or :class:`Thread` that the original message was sent from.
    guild: Optional[Union[:class:`Guild`, :class:`Object`]]
        The guild that the original message belonged to, if applicable.
    content: :class:`str`
        The contents of the original message.
    embeds: List[:class:`Embed`]
        A list of embeds the original message had.
    attachments: List[:class:`Attachment`]
        A list of attachments given to the original message.
    flags: :class:`MessageFlags`
        Extra features of the original message.
    mentions: List[Union[:class:`abc.User`, :class:`Object`]]
        A list of :class:`Member` that were originally mentioned.
    role_mentions: List[Union[:class:`Role`, :class:`Object`]]
        A list of :class:`Role` that were originally mentioned.
    stickers: List[:class:`StickerItem`]
        A list of sticker items given to the original message.
    components: List[:class:`Component`]
        A list of components in the original message.
    """

    def __init__(
        self,
        *,
        state: ConnectionState,
        reference: MessageReference,
        data: ForwardedMessagePayload,
    ):
        self._state: ConnectionState = state
        self._reference = reference
        self.id: int = reference.message_id
        self.channel = state.get_channel(reference.channel_id) or (
            reference.channel_id
            and PartialMessageable(
                state=state,
                id=reference.channel_id,
            )
        )
        self.guild = state._get_guild(reference.guild_id) or (
            reference.guild_id and Object(reference.guild_id)
        )
        self.original_message = state._get_message(self.id) or (
            self.id and self.channel.get_partial_message(self.id)
        )
        self.content: str = data["content"]
        self.embeds: list[Embed] = [Embed.from_dict(a) for a in data["embeds"]]
        self.attachments: list[Attachment] = [
            Attachment(data=a, state=state) for a in data["attachments"]
        ]
        self.flags: MessageFlags = MessageFlags._from_value(data.get("flags", 0))
        self.stickers: list[StickerItem] = [
            StickerItem(data=d, state=state) for d in data.get("sticker_items", [])
        ]
        self.components: list[Component] = [
            _component_factory(d) for d in data.get("components", [])
        ]
        self._edited_timestamp: datetime.datetime | None = utils.parse_time(
            data["edited_timestamp"]
        )

    @property
    def created_at(self) -> datetime.datetime:
        """The original message's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def edited_at(self) -> datetime.datetime | None:
        """An aware UTC datetime object containing the
        edited time of the original message.
        """
        return self._edited_timestamp

    def __repr__(self) -> str:
        return f"<ForwardedMessage reference={self._reference!r}>"


class MessageSnapshot:
    """Represents a message snapshot.

    .. versionadded:: 2.7

    Attributes
    ----------
    message: :class:`ForwardedMessage`
        The forwarded message, which includes a minimal subset of fields from the original message.
    """

    def __init__(
        self,
        *,
        state: ConnectionState,
        reference: MessageReference,
        data: MessageSnapshotPayload,
    ):
        self._state: ConnectionState = state
        self.message: ForwardedMessage | None
        if fm := data.get("message"):
            self.message = ForwardedMessage(state=state, reference=reference, data=fm)

    def __repr__(self) -> str:
        return f"<MessageSnapshot message={self.message!r}>"


def flatten_handlers(cls):
    prefix = len("_handle_")
    handlers = [
        (key[prefix:], value)
        for key, value in cls.__dict__.items()
        if key.startswith("_handle_") and key != "_handle_member"
    ]

    # store _handle_member last
    handlers.append(("member", cls._handle_member))
    cls._HANDLERS = handlers
    cls._CACHED_SLOTS = [attr for attr in cls.__slots__ if attr.startswith("_cs_")]
    return cls


@flatten_handlers
class Message(Hashable):
    r"""Represents a message from Discord.

    .. container:: operations

        .. describe:: x == y

            Checks if two messages are equal.

        .. describe:: x != y

            Checks if two messages are not equal.

        .. describe:: hash(x)

            Returns the message's hash.

    Attributes
    -----------
    tts: :class:`bool`
        Specifies if the message was done with text-to-speech.
        This can only be accurately received in :func:`on_message` due to
        a discord limitation.
    type: :class:`MessageType`
        The type of message. In most cases this should not be checked, but it is helpful
        in cases where it might be a system message for :attr:`system_content`.
    author: Union[:class:`Member`, :class:`abc.User`]
        A :class:`Member` that sent the message. If :attr:`channel` is a
        private channel or the user has the left the guild, then it is a :class:`User` instead.
    content: :class:`str`
        The actual contents of the message.
    nonce: Optional[Union[:class:`str`, :class:`int`]]
        The value used by the discord guild and the client to verify that the message is successfully sent.
        This is not stored long term within Discord's servers and is only used ephemerally.
    embeds: List[:class:`Embed`]
        A list of embeds the message has.
    channel: Union[:class:`TextChannel`, :class:`Thread`, :class:`DMChannel`, :class:`GroupChannel`, :class:`PartialMessageable`]
        The :class:`TextChannel` or :class:`Thread` that the message was sent from.
        Could be a :class:`DMChannel` or :class:`GroupChannel` if it's a private message.
    reference: Optional[:class:`~discord.MessageReference`]
        The message that this message references. This is only applicable to messages of
        type :attr:`MessageType.pins_add`, crossposted messages created by a
        followed channel integration, or message replies.

        .. versionadded:: 1.5

    mention_everyone: :class:`bool`
        Specifies if the message mentions everyone.

        .. note::

            This does not check if the ``@everyone`` or the ``@here`` text is in the message itself.
            Rather this boolean indicates if either the ``@everyone`` or the ``@here`` text is in the message
            **and** it did end up mentioning.
    mentions: List[:class:`abc.User`]
        A list of :class:`Member` that were mentioned. If the message is in a private message
        then the list will be of :class:`User` instead. For messages that are not of type
        :attr:`MessageType.default`\, this array can be used to aid in system messages.
        For more information, see :attr:`system_content`.

        .. warning::

            The order of the mentions list is not in any particular order, so you should
            not rely on it. This is a Discord limitation, not one with the library.
    channel_mentions: List[:class:`abc.GuildChannel`]
        A list of :class:`abc.GuildChannel` that were mentioned. If the message is in a private message
        then the list is always empty.
    role_mentions: List[:class:`Role`]
        A list of :class:`Role` that were mentioned. If the message is in a private message
        then the list is always empty.
    id: :class:`int`
        The message ID.
    webhook_id: Optional[:class:`int`]
        If this message was sent by a webhook, then this is the webhook ID's that sent this
        message.
    attachments: List[:class:`Attachment`]
        A list of attachments given to a message.
    pinned: :class:`bool`
        Specifies if the message is currently pinned.
    flags: :class:`MessageFlags`
        Extra features of the message.

        .. versionadded:: 1.3

    reactions : List[:class:`Reaction`]
        Reactions to a message. Reactions can be either custom emoji or standard unicode emoji.
    activity: Optional[:class:`dict`]
        The activity associated with this message. Sent with Rich-Presence related messages that for
        example, request joining, spectating, or listening to or with another member.

        It is a dictionary with the following optional keys:

        - ``type``: An integer denoting the type of message activity being requested.
        - ``party_id``: The party ID associated with the party.
    application: Optional[:class:`dict`]
        The rich presence enabled application associated with this message.

        It is a dictionary with the following keys:

        - ``id``: A string representing the application's ID.
        - ``name``: A string representing the application's name.
        - ``description``: A string representing the application's description.
        - ``icon``: A string representing the icon ID of the application.
        - ``cover_image``: A string representing the embed's image asset ID.
    stickers: List[:class:`StickerItem`]
        A list of sticker items given to the message.

        .. versionadded:: 1.6
    components: List[:class:`Component`]
        A list of components in the message.

        .. versionadded:: 2.0
    guild: Optional[:class:`Guild`]
        The guild that the message belongs to, if applicable.
    interaction: Optional[:class:`MessageInteraction`]
        The interaction associated with the message, if applicable.

        .. deprecated:: 2.6

            Use :attr:`interaction_metadata` instead.
    interaction_metadata: Optional[:class:`InteractionMetadata`]
        The interaction metadata associated with the message, if applicable.

        .. versionadded:: 2.6
    thread: Optional[:class:`Thread`]
        The thread created from this message, if applicable.

        .. versionadded:: 2.0
    poll: Optional[:class:`Poll`]
        The poll associated with this message, if applicable.

        .. versionadded:: 2.6
    call: Optional[:class:`MessageCall`]
        The call information associated with this message, if applicable.

        .. versionadded:: 2.6
    snapshots: Optional[List[:class:`MessageSnapshots`]]
        The snapshots attached to this message, if applicable.

        .. versionadded:: 2.7
    """

    __slots__ = (
        "_state",
        "_raw_data",
        "_edited_timestamp",
        "_cs_channel_mentions",
        "_cs_raw_mentions",
        "_cs_clean_content",
        "_cs_raw_channel_mentions",
        "_cs_raw_role_mentions",
        "_cs_system_content",
        "tts",
        "content",
        "channel",
        "webhook_id",
        "mention_everyone",
        "embeds",
        "id",
        "mentions",
        "author",
        "attachments",
        "nonce",
        "pinned",
        "role_mentions",
        "type",
        "flags",
        "reactions",
        "reference",
        "application",
        "activity",
        "stickers",
        "components",
        "guild",
        "_interaction",
        "interaction_metadata",
        "thread",
        "_poll",
        "call",
        "snapshots",
    )

    if TYPE_CHECKING:
        _HANDLERS: ClassVar[list[tuple[str, Callable[..., None]]]]
        _CACHED_SLOTS: ClassVar[list[str]]
        guild: Guild | None
        reference: MessageReference | None
        mentions: list[User | Member]
        author: User | Member
        role_mentions: list[Role]

    def __init__(
        self,
        *,
        state: ConnectionState,
        channel: MessageableChannel,
        data: MessagePayload,
    ):
        self._state: ConnectionState = state
        self._raw_data: MessagePayload = data
        self.id: int = int(data["id"])
        self.webhook_id: int | None = utils._get_as_snowflake(data, "webhook_id")
        self.reactions: list[Reaction] = [
            Reaction(message=self, data=d) for d in data.get("reactions", [])
        ]
        self.attachments: list[Attachment] = [
            Attachment(data=a, state=self._state) for a in data["attachments"]
        ]
        self.embeds: list[Embed] = [Embed.from_dict(a) for a in data["embeds"]]
        self.application: MessageApplicationPayload | None = data.get("application")
        self.activity: MessageActivityPayload | None = data.get("activity")
        self.channel: MessageableChannel = channel
        self._edited_timestamp: datetime.datetime | None = utils.parse_time(
            data["edited_timestamp"]
        )
        self.type: MessageType = try_enum(MessageType, data["type"])
        self.pinned: bool = data["pinned"]
        self.flags: MessageFlags = MessageFlags._from_value(data.get("flags", 0))
        self.mention_everyone: bool = data["mention_everyone"]
        self.tts: bool = data["tts"]
        self.content: str = data["content"]
        self.nonce: int | str | None = data.get("nonce")
        self.stickers: list[StickerItem] = [
            StickerItem(data=d, state=state) for d in data.get("sticker_items", [])
        ]
        self.components: list[Component] = [
            _component_factory(d, state=state) for d in data.get("components", [])
        ]

        try:
            # if the channel doesn't have a guild attribute, we handle that
            self.guild = channel.guild  # type: ignore
        except AttributeError:
            self.guild = state._get_guild(utils._get_as_snowflake(data, "guild_id"))

        try:
            ref = data["message_reference"]
        except KeyError:
            self.reference = None
        else:
            self.reference = ref = MessageReference.with_state(state, ref)
            try:
                resolved = data["referenced_message"]
            except KeyError:
                pass
            else:
                if resolved is None:
                    ref.resolved = DeletedReferencedMessage(ref)
                else:
                    # Right now the channel IDs match but maybe in the future they won't.
                    if ref.channel_id == channel.id:
                        chan = channel
                    else:
                        chan, _ = state._get_guild_channel(
                            resolved, guild_id=self.guild.id
                        )

                    # the channel will be the correct type here
                    ref.resolved = self.__class__(channel=chan, data=resolved, state=state)  # type: ignore

        self.snapshots: list[MessageSnapshot]
        try:
            self.snapshots = [
                MessageSnapshot(
                    state=state,
                    reference=self.reference,
                    data=ms,
                )
                for ms in data["message_snapshots"]
            ]
        except KeyError:
            self.snapshots = []

        from .interactions import InteractionMetadata, MessageInteraction

        self._interaction: MessageInteraction | None
        try:
            self._interaction = MessageInteraction(
                data=data["interaction"], state=state
            )
        except KeyError:
            self._interaction = None
        try:
            self.interaction_metadata = InteractionMetadata(
                data=data["interaction_metadata"], state=state
            )
        except KeyError:
            self.interaction_metadata = None

        self._poll: Poll | None
        try:
            self._poll = Poll.from_dict(data["poll"], self)
            self._state.store_poll(self._poll, self.id)
        except KeyError:
            self._poll = None

        self.thread: Thread | None
        try:
            self.thread = Thread(
                guild=self.guild, state=self._state, data=data["thread"]
            )
        except KeyError:
            self.thread = None

        self.call: MessageCall | None
        try:
            self.call = MessageCall(state=self._state, data=data["call"])
        except KeyError:
            self.call = None

        for handler in ("author", "member", "mentions", "mention_roles"):
            try:
                getattr(self, f"_handle_{handler}")(data[handler])
            except KeyError:
                continue

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return (
            f"<{name} id={self.id} channel={self.channel!r} type={self.type!r}"
            f" author={self.author!r} flags={self.flags!r}>"
        )

    def _try_patch(self, data, key, transform=None) -> None:
        try:
            value = data[key]
        except KeyError:
            pass
        else:
            if transform is None:
                setattr(self, key, value)
            else:
                setattr(self, key, transform(value))

    def _add_reaction(self, data, emoji, user_id) -> Reaction:
        reaction = utils.find(lambda r: r.emoji == emoji, self.reactions)
        is_me = data["me"] = user_id == self._state.self_id

        if reaction is None:
            reaction = Reaction(message=self, data=data, emoji=emoji)
            self.reactions.append(reaction)
        else:
            reaction.count += 1
            if is_me:
                reaction.me = is_me

        return reaction

    def _remove_reaction(
        self, data: ReactionPayload, emoji: EmojiInputType, user_id: int
    ) -> Reaction:
        reaction = utils.find(lambda r: r.emoji == emoji, self.reactions)

        if reaction is None:
            # already removed?
            raise ValueError("Emoji already removed?")

        # if reaction isn't in the list, we crash. This means discord
        # sent bad data, or we stored improperly
        reaction.count -= 1

        if user_id == self._state.self_id:
            reaction.me = False
        if reaction.count == 0:
            # this raises ValueError if something went wrong as well.
            self.reactions.remove(reaction)

        return reaction

    def _clear_emoji(self, emoji) -> Reaction | None:
        to_check = str(emoji)
        for index, reaction in enumerate(self.reactions):
            if str(reaction.emoji) == to_check:
                break
        else:
            # didn't find anything so just return
            return

        del self.reactions[index]
        return reaction

    def _update(self, data):
        # In an update scheme, 'author' key has to be handled before 'member'
        # otherwise they overwrite each other which is undesirable.
        # Since there's no good way to do this we have to iterate over every
        # handler rather than iterating over the keys which is a little slower
        for key, handler in self._HANDLERS:
            try:
                value = data[key]
            except KeyError:
                continue
            else:
                handler(self, value)

        # clear the cached properties
        for attr in self._CACHED_SLOTS:
            try:
                delattr(self, attr)
            except AttributeError:
                pass

    def _handle_edited_timestamp(self, value: str) -> None:
        self._edited_timestamp = utils.parse_time(value)

    def _handle_pinned(self, value: bool) -> None:
        self.pinned = value

    def _handle_flags(self, value: int) -> None:
        self.flags = MessageFlags._from_value(value)

    def _handle_application(self, value: MessageApplicationPayload) -> None:
        self.application = value

    def _handle_activity(self, value: MessageActivityPayload) -> None:
        self.activity = value

    def _handle_mention_everyone(self, value: bool) -> None:
        self.mention_everyone = value

    def _handle_tts(self, value: bool) -> None:
        self.tts = value

    def _handle_type(self, value: int) -> None:
        self.type = try_enum(MessageType, value)

    def _handle_content(self, value: str) -> None:
        self.content = value

    def _handle_attachments(self, value: list[AttachmentPayload]) -> None:
        self.attachments = [Attachment(data=a, state=self._state) for a in value]

    def _handle_embeds(self, value: list[EmbedPayload]) -> None:
        self.embeds = [Embed.from_dict(data) for data in value]

    def _handle_nonce(self, value: str | int) -> None:
        self.nonce = value

    def _handle_poll(self, value: PollPayload) -> None:
        self._poll = Poll.from_dict(value, self)
        self._state.store_poll(self._poll, self.id)

    def _handle_author(self, author: UserPayload) -> None:
        self.author = self._state.store_user(author)
        if isinstance(self.guild, Guild):
            found = self.guild.get_member(self.author.id)
            if found is not None:
                self.author = found

    def _handle_member(self, member: MemberPayload) -> None:
        # The gateway now gives us full Member objects sometimes with the following keys
        # deaf, mute, joined_at, roles
        # For the sake of performance I'm going to assume that the only
        # field that needs *updating* would be the joined_at field.
        # If there is no Member object (for some strange reason), then we can upgrade
        # ourselves to a more "partial" member object.
        author = self.author
        try:
            # Update member reference
            author._update_from_message(member)  # type: ignore
        except AttributeError:
            # It's a user here
            # TODO: consider adding to cache here
            self.author = Member._from_message(message=self, data=member)

    def _handle_mentions(self, mentions: list[UserWithMemberPayload]) -> None:
        self.mentions = r = []
        guild = self.guild
        state = self._state
        if not isinstance(guild, Guild):
            self.mentions = [state.store_user(m) for m in mentions]
            return

        for mention in filter(None, mentions):
            id_search = int(mention["id"])
            member = guild.get_member(id_search)
            if member is not None:
                r.append(member)
            else:
                r.append(Member._try_upgrade(data=mention, guild=guild, state=state))

    def _handle_mention_roles(self, role_mentions: list[int]) -> None:
        self.role_mentions = []
        if isinstance(self.guild, Guild):
            for role_id in map(int, role_mentions):
                role = self.guild.get_role(role_id)
                if role is not None:
                    self.role_mentions.append(role)

    def _handle_components(self, components: list[ComponentPayload]):
        self.components = [_component_factory(d, state=self._state) for d in components]

    def _rebind_cached_references(
        self, new_guild: Guild, new_channel: TextChannel | Thread
    ) -> None:
        self.guild = new_guild
        self.channel = new_channel

    @property
    def interaction(self) -> MessageInteraction | None:
        utils.warn_deprecated(
            "interaction",
            "interaction_metadata",
            "2.6",
            reference="https://discord.com/developers/docs/change-log#userinstallable-apps-preview",
        )
        return self._interaction

    @interaction.setter
    def interaction(self, value: MessageInteraction | None) -> None:
        utils.warn_deprecated(
            "interaction",
            "interaction_metadata",
            "2.6",
            reference="https://discord.com/developers/docs/change-log#userinstallable-apps-preview",
        )
        self._interaction = value

    @utils.cached_slot_property("_cs_raw_mentions")
    def raw_mentions(self) -> list[int]:
        """A property that returns an array of user IDs matched with
        the syntax of ``<@user_id>`` in the message content.

        This allows you to receive the user IDs of mentioned users
        even in a private message context.
        """
        return [int(x) for x in re.findall(r"<@!?([0-9]{15,20})>", self.content)]

    @utils.cached_slot_property("_cs_raw_channel_mentions")
    def raw_channel_mentions(self) -> list[int]:
        """A property that returns an array of channel IDs matched with
        the syntax of ``<#channel_id>`` in the message content.
        """
        return [int(x) for x in re.findall(r"<#([0-9]{15,20})>", self.content)]

    @utils.cached_slot_property("_cs_raw_role_mentions")
    def raw_role_mentions(self) -> list[int]:
        """A property that returns an array of role IDs matched with
        the syntax of ``<@&role_id>`` in the message content.
        """
        return [int(x) for x in re.findall(r"<@&([0-9]{15,20})>", self.content)]

    @utils.cached_slot_property("_cs_channel_mentions")
    def channel_mentions(self) -> list[GuildChannel]:
        if self.guild is None:
            return []
        it = filter(None, map(self.guild.get_channel, self.raw_channel_mentions))
        return utils._unique(it)

    @utils.cached_slot_property("_cs_clean_content")
    def clean_content(self) -> str:
        """A property that returns the content in a "cleaned up"
        manner. This basically means that mentions are transformed
        into the way the client shows it. e.g. ``<#id>`` will transform
        into ``#name``.

        This will also transform @everyone and @here mentions into
        non-mentions.

        .. note::

            This *does not* affect markdown. If you want to escape
            or remove markdown then use :func:`utils.escape_markdown` or :func:`utils.remove_markdown`
            respectively, along with this function.
        """

        transformations = {
            re.escape(f"<#{channel.id}>"): f"#{channel.name}"
            for channel in self.channel_mentions
        }

        mention_transforms = {
            re.escape(f"<@{member.id}>"): f"@{member.display_name}"
            for member in self.mentions
        }

        # add the <@!user_id> cases as well..
        second_mention_transforms = {
            re.escape(f"<@!{member.id}>"): f"@{member.display_name}"
            for member in self.mentions
        }

        transformations.update(mention_transforms)
        transformations.update(second_mention_transforms)

        if self.guild is not None:
            role_transforms = {
                re.escape(f"<@&{role.id}>"): f"@{role.name}"
                for role in self.role_mentions
            }
            transformations.update(role_transforms)

        def repl(obj):
            return transformations.get(re.escape(obj.group(0)), "")

        pattern = re.compile("|".join(transformations.keys()))
        result = pattern.sub(repl, self.content)
        return escape_mentions(result)

    @property
    def created_at(self) -> datetime.datetime:
        """The message's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def edited_at(self) -> datetime.datetime | None:
        """An aware UTC datetime object containing the
        edited time of the message.
        """
        return self._edited_timestamp

    @property
    def jump_url(self) -> str:
        """Returns a URL that allows the client to jump to this message."""
        guild_id = getattr(self.guild, "id", "@me")
        return f"https://discord.com/channels/{guild_id}/{self.channel.id}/{self.id}"

    @property
    def poll(self) -> Poll | None:
        return self._state._polls.get(self.id)

    def is_system(self) -> bool:
        """Whether the message is a system message.

        A system message is a message that is constructed entirely by the Discord API
        in response to something.

        .. versionadded:: 1.3
        """
        return self.type not in (
            MessageType.default,
            MessageType.reply,
            MessageType.application_command,
            MessageType.thread_starter_message,
        )

    @utils.cached_slot_property("_cs_system_content")
    def system_content(self) -> str:
        r"""A property that returns the content that is rendered
        regardless of the :attr:`Message.type`.

        In the case of :attr:`MessageType.default` and :attr:`MessageType.reply`\,
        this just returns the regular :attr:`Message.content`, and forwarded messages
        will display the original message's content from :attr:`Message.snapshots`. Otherwise, this
        returns an English message denoting the contents of the system message.
        """

        if self.type is MessageType.default:
            if self.snapshots:
                return self.snapshots[0].message and self.snapshots[0].message.content
            return self.content

        if self.type is MessageType.recipient_add:
            if self.channel.type is ChannelType.group:
                return f"{self.author.name} added {self.mentions[0].name} to the group."
            else:
                return (
                    f"{self.author.name} added {self.mentions[0].name} to the thread."
                )

        if self.type is MessageType.recipient_remove:
            if self.channel.type is ChannelType.group:
                return (
                    f"{self.author.name} removed {self.mentions[0].name} from the"
                    " group."
                )
            else:
                return (
                    f"{self.author.name} removed {self.mentions[0].name} from the"
                    " thread."
                )

        if self.type is MessageType.channel_name_change:
            return f"{self.author.name} changed the channel name: **{self.content}**"

        if self.type is MessageType.channel_icon_change:
            return f"{self.author.name} changed the channel icon."

        if self.type is MessageType.pins_add:
            return f"{self.author.name} pinned a message to this channel."

        if self.type is MessageType.new_member:
            formats = [
                "{0} joined the party.",
                "{0} is here.",
                "Welcome, {0}. We hope you brought pizza.",
                "A wild {0} appeared.",
                "{0} just landed.",
                "{0} just slid into the server.",
                "{0} just showed up!",
                "Welcome {0}. Say hi!",
                "{0} hopped into the server.",
                "Everyone welcome {0}!",
                "Glad you're here, {0}.",
                "Good to see you, {0}.",
                "Yay you made it, {0}!",
            ]

            created_at_ms = int(self.created_at.timestamp() * 1000)
            return formats[created_at_ms % len(formats)].format(self.author.name)

        if self.type is MessageType.premium_guild_subscription:
            if not self.content:
                return f"{self.author.name} just boosted the server!"
            else:
                return (
                    f"{self.author.name} just boosted the server **{self.content}**"
                    " times!"
                )

        if self.type is MessageType.premium_guild_tier_1:
            if not self.content:
                return (
                    f"{self.author.name} just boosted the server! {self.guild} has"
                    " achieved **Level 1!**"
                )
            else:
                return (
                    f"{self.author.name} just boosted the server **{self.content}**"
                    f" times! {self.guild} has achieved **Level 1!**"
                )

        if self.type is MessageType.premium_guild_tier_2:
            if not self.content:
                return (
                    f"{self.author.name} just boosted the server! {self.guild} has"
                    " achieved **Level 2!**"
                )
            else:
                return (
                    f"{self.author.name} just boosted the server **{self.content}**"
                    f" times! {self.guild} has achieved **Level 2!**"
                )

        if self.type is MessageType.premium_guild_tier_3:
            if not self.content:
                return (
                    f"{self.author.name} just boosted the server! {self.guild} has"
                    " achieved **Level 3!**"
                )
            else:
                return (
                    f"{self.author.name} just boosted the server **{self.content}**"
                    f" times! {self.guild} has achieved **Level 3!**"
                )

        if self.type is MessageType.channel_follow_add:
            return f"{self.author.name} has added {self.content} to this channel"

        if self.type is MessageType.guild_stream:
            # the author will be a Member
            return f"{self.author.name} is live! Now streaming {self.author.activity.name}"  # type: ignore

        if self.type is MessageType.guild_discovery_disqualified:
            return (
                "This server has been removed from Server Discovery because it no"
                " longer passes all the requirements. Check Server Settings for more"
                " details."
            )

        if self.type is MessageType.guild_discovery_requalified:
            return (
                "This server is eligible for Server Discovery again and has been"
                " automatically relisted!"
            )

        if self.type is MessageType.guild_discovery_grace_period_initial_warning:
            return (
                "This server has failed Discovery activity requirements for 1 week. If"
                " this server fails for 4 weeks in a row, it will be automatically"
                " removed from Discovery."
            )

        if self.type is MessageType.guild_discovery_grace_period_final_warning:
            return (
                "This server has failed Discovery activity requirements for 3 weeks in"
                " a row. If this server fails for 1 more week, it will be removed from"
                " Discovery."
            )

        if self.type is MessageType.thread_created:
            return (
                f"{self.author.name} started a thread: **{self.content}**. See all"
                " **threads**."
            )

        if self.type is MessageType.reply:
            return self.content

        if self.type is MessageType.thread_starter_message:
            if self.reference is None or self.reference.resolved is None:
                return "Sorry, we couldn't load the first message in this thread"

            # the resolved message for the reference will be a Message
            return self.reference.resolved.content  # type: ignore

        if self.type is MessageType.guild_invite_reminder:
            return (
                "Wondering who to invite?\nStart by inviting anyone who can help you"
                " build the server!"
            )

    async def delete(
        self, *, delay: float | None = None, reason: str | None = None
    ) -> None:
        """|coro|

        Deletes the message.

        Your own messages could be deleted without any proper permissions. However, to
        delete other people's messages, you need the :attr:`~Permissions.manage_messages`
        permission.

        .. versionchanged:: 1.1
            Added the new ``delay`` keyword-only parameter.

        Parameters
        ----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message. If the deletion fails then it is silently ignored.
        reason: Optional[:class:`str`]
            The reason for deleting the message. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have proper permissions to delete the message.
        NotFound
            The message was deleted already
        HTTPException
            Deleting the message failed.
        """
        del_func = self._state.http.delete_message(
            self.channel.id, self.id, reason=reason
        )
        if delay is not None:
            utils.delay_task(delay, del_func)
        else:
            await del_func

    @overload
    async def edit(
        self,
        *,
        content: str | None = ...,
        embed: Embed | None = ...,
        embeds: list[Embed] = ...,
        file: File | None = ...,
        files: list[File] | None = ...,
        attachments: list[Attachment] = ...,
        suppress: bool = ...,
        delete_after: float | None = ...,
        allowed_mentions: AllowedMentions | None = ...,
        view: View | None = ...,
    ) -> Message: ...

    async def edit(
        self,
        content: str | None = MISSING,
        embed: Embed | None = MISSING,
        embeds: list[Embed] = MISSING,
        file: Sequence[File] = MISSING,
        files: list[Sequence[File]] = MISSING,
        attachments: list[Attachment] = MISSING,
        suppress: bool = MISSING,
        delete_after: float | None = None,
        allowed_mentions: AllowedMentions | None = MISSING,
        view: View | None = MISSING,
    ) -> Message:
        """|coro|

        Edits the message.

        The content must be able to be transformed into a string via ``str(content)``.

        .. versionchanged:: 1.3
            The ``suppress`` keyword-only parameter was added.

        Parameters
        ----------
        content: Optional[:class:`str`]
            The new content to replace the message with.
            Could be ``None`` to remove the content.
        embed: Optional[:class:`Embed`]
            The new embed to replace the original with.
            Could be ``None`` to remove the embed.
        embeds: List[:class:`Embed`]
            The new embeds to replace the original with. Must be a maximum of 10.
            To remove all embeds ``[]`` should be passed.

            .. versionadded:: 2.0
        file: Sequence[:class:`File`]
            A new file to add to the message.
        files: List[Sequence[:class:`File`]]
            New files to add to the message.
        attachments: List[:class:`Attachment`]
            A list of attachments to keep in the message. If ``[]`` is passed
            then all attachments are removed.
        suppress: :class:`bool`
            Whether to suppress embeds for the message. This removes
            all the embeds if set to ``True``. If set to ``False``
            this brings the embeds back if they were suppressed.
            Using this parameter requires :attr:`~.Permissions.manage_messages`.
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message we just edited. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: Optional[:class:`~discord.AllowedMentions`]
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.

            .. versionadded:: 1.4
        view: Optional[:class:`~discord.ui.View`]
            The updated view to update this message with. If ``None`` is passed then
            the view is removed.

        Raises
        ------
        NotFound
            The message was not found.
        HTTPException
            Editing the message failed.
        Forbidden
            Tried to suppress a message without permissions or
            edited a message's content or embed that isn't yours.
        ~discord.InvalidArgument
            You specified both ``embed`` and ``embeds``,
            specified both ``file`` and ``files``, or either``file``
            or ``files`` were of the wrong type.
        """

        payload: dict[str, Any] = {}
        if content is not MISSING:
            payload["content"] = str(content) if content is not None else None
        if embed is not MISSING and embeds is not MISSING:
            raise InvalidArgument(
                "cannot pass both embed and embeds parameter to edit()"
            )

        if embed is not MISSING:
            payload["embeds"] = [] if embed is None else [embed.to_dict()]
        elif embeds is not MISSING:
            payload["embeds"] = [e.to_dict() for e in embeds]

        flags = MessageFlags._from_value(self.flags.value)

        if suppress is not MISSING:
            flags.suppress_embeds = suppress

        if allowed_mentions is MISSING:
            if (
                self._state.allowed_mentions is not None
                and self.author.id == self._state.self_id
            ):
                payload["allowed_mentions"] = self._state.allowed_mentions.to_dict()
        elif allowed_mentions is not None:
            if self._state.allowed_mentions is not None:
                payload["allowed_mentions"] = self._state.allowed_mentions.merge(
                    allowed_mentions
                ).to_dict()
            else:
                payload["allowed_mentions"] = allowed_mentions.to_dict()

        if attachments is not MISSING:
            payload["attachments"] = [a.to_dict() for a in attachments]

        if view is not MISSING:
            self._state.prevent_view_updates_for(self.id)
            payload["components"] = view.to_components() if view else []
            if view and view.is_components_v2():
                flags.is_components_v2 = True
        if file is not MISSING and files is not MISSING:
            raise InvalidArgument("cannot pass both file and files parameter to edit()")

        if flags.value != self.flags.value:
            payload["flags"] = flags.value

        if file is not MISSING or files is not MISSING:
            if file is not MISSING:
                if not isinstance(file, File):
                    raise InvalidArgument("file parameter must be of type File")
                files = [file]
            else:
                if len(files) > 10:
                    raise InvalidArgument(
                        "files parameter must be a list of up to 10 elements"
                    )
                elif not all(isinstance(file, File) for file in files):
                    raise InvalidArgument("files parameter must be a list of File")

            if "attachments" not in payload:
                # don't want it to remove any attachments when we just add a new file
                payload["attachments"] = [a.to_dict() for a in self.attachments]
            try:
                data = await self._state.http.edit_files(
                    self.channel.id,
                    self.id,
                    files=files,
                    **payload,
                )
            finally:
                for f in files:
                    f.close()
        else:
            data = await self._state.http.edit_message(
                self.channel.id, self.id, **payload
            )
        message = Message(state=self._state, channel=self.channel, data=data)

        if view and not view.is_finished():
            view.message = message
            view.refresh(message.components)
            if view.is_dispatchable():
                self._state.store_view(view, self.id)

        if delete_after is not None:
            await self.delete(delay=delete_after)

        return message

    async def publish(self) -> None:
        """|coro|

        Publishes this message to your announcement channel.

        You must have the :attr:`~Permissions.send_messages` permission to do this.

        If the message is not your own then the :attr:`~Permissions.manage_messages`
        permission is also needed.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to publish this message.
        HTTPException
            Publishing the message failed.
        """

        await self._state.http.publish_message(self.channel.id, self.id)

    async def pin(self, *, reason: str | None = None) -> None:
        """|coro|

        Pins the message.

        You must have the :attr:`~Permissions.manage_messages` permission to do
        this in a non-private channel context.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The reason for pinning the message. Shows up on the audit log.

            .. versionadded:: 1.4

        Raises
        ------
        Forbidden
            You do not have permissions to pin the message.
        NotFound
            The message or channel was not found or deleted.
        HTTPException
            Pinning the message failed, probably due to the channel
            having more than 50 pinned messages.
        """

        await self._state.http.pin_message(self.channel.id, self.id, reason=reason)
        self.pinned = True

    async def unpin(self, *, reason: str | None = None) -> None:
        """|coro|

        Unpins the message.

        You must have the :attr:`~Permissions.manage_messages` permission to do
        this in a non-private channel context.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The reason for unpinning the message. Shows up on the audit log.

            .. versionadded:: 1.4

        Raises
        ------
        Forbidden
            You do not have permissions to unpin the message.
        NotFound
            The message or channel was not found or deleted.
        HTTPException
            Unpinning the message failed.
        """

        await self._state.http.unpin_message(self.channel.id, self.id, reason=reason)
        self.pinned = False

    async def add_reaction(self, emoji: EmojiInputType) -> None:
        """|coro|

        Add a reaction to the message.

        The emoji may be a unicode emoji, a custom :class:`GuildEmoji`, or an :class:`AppEmoji`.

        You must have the :attr:`~Permissions.read_message_history` permission
        to use this. If nobody else has reacted to the message using this
        emoji, the :attr:`~Permissions.add_reactions` permission is required.

        Parameters
        ----------
        emoji: Union[:class:`GuildEmoji`, :class:`AppEmoji`, :class:`Reaction`, :class:`PartialEmoji`, :class:`str`]
            The emoji to react with.

        Raises
        ------
        HTTPException
            Adding the reaction failed.
        Forbidden
            You do not have the proper permissions to react to the message.
        NotFound
            The emoji you specified was not found.
        InvalidArgument
            The emoji parameter is invalid.
        """

        emoji = convert_emoji_reaction(emoji)
        await self._state.http.add_reaction(self.channel.id, self.id, emoji)

    async def remove_reaction(
        self, emoji: EmojiInputType | Reaction, member: Snowflake
    ) -> None:
        """|coro|

        Remove a reaction by the member from the message.

        The emoji may be a unicode emoji, a custom :class:`GuildEmoji`, or an :class:`AppEmoji`.

        If the reaction is not your own (i.e. ``member`` parameter is not you) then
        the :attr:`~Permissions.manage_messages` permission is needed.

        The ``member`` parameter must represent a member and meet
        the :class:`abc.Snowflake` abc.

        Parameters
        ----------
        emoji: Union[:class:`GuildEmoji`, :class:`AppEmoji`, :class:`Reaction`, :class:`PartialEmoji`, :class:`str`]
            The emoji to remove.
        member: :class:`abc.Snowflake`
            The member for which to remove the reaction.

        Raises
        ------
        HTTPException
            Removing the reaction failed.
        Forbidden
            You do not have the proper permissions to remove the reaction.
        NotFound
            The member or emoji you specified was not found.
        InvalidArgument
            The emoji parameter is invalid.
        """

        emoji = convert_emoji_reaction(emoji)

        if member.id == self._state.self_id:
            await self._state.http.remove_own_reaction(self.channel.id, self.id, emoji)
        else:
            await self._state.http.remove_reaction(
                self.channel.id, self.id, emoji, member.id
            )

    async def clear_reaction(self, emoji: EmojiInputType | Reaction) -> None:
        """|coro|

        Clears a specific reaction from the message.

        The emoji may be a unicode emoji, a custom :class:`GuildEmoji`, or an :class:`AppEmoji`.

        You need the :attr:`~Permissions.manage_messages` permission to use this.

        .. versionadded:: 1.3

        Parameters
        ----------
        emoji: Union[:class:`GuildEmoji`, :class:`AppEmoji`, :class:`Reaction`, :class:`PartialEmoji`, :class:`str`]
            The emoji to clear.

        Raises
        ------
        HTTPException
            Clearing the reaction failed.
        Forbidden
            You do not have the proper permissions to clear the reaction.
        NotFound
            The emoji you specified was not found.
        InvalidArgument
            The emoji parameter is invalid.
        """

        emoji = convert_emoji_reaction(emoji)
        await self._state.http.clear_single_reaction(self.channel.id, self.id, emoji)

    async def clear_reactions(self) -> None:
        """|coro|

        Removes all the reactions from the message.

        You need the :attr:`~Permissions.manage_messages` permission to use this.

        Raises
        ------
        HTTPException
            Removing the reactions failed.
        Forbidden
            You do not have the proper permissions to remove all the reactions.
        """
        await self._state.http.clear_reactions(self.channel.id, self.id)

    async def create_thread(
        self,
        *,
        name: str,
        auto_archive_duration: ThreadArchiveDuration = MISSING,
        slowmode_delay: int = MISSING,
    ) -> Thread:
        """|coro|

        Creates a public thread from this message.

        You must have :attr:`~discord.Permissions.create_public_threads` in order to
        create a public thread from a message.

        The channel this message belongs in must be a :class:`TextChannel`.

        .. versionadded:: 2.0

        Parameters
        ----------
        name: :class:`str`
            The name of the thread.
        auto_archive_duration:  Optional[:class:`int`]
            The duration in minutes before a thread is automatically archived for inactivity.
            If not provided, the channel's default auto archive duration is used.
        slowmode_delay: Optional[:class:`int`]
            Specifies the slowmode rate limit for user in this thread, in seconds.
            A value of ``0`` disables slowmode. The maximum value possible is ``21600``.

        Returns
        -------
        :class:`.Thread`
            The created thread.

        Raises
        ------
        Forbidden
            You do not have permissions to create a thread.
        HTTPException
            Creating the thread failed.
        InvalidArgument
            This message does not have guild info attached.
        """
        if self.guild is None:
            raise InvalidArgument("This message does not have guild info attached.")

        default_auto_archive_duration: ThreadArchiveDuration = getattr(
            self.channel, "default_auto_archive_duration", 1440
        )

        data = await self._state.http.start_thread_with_message(
            self.channel.id,
            self.id,
            name=name,
            auto_archive_duration=auto_archive_duration
            or default_auto_archive_duration,
            rate_limit_per_user=slowmode_delay or 0,
        )

        self.thread = Thread(guild=self.guild, state=self._state, data=data)
        return self.thread

    async def reply(self, content: str | None = None, **kwargs) -> Message:
        """|coro|

        A shortcut method to :meth:`.abc.Messageable.send` to reply to the
        :class:`.Message`.

        .. versionadded:: 1.6

        Returns
        -------
        :class:`.Message`
            The message that was sent.

        Raises
        ------
        ~discord.HTTPException
            Sending the message failed.
        ~discord.Forbidden
            You do not have the proper permissions to send the message.
        ~discord.InvalidArgument
            The ``files`` list is not of the appropriate size, or
            you specified both ``file`` and ``files``.
        """

        return await self.channel.send(content, reference=self.to_reference(), **kwargs)

    async def forward_to(
        self, channel: MessageableChannel | PartialMessageableChannel, **kwargs
    ) -> Message:
        """|coro|

        A shortcut method to :meth:`.abc.Messageable.send` to forward the
        :class:`.Message` to a channel.

        .. versionadded:: 2.7

        Parameters
        ----------
        channel: Union[:class:`TextChannel`, :class:`Thread`, :class:`DMChannel`, :class:`GroupChannel`, :class:`PartialMessageable`]
            The channel to forward this to.

        Returns
        -------
        :class:`.Message`
            The message that was sent.

        Raises
        ------
        ~discord.HTTPException
            Sending the message failed.
        ~discord.Forbidden
            You do not have the proper permissions to send the message.
        ~discord.InvalidArgument
            The ``files`` list is not of the appropriate size, or
            you specified both ``file`` and ``files``.
        """

        return await channel.send(
            reference=self.to_reference(type=MessageReferenceType.forward), **kwargs
        )

    async def end_poll(self) -> Message:
        """|coro|

        Immediately ends the poll associated with this message. Only doable by the poll's owner.

        .. versionadded:: 2.6

        Returns
        -------
        :class:`Message`
            The updated message.

        Raises
        ------
        Forbidden
            You do not have permissions to end this poll.
        HTTPException
            Ending this poll failed.
        """

        data = await self._state.http.expire_poll(
            self.channel.id,
            self.id,
        )
        message = Message(state=self._state, channel=self.channel, data=data)

        return message

    def to_reference(
        self, *, fail_if_not_exists: bool = True, type: MessageReferenceType = None
    ) -> MessageReference:
        """Creates a :class:`~discord.MessageReference` from the current message.

        .. versionadded:: 1.6

        Parameters
        ----------
        fail_if_not_exists: :class:`bool`
            Whether replying using the message reference should raise :class:`HTTPException`
            if the message no longer exists or Discord could not fetch the message.

            .. versionadded:: 1.7

        type: Optional[:class:`~discord.MessageReferenceType`]
            The type of message reference. Defaults to a reply.

            .. versionadded:: 2.7

        Returns
        -------
        :class:`~discord.MessageReference`
            The reference to this message.
        """

        return MessageReference.from_message(
            self, fail_if_not_exists=fail_if_not_exists, type=type
        )

    def to_message_reference_dict(
        self, type: MessageReferenceType = None
    ) -> MessageReferencePayload:
        data: MessageReferencePayload = {
            "message_id": self.id,
            "channel_id": self.channel.id,
            "type": type and type.value,
        }

        if self.guild is not None:
            data["guild_id"] = self.guild.id

        return data


class PartialMessage(Hashable):
    """Represents a partial message to aid with working messages when only
    a message and channel ID are present.

    There are two ways to construct this class. The first one is through
    the constructor itself, and the second is via the following:

    - :meth:`TextChannel.get_partial_message`
    - :meth:`Thread.get_partial_message`
    - :meth:`DMChannel.get_partial_message`
    - :meth:`VoiceChannel.get_partial_message`
    - :meth:`StageChannel.get_partial_message`
    - :meth:`PartialMessageable.get_partial_message`

    Note that this class is trimmed down and has no rich attributes.

    .. versionadded:: 1.6

    .. container:: operations

        .. describe:: x == y

            Checks if two partial messages are equal.

        .. describe:: x != y

            Checks if two partial messages are not equal.

        .. describe:: hash(x)

            Returns the partial message's hash.

    Attributes
    ----------
    channel: Union[:class:`TextChannel`, :class:`Thread`, :class:`DMChannel`, :class:`VoiceChannel`, :class:`StageChannel`, :class:`PartialMessageable`]
        The channel associated with this partial message.
    id: :class:`int`
        The message ID.
    """

    __slots__ = ("channel", "id", "_cs_guild", "_state")

    jump_url: str = Message.jump_url  # type: ignore
    delete = Message.delete
    publish = Message.publish
    pin = Message.pin
    unpin = Message.unpin
    add_reaction = Message.add_reaction
    remove_reaction = Message.remove_reaction
    clear_reaction = Message.clear_reaction
    clear_reactions = Message.clear_reactions
    reply = Message.reply
    forward_to = Message.forward_to
    to_reference = Message.to_reference
    to_message_reference_dict = Message.to_message_reference_dict

    def __init__(self, *, channel: PartialMessageableChannel, id: int):
        if channel.type not in (
            ChannelType.text,
            ChannelType.voice,
            ChannelType.stage_voice,
            ChannelType.news,
            ChannelType.private,
            ChannelType.news_thread,
            ChannelType.public_thread,
            ChannelType.private_thread,
        ) and not isinstance(channel, PartialMessageable):
            raise TypeError(
                "Expected TextChannel, VoiceChannel, StageChannel, DMChannel, Thread or PartialMessageable not"
                f" {type(channel)!r}"
            )

        self.channel: PartialMessageableChannel = channel
        self._state: ConnectionState = channel._state
        self.id: int = id

    def _update(self, data) -> None:
        # This is used for duck typing purposes.
        # Just do nothing with the data.
        pass

    # Also needed for duck typing purposes
    # n.b. not exposed
    pinned = property(None, lambda x, y: None)

    def __repr__(self) -> str:
        return f"<PartialMessage id={self.id} channel={self.channel!r}>"

    @property
    def created_at(self) -> datetime.datetime:
        """The partial message's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def poll(self) -> Poll | None:
        return self._state._polls.get(self.id)

    @utils.cached_slot_property("_cs_guild")
    def guild(self) -> Guild | None:
        """The guild that the partial message belongs to, if applicable."""
        return getattr(self.channel, "guild", None)

    async def fetch(self) -> Message:
        """|coro|

        Fetches the partial message to a full :class:`Message`.

        Returns
        -------
        :class:`Message`
            The full message.

        Raises
        ------
        NotFound
            The message was not found.
        Forbidden
            You do not have the permissions required to get a message.
        HTTPException
            Retrieving the message failed.
        """

        data = await self._state.http.get_message(self.channel.id, self.id)
        return self._state.create_message(channel=self.channel, data=data)

    async def edit(self, **fields: Any) -> Message | None:
        """|coro|

        Edits the message.

        .. versionchanged:: 1.7
            :class:`discord.Message` is returned instead of ``None`` if an edit took place.

        Parameters
        ----------
        content: Optional[:class:`str`]
            The new content to replace the message with.
            Could be ``None`` to remove the content.
        embed: Optional[:class:`~discord.Embed`]
            The new embed to replace the original with.
            Could be ``None`` to remove the embed.
        embeds: Optional[List[:class:`~discord.Embed`]]
            A list of embeds to upload. Must be a maximum of 10.

            .. versionadded:: 2.0
        suppress: :class:`bool`
            Whether to suppress embeds for the message. This removes
            all the embeds if set to ``True``. If set to ``False``
            this brings the embeds back if they were suppressed.
            Using this parameter requires :attr:`~.Permissions.manage_messages`.
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message we just edited. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: Optional[:class:`~discord.AllowedMentions`]
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.
        view: Optional[:class:`~discord.ui.View`]
            The updated view to update this message with. If ``None`` is passed then
            the view is removed.

            .. versionadded:: 2.0

        Returns
        -------
        Optional[:class:`Message`]
            The message that was edited.

        Raises
        ------
        NotFound
            The message was not found.
        HTTPException
            Editing the message failed.
        Forbidden
            Tried to suppress a message without permissions or
            edited a message's content or embed that isn't yours.
        """

        content = fields.pop("content", MISSING)
        if content is not MISSING:
            fields["content"] = str(content) if content is not None else None

        embed = fields.pop("embed", MISSING)
        embeds = fields.pop("embeds", MISSING)

        if embed is not MISSING and embeds is not MISSING:
            raise InvalidArgument("Cannot pass both embed and embeds parameters.")

        if embed is not MISSING:
            fields["embeds"] = [] if embed is None else [embed.to_dict()]

        if embeds is not MISSING:
            fields["embeds"] = [embed.to_dict() for embed in embeds]

        suppress = fields.pop("suppress", False)
        flags = MessageFlags._from_value(0)
        flags.suppress_embeds = suppress
        fields["flags"] = flags.value

        delete_after = fields.pop("delete_after", None)

        allowed_mentions = fields.get("allowed_mentions", MISSING)
        if allowed_mentions is not MISSING:
            if self._state.allowed_mentions is not None:
                allowed_mentions = self._state.allowed_mentions.merge(
                    allowed_mentions
                ).to_dict()
            else:
                allowed_mentions = allowed_mentions.to_dict()
            fields["allowed_mentions"] = allowed_mentions
        else:
            fields["allowed_mentions"] = (
                self._state.allowed_mentions.to_dict()
                if self._state.allowed_mentions
                else None
            )

        view = fields.pop("view", MISSING)
        if view is not MISSING:
            self._state.prevent_view_updates_for(self.id)
            fields["components"] = view.to_components() if view else []

        if fields:
            data = await self._state.http.edit_message(
                self.channel.id, self.id, **fields
            )

        if delete_after is not None:
            await self.delete(delay=delete_after)

        if fields:
            # data isn't unbound
            msg = self._state.create_message(channel=self.channel, data=data)  # type: ignore
            if view and not view.is_finished():
                view.message = msg
                view.refresh(msg.components)
                if view.is_dispatchable():
                    self._state.store_view(view, self.id)
            return msg

    async def end_poll(self) -> Message:
        """|coro|

        Immediately ends the poll associated with this message. Only doable by the poll's owner.

        .. versionadded:: 2.6

        Returns
        -------
        :class:`Message`
            The updated message.

        Raises
        ------
        Forbidden
            You do not have permissions to end this poll.
        HTTPException
            Ending this poll failed.
        """

        data = await self._state.http.expire_poll(
            self.channel.id,
            self.id,
        )
        message = self._state.create_message(channel=self.channel, data=data)

        return message
