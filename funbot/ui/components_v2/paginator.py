"""V2 Paginator with 5-button navigation using LayoutView."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import discord
from discord import ui

from funbot.embeds import ErrorEmbed
from funbot.ui.components.modal import Modal

from .action_row import ActionRow
from .container import Container
from .layout_view import LayoutView
from .separator import Separator
from .text_display import TextDisplay

if TYPE_CHECKING:
    from funbot.types import Interaction, User

__all__ = ("Page", "PaginatorView")


@dataclass
class Page:
    """Represents a single page in the V2 paginator.

    Unlike legacy Page, V2 pages use text content displayed in a Container.
    Files are still supported for attachments.
    """

    content: str = ""
    """Markdown content for this page."""

    files: list[discord.File] = field(default_factory=list)
    """Optional files to attach."""


class PageJumpModal(Modal):
    """Modal for jumping to a specific page."""

    def __init__(self, max_page: int) -> None:
        super().__init__(title="Jump to Page")
        self.max_page = max_page
        self.page_number: int | None = None

        self.page_input = ui.TextInput(
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
            page = int(self.page_input.value)
            if 1 <= page <= self.max_page:
                self.page_number = page - 1  # Convert to 0-indexed
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


class PaginatorView(LayoutView):
    """A V2 paginator view with 5-button navigation.

    Buttons: First | Previous | Page X/Y | Next | Last

    The page number button opens a modal to jump to a specific page.
    Content is displayed in a styled Container.

    Example:
        pages = [
            Page(content="# Page 1\\nContent here"),
            Page(content="# Page 2\\nMore content"),
        ]
        view = PaginatorView(pages, author=interaction.user)
        await view.start(interaction)
    """

    CONTENT_ID = 99901  # Component ID for the content TextDisplay

    def __init__(
        self, pages: list[Page], *, author: User | None = None, timeout: float = 600.0
    ) -> None:
        """Initialize the V2 paginator.

        Args:
            pages: List of Page objects to paginate.
            author: The user who can interact with this view.
            timeout: Timeout in seconds.
        """
        super().__init__(author=author, timeout=timeout)
        self._pages = pages
        self._current_page = 0
        self.max_page = len(pages)

        # Build the layout
        self._build_layout()

    def _build_layout(self) -> None:
        """Build the initial layout structure."""
        # Content container
        self.content_container = Container(accent_color=discord.Color.blurple())
        self.content_display = TextDisplay(
            self._pages[0].content if self._pages else "No content", id=self.CONTENT_ID
        )
        self.content_container.add_item(self.content_display)
        self.add_item(self.content_container)

        # Separator before buttons
        self.add_item(Separator(divider=False, spacing=discord.SeparatorSpacing.small))

        # Navigation buttons
        self.nav_row = NavigationRow(self)
        self.add_item(self.nav_row)

    @property
    def pages(self) -> list[Page]:
        """Get the pages."""
        return self._pages

    @pages.setter
    def pages(self, pages: list[Page]) -> None:
        """Set new pages and update max page."""
        self._pages = pages
        self.max_page = len(pages)
        if self._current_page >= self.max_page:
            self._current_page = max(0, self.max_page - 1)

    @property
    def current_page(self) -> int:
        """Get current page index (0-indexed)."""
        return self._current_page

    @current_page.setter
    def current_page(self, page: int) -> None:
        """Set current page and update button states."""
        self._current_page = max(0, min(page, self.max_page - 1))
        self.nav_row.update_states(self._current_page, self.max_page)

    @property
    def current_page_data(self) -> Page:
        """Get the current page data."""
        return self._pages[self._current_page]

    async def update_page(self, interaction: Interaction) -> None:
        """Update the view with the current page content."""
        self.content_display.content = self.current_page_data.content
        self.nav_row.update_states(self._current_page, self.max_page)

        kwargs: dict[str, Any] = {"view": self}
        if self.current_page_data.files:
            kwargs["attachments"] = self.current_page_data.files

        await self.absolute_edit(interaction, **kwargs)

    async def start(self, interaction: Interaction, *, ephemeral: bool = False) -> None:
        """Start the paginator by sending the first page.

        Args:
            interaction: The interaction to respond to.
            ephemeral: Whether the message should be ephemeral.
        """
        self.nav_row.update_states(self._current_page, self.max_page)

        kwargs: dict[str, Any] = {"view": self, "ephemeral": ephemeral}
        if self.current_page_data.files:
            kwargs["files"] = self.current_page_data.files

        if interaction.response.is_done():
            msg = await interaction.followup.send(**kwargs, wait=True)
        else:
            await interaction.response.send_message(**kwargs)
            msg = await interaction.original_response()

        self.message = msg


class NavigationRow(ActionRow["PaginatorView"]):
    """Navigation buttons for the paginator."""

    def __init__(self, paginator: PaginatorView) -> None:
        super().__init__()
        self.paginator = paginator
        self._page_label = f"1/{paginator.max_page}"

    def update_states(self, current: int, max_page: int) -> None:
        """Update button disabled states and page label."""
        at_start = current <= 0
        at_end = current >= max_page - 1

        # Update all buttons
        for child in self.children:
            if isinstance(child, ui.Button):
                if child.custom_id in {"paginator:first", "paginator:prev"}:
                    child.disabled = at_start
                elif child.custom_id == "paginator:page":
                    child.label = f"{current + 1}/{max_page}"
                elif child.custom_id in {"paginator:next", "paginator:last"}:
                    child.disabled = at_end

    @ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, custom_id="paginator:first")
    async def first_button(self, interaction: Interaction, _button: ui.Button) -> None:
        """Jump to first page."""
        self.paginator.current_page = 0
        await self.paginator.update_page(interaction)

    @ui.button(emoji="◀️", style=discord.ButtonStyle.primary, custom_id="paginator:prev")
    async def prev_button(self, interaction: Interaction, _button: ui.Button) -> None:
        """Go to previous page."""
        self.paginator.current_page -= 1
        await self.paginator.update_page(interaction)

    @ui.button(label="1/1", style=discord.ButtonStyle.secondary, custom_id="paginator:page")
    async def page_button(self, interaction: Interaction, _button: ui.Button) -> None:
        """Show page jump modal."""
        modal = PageJumpModal(self.paginator.max_page)
        await interaction.response.send_modal(modal)
        await modal.wait()

        if modal.page_number is not None:
            self.paginator.current_page = modal.page_number
            await self.paginator.update_page(interaction)

    @ui.button(emoji="▶️", style=discord.ButtonStyle.primary, custom_id="paginator:next")
    async def next_button(self, interaction: Interaction, _button: ui.Button) -> None:
        """Go to next page."""
        self.paginator.current_page += 1
        await self.paginator.update_page(interaction)

    @ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="paginator:last")
    async def last_button(self, interaction: Interaction, _button: ui.Button) -> None:
        """Jump to last page."""
        self.paginator.current_page = self.paginator.max_page - 1
        await self.paginator.update_page(interaction)
