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

from typing import TYPE_CHECKING, Any, TypeVar

import discord.abc
from discord.interactions import Interaction, InteractionMessage, InteractionResponse
from discord.webhook.async_ import Webhook

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    import discord
    from .. import Bot
    from ..state import ConnectionState
    from ..voice_client import VoiceClient

    from .core import ApplicationCommand, Option
    from ..interactions import InteractionChannel
    from ..guild import Guild
    from ..member import Member
    from ..message import Message
    from ..user import User
    from ..permissions import Permissions
    from ..client import ClientUser

    from ..cog import Cog
    from ..webhook import WebhookMessage

    from typing import Callable, Awaitable

from ..utils import cached_property

T = TypeVar("T")
CogT = TypeVar("CogT", bound="Cog")

if TYPE_CHECKING:
    P = ParamSpec("P")
else:
    P = TypeVar("P")

__all__ = ("ApplicationContext", "AutocompleteContext")


class ApplicationContext(discord.abc.Messageable):
    """Represents a Discord application command interaction context.

    This class is not created manually and is instead passed to application
    commands as the first parameter.

    .. versionadded:: 2.0

    Attributes
    ----------
    bot: :class:`.Bot`
        The bot that the command belongs to.
    interaction: :class:`.Interaction`
        The interaction object that invoked the command.
    """

    def __init__(self, bot: Bot, interaction: Interaction):
        self.bot = bot
        self.interaction = interaction

        # below attributes will be set after initialization
        self.focused: Option = None  # type: ignore
        self.value: str = None  # type: ignore
        self.options: dict = None  # type: ignore

        self._state: ConnectionState = self.interaction._state

    async def _get_channel(self) -> InteractionChannel | None:
        return self.interaction.channel

    async def invoke(
        self,
        command: ApplicationCommand[CogT, P, T],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        r"""|coro|

        Calls a command with the arguments given.
        This is useful if you want to just call the callback that a
        :class:`.ApplicationCommand` holds internally.

        .. note::

            This does not handle converters, checks, cooldowns, pre-invoke,
            or after-invoke hooks in any matter. It calls the internal callback
            directly as-if it was a regular function.
            You must take care in passing the proper arguments when
            using this function.

        Parameters
        -----------
        command: :class:`.ApplicationCommand`
            The command that is going to be called.
        \*args
            The arguments to use.
        \*\*kwargs
            The keyword arguments to use.

        Raises
        -------
        TypeError
            The command argument to invoke is missing.
        """
        return await command(self, *args, **kwargs)

    @property
    def command(self) -> ApplicationCommand | None:
        """The command that this context belongs to."""
        return self.interaction.command

    @command.setter
    def command(self, value: ApplicationCommand | None) -> None:
        self.interaction.command = value

    @cached_property
    def channel(self) -> InteractionChannel | None:
        """Union[:class:`abc.GuildChannel`, :class:`PartialMessageable`, :class:`Thread`]:
        Returns the channel associated with this context's command. Shorthand for :attr:`.Interaction.channel`.
        """
        return self.interaction.channel

    @cached_property
    def channel_id(self) -> int | None:
        """Returns the ID of the channel associated with this context's command.
        Shorthand for :attr:`.Interaction.channel_id`.
        """
        return self.interaction.channel_id

    @cached_property
    def guild(self) -> Guild | None:
        """Returns the guild associated with this context's command.
        Shorthand for :attr:`.Interaction.guild`.
        """
        return self.interaction.guild

    @cached_property
    def guild_id(self) -> int | None:
        """Returns the ID of the guild associated with this context's command.
        Shorthand for :attr:`.Interaction.guild_id`.
        """
        return self.interaction.guild_id

    @cached_property
    def locale(self) -> str | None:
        """Returns the locale of the guild associated with this context's command.
        Shorthand for :attr:`.Interaction.locale`.
        """
        return self.interaction.locale

    @cached_property
    def guild_locale(self) -> str | None:
        """Returns the locale of the guild associated with this context's command.
        Shorthand for :attr:`.Interaction.guild_locale`.
        """
        return self.interaction.guild_locale

    @cached_property
    def app_permissions(self) -> Permissions:
        return self.interaction.app_permissions

    @cached_property
    def me(self) -> Member | ClientUser | None:
        """Union[:class:`.Member`, :class:`.ClientUser`]:
        Similar to :attr:`.Guild.me` except it may return the :class:`.ClientUser` in private message
        message contexts, or when :meth:`Intents.guilds` is absent.
        """
        return (
            self.interaction.guild.me
            if self.interaction.guild is not None
            else self.bot.user
        )

    @cached_property
    def message(self) -> Message | None:
        """Returns the message sent with this context's command.
        Shorthand for :attr:`.Interaction.message`, if applicable.
        """
        return self.interaction.message

    @cached_property
    def user(self) -> Member | User:
        """Returns the user that sent this context's command.
        Shorthand for :attr:`.Interaction.user`.
        """
        return self.interaction.user  # type: ignore # command user will never be None

    author: Member | User = user

    @property
    def voice_client(self) -> VoiceClient | None:
        """Returns the voice client associated with this context's command.
        Shorthand for :attr:`Interaction.guild.voice_client<~discord.Guild.voice_client>`, if applicable.
        """
        if self.interaction.guild is None:
            return None

        return self.interaction.guild.voice_client

    @cached_property
    def response(self) -> InteractionResponse:
        """Returns the response object associated with this context's command.
        Shorthand for :attr:`.Interaction.response`.
        """
        return self.interaction.response

    @property
    def selected_options(self) -> list[dict[str, Any]] | None:
        """The options and values that were selected by the user when sending the command.

        Returns
        -------
        Optional[List[Dict[:class:`str`, Any]]]
            A dictionary containing the options and values that were selected by the user when the command
            was processed, if applicable. Returns ``None`` if the command has not yet been invoked,
            or if there are no options defined for that command.
        """
        return self.interaction.data.get("options", None)

    @property
    def unselected_options(self) -> list[Option] | None:
        """The options that were not provided by the user when sending the command.

        Returns
        -------
        Optional[List[:class:`.Option`]]
            A list of Option objects (if any) that were not selected by the user when the command was processed.
            Returns ``None`` if there are no options defined for that command.
        """
        if self.command.options is not None:  # type: ignore
            if self.selected_options:
                return [
                    option
                    for option in self.command.options  # type: ignore
                    if option.to_dict()["name"]
                    not in [opt["name"] for opt in self.selected_options]
                ]
            else:
                return self.command.options  # type: ignore
        return None

    @property
    @discord.utils.copy_doc(InteractionResponse.send_modal)
    def send_modal(self) -> Callable[..., Awaitable[Interaction]]:
        return self.interaction.response.send_modal

    @property
    @discord.utils.copy_doc(Interaction.respond)
    def respond(
        self, *args, **kwargs
    ) -> Callable[..., Awaitable[Interaction | WebhookMessage]]:
        return self.interaction.respond

    @property
    @discord.utils.copy_doc(InteractionResponse.send_message)
    def send_response(self) -> Callable[..., Awaitable[Interaction]]:
        if not self.interaction.response.is_done():
            return self.interaction.response.send_message
        else:
            raise RuntimeError(
                "Interaction was already issued a response. Try using"
                f" {type(self).__name__}.send_followup() instead."
            )

    @property
    @discord.utils.copy_doc(Webhook.send)
    def send_followup(self) -> Callable[..., Awaitable[WebhookMessage]]:
        if self.interaction.response.is_done():
            return self.followup.send
        else:
            raise RuntimeError(
                "Interaction was not yet issued a response. Try using"
                f" {type(self).__name__}.respond() first."
            )

    @property
    @discord.utils.copy_doc(InteractionResponse.defer)
    def defer(self) -> Callable[..., Awaitable[None]]:
        return self.interaction.response.defer

    @property
    def followup(self) -> Webhook:
        """Returns the followup webhook for followup interactions."""
        return self.interaction.followup

    async def delete(self, *, delay: float | None = None) -> None:
        """|coro|

        Deletes the original interaction response message.

        This is a higher level interface to :meth:`Interaction.delete_original_response`.

        Parameters
        ----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait before deleting the message.

        Raises
        ------
        HTTPException
            Deleting the message failed.
        Forbidden
            You do not have proper permissions to delete the message.
        """
        if not self.interaction.response.is_done():
            await self.defer()

        return await self.interaction.delete_original_response(delay=delay)

    @property
    @discord.utils.copy_doc(Interaction.edit_original_response)
    def edit(self) -> Callable[..., Awaitable[InteractionMessage]]:
        return self.interaction.edit_original_response

    @property
    def cog(self) -> Cog | None:
        """Returns the cog associated with this context's command.
        ``None`` if it does not exist.
        """
        if self.command is None:
            return None

        return self.command.cog

    def is_guild_authorised(self) -> bool:
        """:class:`bool`: Checks if the invoked command is guild-installed.
        This is a shortcut for :meth:`Interaction.is_guild_authorised`.

        There is an alias for this called :meth:`.is_guild_authorized`.

        .. versionadded:: 2.7
        """
        return self.interaction.is_guild_authorised()

    def is_user_authorised(self) -> bool:
        """:class:`bool`: Checks if the invoked command is user-installed.
        This is a shortcut for :meth:`Interaction.is_user_authorised`.

        There is an alias for this called :meth:`.is_user_authorized`.

        .. versionadded:: 2.7
        """
        return self.interaction.is_user_authorised()

    def is_guild_authorized(self) -> bool:
        """:class:`bool`: An alias for :meth:`.is_guild_authorised`.

        .. versionadded:: 2.7
        """
        return self.is_guild_authorised()

    def is_user_authorized(self) -> bool:
        """:class:`bool`: An alias for :meth:`.is_user_authorised`.

        .. versionadded:: 2.7
        """
        return self.is_user_authorised()


class AutocompleteContext:
    """Represents context for a slash command's option autocomplete.

    This class is not created manually and is instead passed to an :class:`.Option`'s autocomplete callback.

    .. versionadded:: 2.0

    Attributes
    ----------
    bot: :class:`.Bot`
        The bot that the command belongs to.
    interaction: :class:`.Interaction`
        The interaction object that invoked the autocomplete.
    focused: :class:`.Option`
        The option the user is currently typing.
    value: :class:`.str`
        The content of the focused option.
    options: Dict[:class:`str`, Any]
        A name to value mapping of the options that the user has selected before this option.
    """

    __slots__ = ("bot", "interaction", "focused", "value", "options")

    def __init__(self, bot: Bot, interaction: Interaction):
        self.bot = bot
        self.interaction = interaction

        self.focused: Option = None  # type: ignore
        self.value: str = None  # type: ignore
        self.options: dict = None  # type: ignore

    @property
    def cog(self) -> Cog | None:
        """Returns the cog associated with this context's command.
        ``None`` if it does not exist.
        """
        if self.command is None:
            return None

        return self.command.cog

    @property
    def command(self) -> ApplicationCommand | None:
        """The command that this context belongs to."""
        return self.interaction.command

    @command.setter
    def command(self, value: ApplicationCommand | None) -> None:
        self.interaction.command = value
