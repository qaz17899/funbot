"""Player quest progress tracking.

Tracks player's progress through quest lines matching Pokeclicker's QuestLine state.
"""

from __future__ import annotations

from tortoise import fields

from funbot.db.models.base import BaseModel
from funbot.pokemon.constants import QuestLineState


class PlayerQuestProgress(BaseModel):
    """Track player's progress through quest lines.

    Matches Pokeclicker's quest tracking:
    - state(): QuestLineState.inactive/started/ended
    - curQuest(): Current quest index
    - curQuestInitial(): Initial quest index (for step requirements)
    """

    class Meta:
        table = "pokemon_player_quest_progress"
        unique_together = (("user", "quest_line"),)

    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="quest_progress", on_delete=fields.CASCADE
    )
    quest_line = fields.ForeignKeyField(
        "models.QuestLineData", related_name="player_progress", on_delete=fields.CASCADE
    )

    # Quest line state (Pokeclicker: this.state())
    # Use integer directly for Postgres compatibility (0=INACTIVE, 1=STARTED, 2=ENDED)
    state = fields.SmallIntField(default=0)

    # Current quest index within the line (Pokeclicker: this.curQuest())
    current_quest_index = fields.SmallIntField(default=0)

    # Timestamps for tracking
    started_at = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)

    def __str__(self) -> str:
        state_name = QuestLineState(self.state).name
        return f"{self.quest_line.name}: {state_name} (step {self.current_quest_index})"

    @property
    def is_completed(self) -> bool:
        """Check if quest line is completed."""
        return self.state == QuestLineState.ENDED

    @property
    def is_started(self) -> bool:
        """Check if quest line is started (or completed)."""
        return self.state >= QuestLineState.STARTED
