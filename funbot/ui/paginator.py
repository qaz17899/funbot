"""Paginator with 5-button navigation and page jump modal."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import discord

from funbot.embeds import ErrorEmbed
from funbot.ui.button import Button
from funbot.ui.modal import Modal
from funbot.ui.view import View

if TYPE_CHECKING:
    from funbot.types import Interaction, User

__all__ = ("Page", "PaginatorView")


@dataclass
class Page:
    """Represents a single page in the paginator."""

    content: str | None = None
    embed: discord.Embed | None = None
    file: discord.File | None = None
    files: list[discord.File] = field(default_factory=list)


class PageJumpModal(Modal):
    """Modal for jumping to a specific page."""

    def __init__(self, max_page: int) -> None:
        super().__init__(title="Jump to Page")
        self.max_page = max_page
        self.page_number: int | None = None

        self.page_input = discord.ui.TextInput(
            label=f"Page Number (1-{max_page})",
            placeholder=f"Enter a number between 1 and {max_page}",
            required=True,
            min_length=1,
            max_length=len(str(max_page)),
        )
        self.add_item(self.page_input)

    async def on_submit(self, interaction: Interaction) -> None:
        """Validate and process the page number input."""
        try:
            page_num = int(self.page_input.value)
            if 1 <= page_num <= self.max_page:
                self.page_number = page_num - 1  # Convert to 0-indexed
                await interaction.response.defer()
                self.stop()
            else:
                embed = ErrorEmbed(
                    title="Invalid Page",
                    description=f"Please enter a number between 1 and {self.max_page}.",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = ErrorEmbed(title="Invalid Input", description="Please enter a valid number.")
            await interaction.response.send_message(embed=embed, ephemeral=True)


class PaginatorView(View):
    """A paginator view with 5-button navigation.

    Buttons: First | Previous | Page X/Y | Next | Last

    The page number button opens a modal to jump to a specific page.
    """

    def __init__(
        self,
        pages: list[Page] | dict[int, Page],
        *,
        author: User | None = None,
        timeout: float = 600.0,
    ) -> None:
        """Initialize the paginator.

        Args:
            pages: List or dict of Page objects to paginate.
            author: The user who can interact with this view.
            timeout: Timeout in seconds.
        """
        super().__init__(author=author, timeout=timeout)

        self._pages = pages
        self._current_page = 0
        self._max_page = len(pages)

        self._add_buttons()
        self._update_button_states()

    @property
    def pages(self) -> list[Page] | dict[int, Page]:
        """Get the pages."""
        return self._pages

    @pages.setter
    def pages(self, pages: list[Page] | dict[int, Page]) -> None:
        """Set new pages and update max page."""
        self._pages = pages
        self._max_page = len(pages)
        self._update_button_states()

    @property
    def current_page(self) -> int:
        """Get current page index (0-indexed)."""
        return self._current_page

    @current_page.setter
    def current_page(self, page: int) -> None:
        """Set current page and update button states."""
        self._current_page = max(0, min(page, self._max_page - 1))
        self._update_button_states()

    @property
    def current_page_data(self) -> Page:
        """Get the current page data."""
        return self._pages[self._current_page]

    def _add_buttons(self) -> None:
        """Add navigation buttons."""
        self.add_item(FirstButton())
        self.add_item(PreviousButton())
        self.add_item(PageNumberButton(self._current_page, self._max_page))
        self.add_item(NextButton())
        self.add_item(LastButton())

    def _update_button_states(self) -> None:
        """Update button disabled states based on current page."""
        for item in self.children:
            if isinstance(item, (FirstButton, PreviousButton)):
                item.disabled = self._current_page == 0
            elif isinstance(item, PageNumberButton):
                item.label = f"{self._current_page + 1}/{self._max_page}"
                item.disabled = self._max_page <= 1
            elif isinstance(item, (NextButton, LastButton)):
                item.disabled = self._current_page >= self._max_page - 1

    async def update_page(self, interaction: Interaction) -> None:
        """Update the message with the current page content."""
        page = self.current_page_data
        self._update_button_states()

        kwargs: dict[str, Any] = {"view": self}

        if page.content is not None:
            kwargs["content"] = page.content

        if page.embed is not None:
            kwargs["embed"] = page.embed

        # Handle files
        if page.file is not None:
            kwargs["attachments"] = [page.file]
        elif page.files:
            kwargs["attachments"] = page.files

        await self.absolute_edit(interaction, **kwargs)
        self.message = await interaction.original_response()

    async def start(self, interaction: Interaction, *, ephemeral: bool = False) -> None:
        """Start the paginator by sending the first page.

        Args:
            interaction: The interaction to respond to.
            ephemeral: Whether the message should be ephemeral.
        """
        page = self.current_page_data
        self._update_button_states()

        kwargs: dict[str, Any] = {"view": self, "ephemeral": ephemeral}

        if page.content is not None:
            kwargs["content"] = page.content

        if page.embed is not None:
            kwargs["embed"] = page.embed

        if page.file is not None:
            kwargs["file"] = page.file
        elif page.files:
            kwargs["files"] = page.files

        if not interaction.response.is_done():
            await interaction.response.send_message(**kwargs)
        else:
            await interaction.followup.send(**kwargs)

        self.message = await interaction.original_response()


class FirstButton(Button["PaginatorView"]):
    """Jump to first page."""

    def __init__(self) -> None:
        super().__init__(
            emoji="⏮️", style=discord.ButtonStyle.secondary, custom_id="paginator:first"
        )

    async def callback(self, interaction: Interaction) -> None:
        self.view._current_page = 0
        await self.view.update_page(interaction)


class PreviousButton(Button["PaginatorView"]):
    """Go to previous page."""

    def __init__(self) -> None:
        super().__init__(emoji="◀️", style=discord.ButtonStyle.primary, custom_id="paginator:prev")

    async def callback(self, interaction: Interaction) -> None:
        self.view._current_page = max(0, self.view._current_page - 1)
        await self.view.update_page(interaction)


class PageNumberButton(Button["PaginatorView"]):
    """Shows current page and opens jump modal when clicked."""

    def __init__(self, current: int, max_page: int) -> None:
        super().__init__(
            label=f"{current + 1}/{max_page}",
            style=discord.ButtonStyle.secondary,
            custom_id="paginator:page",
        )

    async def callback(self, interaction: Interaction) -> None:
        modal = PageJumpModal(self.view._max_page)
        await interaction.response.send_modal(modal)

        # Wait for modal to complete
        await modal.wait()

        if modal.page_number is not None:
            self.view._current_page = modal.page_number
            await self.view.update_page(interaction)


class NextButton(Button["PaginatorView"]):
    """Go to next page."""

    def __init__(self) -> None:
        super().__init__(emoji="▶️", style=discord.ButtonStyle.primary, custom_id="paginator:next")

    async def callback(self, interaction: Interaction) -> None:
        self.view._current_page = min(self.view._max_page - 1, self.view._current_page + 1)
        await self.view.update_page(interaction)


class LastButton(Button["PaginatorView"]):
    """Jump to last page."""

    def __init__(self) -> None:
        super().__init__(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="paginator:last")

    async def callback(self, interaction: Interaction) -> None:
        self.view._current_page = self.view._max_page - 1
        await self.view.update_page(interaction)
