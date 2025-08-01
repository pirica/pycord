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

import inspect
import os
from typing import TYPE_CHECKING, Callable, TypeVar

from ..components import Button as ButtonComponent
from ..enums import ButtonStyle, ComponentType
from ..partial_emoji import PartialEmoji, _EmojiTag
from .item import Item, ItemCallbackType

__all__ = (
    "Button",
    "button",
)

if TYPE_CHECKING:
    from ..emoji import AppEmoji, GuildEmoji
    from .view import View

B = TypeVar("B", bound="Button")
V = TypeVar("V", bound="View", covariant=True)


class Button(Item[V]):
    """Represents a UI button.

    .. versionadded:: 2.0

    Parameters
    ----------
    style: :class:`discord.ButtonStyle`
        The style of the button.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        If this button is for a URL, it does not have a custom ID.
    url: Optional[:class:`str`]
        The URL this button sends you to.
    disabled: :class:`bool`
        Whether the button is disabled or not.
    label: Optional[:class:`str`]
        The label of the button, if any. Maximum of 80 chars.
    emoji: Optional[Union[:class:`.PartialEmoji`, :class:`GuildEmoji`, :class:`AppEmoji`, :class:`str`]]
        The emoji of the button, if available.
    sku_id: Optional[Union[:class:`int`]]
        The ID of the SKU this button refers to.
    row: Optional[:class:`int`]
        The relative row this button belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).

        .. warning::

            This parameter does not work with V2 components or with more than 25 items in your view.

    id: Optional[:class:`int`]
        The button's ID.
    """

    __item_repr_attributes__: tuple[str, ...] = (
        "style",
        "url",
        "disabled",
        "label",
        "emoji",
        "sku_id",
        "row",
        "custom_id",
        "id",
    )

    def __init__(
        self,
        *,
        style: ButtonStyle = ButtonStyle.secondary,
        label: str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | GuildEmoji | AppEmoji | PartialEmoji | None = None,
        sku_id: int | None = None,
        row: int | None = None,
        id: int | None = None,
    ):
        super().__init__()
        if label and len(str(label)) > 80:
            raise ValueError("label must be 80 characters or fewer")
        if custom_id is not None and len(str(custom_id)) > 100:
            raise ValueError("custom_id must be 100 characters or fewer")
        if custom_id is not None and url is not None:
            raise TypeError("cannot mix both url and custom_id with Button")
        if sku_id is not None and url is not None:
            raise TypeError("cannot mix both url and sku_id with Button")
        if custom_id is not None and sku_id is not None:
            raise TypeError("cannot mix both sku_id and custom_id with Button")

        if not isinstance(custom_id, str) and custom_id is not None:
            raise TypeError(
                f"expected custom_id to be str, not {custom_id.__class__.__name__}"
            )

        self._provided_custom_id = custom_id is not None
        if url is None and custom_id is None and sku_id is None:
            custom_id = os.urandom(16).hex()

        if url is not None:
            style = ButtonStyle.link
        if sku_id is not None:
            style = ButtonStyle.premium

        if emoji is not None:
            if isinstance(emoji, str):
                emoji = PartialEmoji.from_str(emoji)
            elif isinstance(emoji, _EmojiTag):
                emoji = emoji._to_partial()
            else:
                raise TypeError(
                    "expected emoji to be str, GuildEmoji, AppEmoji, or PartialEmoji not"
                    f" {emoji.__class__}"
                )

        self._underlying = ButtonComponent._raw_construct(
            type=ComponentType.button,
            custom_id=custom_id,
            url=url,
            disabled=disabled,
            label=label,
            style=style,
            emoji=emoji,
            sku_id=sku_id,
            id=id,
        )
        self.row = row

    @property
    def style(self) -> ButtonStyle:
        """The style of the button."""
        return self._underlying.style

    @style.setter
    def style(self, value: ButtonStyle):
        self._underlying.style = value

    @property
    def custom_id(self) -> str | None:
        """The ID of the button that gets received during an interaction.

        If this button is for a URL, it does not have a custom ID.
        """
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: str | None):
        if value is not None and not isinstance(value, str):
            raise TypeError("custom_id must be None or str")
        if value and len(value) > 100:
            raise ValueError("custom_id must be 100 characters or fewer")
        self._underlying.custom_id = value
        self._provided_custom_id = value is not None

    @property
    def url(self) -> str | None:
        """The URL this button sends you to."""
        return self._underlying.url

    @url.setter
    def url(self, value: str | None):
        if value is not None and not isinstance(value, str):
            raise TypeError("url must be None or str")
        self._underlying.url = value

    @property
    def disabled(self) -> bool:
        """Whether the button is disabled or not."""
        return self._underlying.disabled

    @disabled.setter
    def disabled(self, value: bool):
        self._underlying.disabled = bool(value)

    @property
    def label(self) -> str | None:
        """The label of the button, if available."""
        return self._underlying.label

    @label.setter
    def label(self, value: str | None):
        if value and len(str(value)) > 80:
            raise ValueError("label must be 80 characters or fewer")
        self._underlying.label = str(value) if value is not None else value

    @property
    def emoji(self) -> PartialEmoji | None:
        """The emoji of the button, if available."""
        return self._underlying.emoji

    @emoji.setter
    def emoji(self, value: str | GuildEmoji | AppEmoji | PartialEmoji | None):  # type: ignore
        if value is None:
            self._underlying.emoji = None
        elif isinstance(value, str):
            self._underlying.emoji = PartialEmoji.from_str(value)
        elif isinstance(value, _EmojiTag):
            self._underlying.emoji = value._to_partial()
        else:
            raise TypeError(
                "expected str, GuildEmoji, AppEmoji, or PartialEmoji, received"
                f" {value.__class__} instead"
            )

    @property
    def sku_id(self) -> int | None:
        """The ID of the SKU this button refers to."""
        return self._underlying.sku_id

    @sku_id.setter
    def sku_id(self, value: int | None):  # type: ignore
        if value is None:
            self._underlying.sku_id = None
        elif isinstance(value, int):
            self._underlying.sku_id = value
        else:
            raise TypeError(f"expected int or None, received {value.__class__} instead")

    @classmethod
    def from_component(cls: type[B], button: ButtonComponent) -> B:
        return cls(
            style=button.style,
            label=button.label,
            disabled=button.disabled,
            custom_id=button.custom_id,
            url=button.url,
            emoji=button.emoji,
            sku_id=button.sku_id,
            row=None,
            id=button.id,
        )

    @property
    def type(self) -> ComponentType:
        return self._underlying.type

    def to_component_dict(self):
        return self._underlying.to_dict()

    def is_dispatchable(self) -> bool:
        return self.custom_id is not None

    def is_storable(self) -> bool:
        return self.is_dispatchable()

    def is_persistent(self) -> bool:
        if self.style is ButtonStyle.link:
            return self.url is not None
        return super().is_persistent()

    def refresh_component(self, button: ButtonComponent) -> None:
        self._underlying = button


def button(
    *,
    label: str | None = None,
    custom_id: str | None = None,
    disabled: bool = False,
    style: ButtonStyle = ButtonStyle.secondary,
    emoji: str | GuildEmoji | AppEmoji | PartialEmoji | None = None,
    row: int | None = None,
    id: int | None = None,
) -> Callable[[ItemCallbackType], ItemCallbackType]:
    """A decorator that attaches a button to a component.

    The function being decorated should have three parameters, ``self`` representing
    the :class:`discord.ui.View`, the :class:`discord.ui.Button` being pressed and
    the :class:`discord.Interaction` you receive.

    .. note::

        Premium and link buttons cannot be created with this decorator. Consider
        creating a :class:`Button` object manually instead. These types of
        buttons do not have a callback associated since Discord doesn't handle
        them when clicked.

    Parameters
    ----------
    label: Optional[:class:`str`]
        The label of the button, if any.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        It is recommended not to set this parameter to prevent conflicts.
    style: :class:`.ButtonStyle`
        The style of the button. Defaults to :attr:`.ButtonStyle.grey`.
    disabled: :class:`bool`
        Whether the button is disabled or not. Defaults to ``False``.
    emoji: Optional[Union[:class:`str`, :class:`GuildEmoji`, :class:`AppEmoji`, :class:`.PartialEmoji`]]
        The emoji of the button. This can be in string form or a :class:`.PartialEmoji`
        or a full :class:`GuildEmoji` or :class:`AppEmoji`.
    row: Optional[:class:`int`]
        The relative row this button belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    def decorator(func: ItemCallbackType) -> ItemCallbackType:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("button function must be a coroutine function")

        func.__discord_ui_model_type__ = Button
        func.__discord_ui_model_kwargs__ = {
            "style": style,
            "custom_id": custom_id,
            "url": None,
            "disabled": disabled,
            "label": label,
            "emoji": emoji,
            "row": row,
            "id": id,
        }
        return func

    return decorator
