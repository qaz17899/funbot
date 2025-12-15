"""Gym battle service for simulating gym battles.

Based on Pokeclicker mechanics:
- 30 second time limit (30 ticks at 1 second per tick)
- Party attack damages gym Pokemon sequentially
- Win = defeat all gym Pokemon within time limit
- Reward = badge (first win) + money
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from urllib.parse import quote

from funbot.db.models.pokemon.gym_data import GymData, GymPokemon, PlayerBadge
from funbot.pokemon.services.battle_service import BattleService

# Constants
GYM_TIME_LIMIT = 30  # seconds
POKECLICKER_NPC_BASE_URL = "https://raw.githubusercontent.com/pokeclicker/pokeclicker/develop/src/assets/images/npcs"
POKECLICKER_BADGE_BASE_URL = "https://raw.githubusercontent.com/pokeclicker/pokeclicker/develop/src/assets/images/badges"


class GymBattleStatus(Enum):
    """Status of a gym battle."""

    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"


@dataclass
class GymPokemonState:
    """State of a single gym Pokemon during battle."""

    name: str
    level: int
    max_hp: int
    current_hp: int
    sprite_url: str | None = None  # Pokemon sprite for UI display

    @property
    def hp_percent(self) -> float:
        """Get HP as percentage (0.0-1.0)."""
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0


@dataclass
class GymBattleState:
    """Complete state of an ongoing gym battle."""

    gym: GymData
    gym_pokemon: list[GymPokemonState]
    current_pokemon_index: int
    time_remaining: float
    player_attack: int
    status: GymBattleStatus = GymBattleStatus.IN_PROGRESS
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def current_pokemon(self) -> GymPokemonState | None:
        """Get the current Pokemon being battled."""
        if 0 <= self.current_pokemon_index < len(self.gym_pokemon):
            return self.gym_pokemon[self.current_pokemon_index]
        return None

    @property
    def total_pokemon(self) -> int:
        """Get total number of gym Pokemon."""
        return len(self.gym_pokemon)

    @property
    def defeated_count(self) -> int:
        """Get number of defeated Pokemon."""
        return self.current_pokemon_index


@dataclass
class GymBattleResult:
    """Result of a completed gym battle."""

    gym_name: str
    leader_name: str
    won: bool
    badge_name: str | None  # Badge earned (if won)
    money_earned: int  # Money earned (if won)
    time_used: float  # Time used in seconds
    is_first_win: bool  # True if this is first time getting badge


class GymService:
    """Service for gym battle operations."""

    @staticmethod
    def get_leader_image_url(leader_name: str) -> str:
        """Get the URL for a gym leader's image.

        Args:
            leader_name: Name of the gym leader (e.g., "Brock")

        Returns:
            URL to the leader's image on Pokeclicker GitHub
        """
        # URL encode the name for special characters
        encoded_name = quote(leader_name)
        return f"{POKECLICKER_NPC_BASE_URL}/{encoded_name}.png"

    @staticmethod
    def get_badge_image_url(badge_name: str) -> str:
        """Get the URL for a badge's image.

        Args:
            badge_name: Name of the badge (e.g., "Boulder")

        Returns:
            URL to the badge's image on Pokeclicker GitHub
        """
        return f"{POKECLICKER_BADGE_BASE_URL}/{badge_name}.svg"

    @staticmethod
    async def get_gym_by_name(name: str) -> GymData | None:
        """Get a gym by its name.

        Args:
            name: Town/gym name (e.g., "Pewter City")

        Returns:
            GymData if found, None otherwise
        """
        return await GymData.filter(name__icontains=name).first()

    @staticmethod
    async def get_available_gyms(region: int = 0) -> list[GymData]:
        """Get all gyms in a region.

        Args:
            region: Region ID (0=Kanto, 1=Johto, etc.)

        Returns:
            List of gyms in the region
        """
        return await GymData.filter(region=region).order_by("id").all()

    @staticmethod
    async def get_player_badges(player_id: int) -> list[str]:
        """Get list of badge names the player has earned.

        Args:
            player_id: The player's user ID

        Returns:
            List of badge names
        """
        badges = await PlayerBadge.filter(user_id=player_id).all()
        return [b.badge for b in badges]

    @staticmethod
    async def has_badge(player_id: int, badge_name: str) -> bool:
        """Check if player has a specific badge.

        Args:
            player_id: The player's user ID
            badge_name: Name of the badge

        Returns:
            True if player has the badge
        """
        return await PlayerBadge.filter(user_id=player_id, badge=badge_name).exists()

    @staticmethod
    async def start_battle(player_id: int, gym: GymData) -> GymBattleState:
        """Start a gym battle.

        Args:
            player_id: Player's Discord ID
            gym: The gym to challenge

        Returns:
            Initial battle state
        """
        from funbot.db.models.pokemon.pokemon_data import PokemonData

        # Get gym Pokemon
        gym_pokemon_models = await GymPokemon.filter(gym=gym).order_by("order").all()

        # Get sprite URLs for all gym Pokemon
        pokemon_names = [gp.pokemon_name for gp in gym_pokemon_models]
        pokemon_data_map: dict[str, str | None] = {}
        if pokemon_names:
            pokemon_data_list = await PokemonData.filter(name__in=pokemon_names).all()
            pokemon_data_map = {p.name: p.sprite_url for p in pokemon_data_list}

        # Convert to battle state with sprites
        gym_pokemon = [
            GymPokemonState(
                name=gp.pokemon_name,
                level=gp.level,
                max_hp=gp.max_health,
                current_hp=gp.max_health,
                sprite_url=pokemon_data_map.get(gp.pokemon_name),
            )
            for gp in gym_pokemon_models
        ]

        # Calculate player attack using centralized BattleService
        player_attack = await BattleService.get_player_party_attack(player_id)

        return GymBattleState(
            gym=gym,
            gym_pokemon=gym_pokemon,
            current_pokemon_index=0,
            time_remaining=float(GYM_TIME_LIMIT),
            player_attack=player_attack,
        )

    @staticmethod
    def tick_battle(state: GymBattleState, delta: float = 1.0) -> GymBattleState:
        """Process one tick of battle.

        Args:
            state: Current battle state
            delta: Time delta in seconds (default 1.0)

        Returns:
            Updated battle state
        """
        if state.status != GymBattleStatus.IN_PROGRESS:
            return state

        # Decrease time
        state.time_remaining -= delta

        # Check time out
        if state.time_remaining <= 0:
            state.status = GymBattleStatus.LOST
            return state

        # Apply damage to current Pokemon
        current = state.current_pokemon
        if current:
            # Use centralized damage calculation from BattleService
            base_damage = BattleService.calculate_damage_per_tick(state.player_attack)
            damage = int(base_damage * delta)
            current.current_hp = max(0, current.current_hp - damage)

            # Check if defeated
            if current.current_hp <= 0:
                state.current_pokemon_index += 1

                # Check if all Pokemon defeated
                if state.current_pokemon_index >= len(state.gym_pokemon):
                    state.status = GymBattleStatus.WON

        return state

    @staticmethod
    async def complete_battle(player_id: int, state: GymBattleState) -> GymBattleResult:
        """Complete a gym battle and award rewards.

        Args:
            player_id: Player's Discord ID
            state: Final battle state

        Returns:
            Battle result with rewards
        """
        from funbot.db.models.pokemon.player_wallet import PlayerWallet

        won = state.status == GymBattleStatus.WON
        badge_name = None
        money_earned = 0
        is_first_win = False

        if won:
            badge_name = state.gym.badge
            money_earned = state.gym.money_reward

            # Check if this is first win
            already_has_badge = await GymService.has_badge(player_id, badge_name)

            if not already_has_badge:
                is_first_win = True

                # Award badge
                await PlayerBadge.create(
                    user_id=player_id, badge=badge_name, badge_id=state.gym.badge_id
                )

            # Award money via wallet
            wallet = await PlayerWallet.filter(user_id=player_id).first()
            if wallet:
                await wallet.add_pokedollar(money_earned)

        time_used = GYM_TIME_LIMIT - max(0, state.time_remaining)

        return GymBattleResult(
            gym_name=state.gym.name,
            leader_name=state.gym.leader,
            won=won,
            badge_name=badge_name,
            money_earned=money_earned,
            time_used=time_used,
            is_first_win=is_first_win,
        )

    @staticmethod
    def simulate_full_battle(state: GymBattleState) -> GymBattleState:
        """Simulate the entire battle instantly (for non-animated mode).

        Args:
            state: Initial battle state

        Returns:
            Final battle state
        """
        # Calculate total gym HP
        total_gym_hp = sum(gp.max_hp for gp in state.gym_pokemon)

        # Calculate ticks needed using centralized BattleService (SSOT)
        ticks_needed = BattleService.calculate_ticks_to_defeat(
            total_gym_hp, state.player_attack
        )

        if ticks_needed <= GYM_TIME_LIMIT:
            # Win!
            state.status = GymBattleStatus.WON
            state.time_remaining = GYM_TIME_LIMIT - ticks_needed
            state.current_pokemon_index = len(state.gym_pokemon)

            # Set all Pokemon HP to 0
            for gp in state.gym_pokemon:
                gp.current_hp = 0
        else:
            # Lose
            state.status = GymBattleStatus.LOST
            state.time_remaining = 0

            # Calculate damage dealt and update HP sequentially (with multiplier)
            damage_per_tick = BattleService.calculate_damage_per_tick(
                state.player_attack
            )
            damage_dealt = damage_per_tick * GYM_TIME_LIMIT
            for i, gp in enumerate(state.gym_pokemon):
                if damage_dealt >= gp.max_hp:
                    damage_dealt -= gp.max_hp
                    gp.current_hp = 0
                    state.current_pokemon_index = i + 1
                else:
                    gp.current_hp = gp.max_hp - damage_dealt
                    state.current_pokemon_index = i
                    break

        return state
