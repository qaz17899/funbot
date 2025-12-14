"""Player's Pokeball inventory model.

Tracks quantity of each ball type owned by the player.
Matches Pokeclicker's pokeballs[ball].quantity() system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tortoise import fields
from tortoise.expressions import F
from tortoise.models import Model

if TYPE_CHECKING:
    from funbot.pokemon.constants.enums import Pokeball

# Ball type to field name mappings
_BALL_QTY_FIELDS = {1: "pokeball", 2: "greatball", 3: "ultraball", 4: "masterball"}

_BALL_USED_FIELDS = {
    1: "pokeball_used",
    2: "greatball_used",
    3: "ultraball_used",
    4: "masterball_used",
}

_BALL_PURCHASED_FIELDS = {
    1: "pokeball_purchased",
    2: "greatball_purchased",
    3: "ultraball_purchased",
    4: "masterball_purchased",
}


class PlayerBallInventory(Model):
    """Pokeball inventory for a player.

    Based on Pokeclicker Pokeballs.ts:
    - Each ball type has a quantity
    - Starters receive 25 Poké Balls
    - Balls are consumed on catch attempts
    """

    class Meta:
        table = "player_ball_inventory"

    id = fields.IntField(pk=True)

    # Owner reference (one-to-one)
    user = fields.OneToOneField(
        "models.User", related_name="ball_inventory", on_delete=fields.CASCADE
    )

    # Ball quantities (Pokeclicker: Pokeballs.ts creates array of Pokeball objects with quantity)
    # Starting with 25 Poké Balls for new players (Pokeballs.ts:17)
    pokeball = fields.IntField(default=25, description="Poké Ball quantity")
    greatball = fields.IntField(default=0, description="Great Ball quantity")
    ultraball = fields.IntField(default=0, description="Ultra Ball quantity")
    masterball = fields.IntField(default=0, description="Master Ball quantity")

    # Statistics
    pokeball_used = fields.IntField(default=0, description="Poké Balls used")
    greatball_used = fields.IntField(default=0, description="Great Balls used")
    ultraball_used = fields.IntField(default=0, description="Ultra Balls used")
    masterball_used = fields.IntField(default=0, description="Master Balls used")

    pokeball_purchased = fields.IntField(default=0, description="Poké Balls purchased")
    greatball_purchased = fields.IntField(default=0, description="Great Balls purchased")
    ultraball_purchased = fields.IntField(default=0, description="Ultra Balls purchased")
    masterball_purchased = fields.IntField(default=0, description="Master Balls purchased")

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    def __str__(self) -> str:
        return f"BallInventory(pokeball={self.pokeball})"

    def get_quantity(self, ball_type: Pokeball | int) -> int:
        """Get quantity of a ball type.

        Args:
            ball_type: Pokeball enum or int value (1=POKEBALL, 2=GREATBALL, etc.)

        Returns:
            Quantity of that ball type
        """
        qty_field = _BALL_QTY_FIELDS.get(int(ball_type))
        if qty_field is None:
            return 0
        return getattr(self, qty_field, 0)

    def has_ball(self, ball_type: Pokeball | int) -> bool:
        """Check if player has at least 1 of this ball type."""
        return self.get_quantity(ball_type) > 0

    async def use_ball(self, ball_type: Pokeball | int) -> bool:
        """Use one ball of the specified type.

        Matches Pokeclicker Pokeballs.ts:222-225:
        - Decrement quantity
        - Increment used statistic

        Args:
            ball_type: Pokeball enum or int value

        Returns:
            True if ball was used, False if no balls available
        """
        ball_int = int(ball_type)
        qty_field = _BALL_QTY_FIELDS.get(ball_int)
        used_field = _BALL_USED_FIELDS.get(ball_int)

        if qty_field is None or used_field is None:
            return False

        # Check if we have any
        if getattr(self, qty_field) <= 0:
            return False

        # Atomic decrement quantity, increment used
        await PlayerBallInventory.filter(id=self.id).update(
            **{qty_field: F(qty_field) - 1, used_field: F(used_field) + 1}
        )

        # Update local state
        setattr(self, qty_field, getattr(self, qty_field) - 1)
        setattr(self, used_field, getattr(self, used_field) + 1)

        return True

    async def gain_balls(
        self, ball_type: Pokeball | int, amount: int, purchased: bool = False
    ) -> int:
        """Add balls to inventory.

        Matches Pokeclicker Pokeballs.ts:214-220:
        - Increment quantity
        - If purchased, increment purchased statistic

        Args:
            ball_type: Pokeball enum or int value
            amount: Number of balls to add
            purchased: Whether this was a purchase (for statistics)

        Returns:
            New quantity of that ball type
        """
        ball_int = int(ball_type)
        qty_field = _BALL_QTY_FIELDS.get(ball_int)
        purchased_field = _BALL_PURCHASED_FIELDS.get(ball_int)

        if qty_field is None:
            return 0

        update_dict: dict[str, Any] = {qty_field: F(qty_field) + amount}
        if purchased and purchased_field:
            update_dict[purchased_field] = F(purchased_field) + amount

        await PlayerBallInventory.filter(id=self.id).update(**update_dict)

        # Refresh local state
        fields_to_refresh = [qty_field]
        if purchased and purchased_field:
            fields_to_refresh.append(purchased_field)
        await self.refresh_from_db(fields=fields_to_refresh)

        return getattr(self, qty_field)
