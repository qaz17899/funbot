"""Route requirement models for unlock conditions.

Based on Pokeclicker's requirement system with TREE STRUCTURE for nested logic:
- RouteKillRequirement: defeat N pokemon on a route
- GymBadgeRequirement: need specific badge
- ClearDungeonRequirement: clear a dungeon
- TemporaryBattleRequirement: defeat a trainer
- OneFromManyRequirement: OR logic (at least one child must pass)
- MultiRequirement: AND logic (all children must pass)
"""

from __future__ import annotations

from enum import IntEnum

from tortoise import fields
from tortoise.models import Model


class RequirementType(IntEnum):
    """Types of route unlock requirements."""

    # Leaf nodes (basic conditions)
    ROUTE_KILL = 1  # RouteKillRequirement(10, Region.kanto, 1)
    GYM_BADGE = 2  # GymBadgeRequirement(BadgeEnums.Boulder)
    DUNGEON_CLEAR = 3  # ClearDungeonRequirement(1, getDungeonIndex('Mt. Moon'))
    TEMP_BATTLE = 4  # TemporaryBattleRequirement('Blue 2')
    QUEST_LINE_COMPLETED = 5  # QuestLineCompletedRequirement('Celio\'s Errand')
    QUEST_LINE_STEP = 6  # QuestLineStepCompletedRequirement('Bill\'s Errand', 0)
    OBTAINED_POKEMON = 7  # ObtainedPokemonRequirement('Sunkern')
    WEATHER = 8  # WeatherRequirement
    DAY_OF_WEEK = 9  # DayOfWeekRequirement
    SPECIAL_EVENT = 10  # SpecialEventRequirement
    ITEM_OWNED = 11  # ItemOwnedRequirement
    STATISTIC = 12  # StatisticRequirement
    POKEMON_LEVEL = 13  # PokemonLevelRequirement

    # Branch nodes (logical operators)
    ONE_FROM_MANY = 100  # OR - at least one child must pass
    MULTI = 101  # AND - all children must pass


class RouteRequirement(Model):
    """Unlock requirement for a route.

    Uses TREE STRUCTURE with self-referencing parent for nested AND/OR logic.
    Example: OneFromManyRequirement containing two RouteKillRequirements
    """

    id = fields.IntField(pk=True)

    # Root requirements link to a route; child requirements link to parent instead
    route = fields.ForeignKeyField(
        "models.RouteData",
        related_name="requirements",
        on_delete=fields.CASCADE,
        null=True,  # Null for child requirements
    )

    # TREE STRUCTURE: self-referencing for nested requirements
    parent = fields.ForeignKeyField(
        "models.RouteRequirement",
        related_name="children",
        on_delete=fields.CASCADE,
        null=True,  # Null for root requirements
    )

    requirement_type = fields.SmallIntField(description="RequirementType enum value")

    # Flexible parameters stored as JSON
    # Examples:
    #   ROUTE_KILL: {"amount": 10, "region": 0, "route": 1}
    #   GYM_BADGE: {"badge": "Boulder"}
    #   DUNGEON_CLEAR: {"amount": 1, "dungeon": "Mt. Moon"}
    #   TEMP_BATTLE: {"battle": "Blue 2"}
    #   QUEST_LINE_COMPLETED: {"quest": "Celio's Errand"}
    #   QUEST_LINE_STEP: {"quest": "Bill's Errand", "step": 0}
    parameters = fields.JSONField(null=True, description="Requirement-specific parameters")

    # Reverse relation for tree structure
    children: fields.ReverseRelation[RouteRequirement]

    class Meta:
        table = "pokemon_route_requirement"


class SpecialRoutePokemon(Model):
    """Pokemon that appear on routes under special conditions.

    Links to a RouteRequirement tree for its unlock condition.
    """

    id = fields.IntField(pk=True)
    route = fields.ForeignKeyField(
        "models.RouteData", related_name="special_pokemon", on_delete=fields.CASCADE
    )
    pokemon_names = fields.JSONField(description='Pokemon names ["Sunkern"]')

    # Root requirement node for this special Pokemon's condition
    # This allows reusing the same recursive evaluation logic
    root_requirement = fields.ForeignKeyField(
        "models.RouteRequirement",
        related_name="special_pokemon_conditions",
        on_delete=fields.SET_NULL,
        null=True,
    )

    class Meta:
        table = "pokemon_special_route_pokemon"
