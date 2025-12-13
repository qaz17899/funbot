"""ActionRow component - container for buttons and selects."""

from __future__ import annotations

from discord import ui

__all__ = ("ActionRow",)


class ActionRow[V: ui.LayoutView](ui.ActionRow[V]):
    """Enhanced ActionRow for grouping buttons and selects.

    An ActionRow can contain up to 5 buttons OR 1 select menu.
    In V2, buttons and selects MUST be placed in an ActionRow.

    Usage with decorator (recommended):
        class MyLayout(LayoutView):
            row = ActionRow()

            @row.button(label="Click Me")
            async def click(self, interaction, button):
                await interaction.response.send_message("Clicked!")

            @row.select(placeholder="Choose", options=[...])
            async def choose(self, interaction, select):
                await interaction.response.send_message(f"Chose: {select.values}")

    Usage as subclass:
        class MyButtonRow(ActionRow):
            @ui.button(label="Button A")
            async def button_a(self, interaction, button):
                ...

            @ui.button(label="Button B")
            async def button_b(self, interaction, button):
                ...

        class MyLayout(LayoutView):
            buttons = MyButtonRow()
    """
