"""QuestLine database models.

Stores quest line data from Pokeclicker QuestLineHelper.ts.
Quest lines are story sequences that unlock features, Pokemon, and content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from tortoise import fields

from funbot.db.models.base import BaseModel

if TYPE_CHECKING:
    from funbot.db.models.pokemon.player_quest_progress import PlayerQuestProgress


class QuestLineData(BaseModel):
    """Static quest line data parsed from Pokeclicker.

    Matches Pokeclicker's QuestLine class:
    - name: Unique identifier for the quest line
    - description: Shown to players in the bulletin board
    - bulletinBoard: Which region's bulletin board shows this quest (None = auto-start)
    - requirement: Optional unlock requirement (links to RouteRequirement tree)
    """

    class Meta:
        table = "pokemon_quest_line_data"

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=128, unique=True)  # "Tutorial Quests"
    description = fields.TextField()  # "A short set of quests to get you going."
    bulletin_board = fields.CharField(max_length=32, default="None")  # "Kanto", "Johto", etc.
    total_quests = fields.SmallIntField(default=0)  # Number of quests in this line

    # Link to unlock requirement tree (reuses RouteRequirement structure)
    # Null means no requirement (available from start, like Tutorial)
    root_requirement = fields.ForeignKeyField(
        "models.RouteRequirement",
        related_name="quest_line_conditions",
        on_delete=fields.SET_NULL,
        null=True,
    )

    # Reverse relation to quests
    quests: fields.ReverseRelation[QuestData]
    player_progress: fields.ReverseRelation[PlayerQuestProgress]

    def __str__(self) -> str:
        return self.name


class QuestData(BaseModel):
    """Individual quest within a quest line.

    Matches Pokeclicker's Quest base class and subclasses:
    - CustomQuest: Generic quests with custom completion check
    - TalkToNPCQuest: Talk to an NPC
    - CapturePokemonsQuest: Capture N Pokemon
    - DefeatDungeonQuest: Clear a dungeon
    - DefeatGymQuest: Beat a gym
    - etc.
    """

    class Meta:
        table = "pokemon_quest_data"
        ordering: ClassVar[list[str]] = ["quest_line_id", "quest_index"]

    id = fields.IntField(primary_key=True)
    quest_line = fields.ForeignKeyField(
        "models.QuestLineData", related_name="quests", on_delete=fields.CASCADE
    )
    quest_index = fields.SmallIntField()  # Order within quest line (0-based)
    quest_type = fields.CharField(max_length=64)  # "CustomQuest", "TalkToNPCQuest", etc.
    description = fields.TextField(default="")  # Quest description shown to player
    amount = fields.IntField(default=1)  # Target amount for completion
    points_reward = fields.IntField(default=0)  # Quest points awarded

    # Type-specific data stored as JSON
    # Examples:
    #   TalkToNPCQuest: {"npcName": "Mom"}
    #   DefeatDungeonQuest: {"dungeon": "Viridian Forest"}
    #   DefeatGymQuest: {"gym": "Pewter City"}
    #   DefeatTemporaryBattleQuest: {"battle": "Blue 1"}
    #   CaptureSpecificPokemonQuest: {"pokemon": "Pidgey", "shiny": false}
    #   DefeatPokemonsQuest: {"route": 2, "region": "kanto"}
    type_data = fields.JSONField(null=True, description="Quest type-specific parameters")

    has_custom_reward = fields.BooleanField(default=False)  # Has special reward callback

    def __str__(self) -> str:
        return f"{self.quest_line.name}[{self.quest_index}]: {self.quest_type}"
