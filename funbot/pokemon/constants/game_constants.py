"""Game constants and formulas for the Pokemon system.

Based on Pokeclicker mechanics with simplifications for Discord bot usage.
"""

from __future__ import annotations

# =============================================================================
# Battle Constants
# =============================================================================

# How often auto-battle ticks (seconds) - used for calculation only
BATTLE_TICK_SECONDS: float = 1.0

# Damage multiplier to compensate for no click attack in Discord bot
# Original Pokeclicker has both auto-attack AND click attack
BOT_CLICK_MULTIPLIER: int = 2

# Base health formula constants
# Health = ROUTE_HEALTH_BASE * (route^2.2 / 12)^1.15 * (1 + region/20)
ROUTE_HEALTH_BASE: int = 100
ROUTE_HEALTH_MIN: int = 20

# Base money per route
# Money = ROUTE_MONEY_BASE * route + 5 * route^1.15
ROUTE_MONEY_BASE: int = 3

# Number of Pokemon defeats needed to "complete" a route
# Matches PokéClicker: GameConstants.ROUTE_KILLS_NEEDED = 10
ROUTE_KILLS_NEEDED: int = 10

# =============================================================================
# Catch Constants
# =============================================================================

# Base catch rate modifier
# Final catch rate = (pokemon_catch_rate^0.75) + pokeball_bonus
BASE_CATCH_RATE: float = 0.75

# Shiny chances (1 in N) - context based like Pokeclicker
SHINY_CHANCE_BATTLE: int = 8192  # Wild route encounters
SHINY_CHANCE_DUNGEON: int = 4096  # Dungeon encounters
SHINY_CHANCE_SAFARI: int = 1024  # Safari zone
SHINY_CHANCE_SHOP: int = 1024  # Shop purchases
SHINY_CHANCE_BREEDING: int = 1024  # Breeding/eggs
SHINY_CHANCE_FARM: int = 1024  # Farm wanderers
SHINY_CHANCE_REWARD: int = 1024  # Quest rewards
SHINY_CHANCE_STONE: int = 2048  # Evolution stone usage
SHINY_CHANCE_BATTLEFRONTIER: int = 1024  # Battle frontier

# Default (backwards compat)
SHINY_CHANCE: int = SHINY_CHANCE_BATTLE

# =============================================================================
# Experience Constants
# =============================================================================

# Base EXP modifier for party-wide distribution
# Each pokemon gets: base_exp * level * modifier / party_size
BASE_EXP_MODIFIER: float = 1.0

# Level scaling factor (Pokeclicker uses medium-slow curve)
# EXP to next level = EXP_SCALE_FACTOR * level^3
EXP_SCALE_FACTOR: float = 1.2
MAX_LEVEL: int = 100

# =============================================================================
# Starter Pokemon
# =============================================================================

# National dex IDs for starters (御三家) from each region
STARTERS: dict[int, list[int]] = {
    0: [1, 4, 7],  # Kanto: Bulbasaur, Charmander, Squirtle
    1: [152, 155, 158],  # Johto: Chikorita, Cyndaquil, Totodile
    2: [252, 255, 258],  # Hoenn: Treecko, Torchic, Mudkip
    3: [387, 390, 393],  # Sinnoh: Turtwig, Chimchar, Piplup
    4: [495, 498, 501],  # Unova: Snivy, Tepig, Oshawott
    5: [650, 653, 656],  # Kalos: Chespin, Fennekin, Froakie
    6: [722, 725, 728],  # Alola: Rowlet, Litten, Popplio
    7: [810, 813, 816],  # Galar: Grookey, Scorbunny, Sobble
    8: [906, 909, 912],  # Paldea: Sprigatito, Fuecoco, Quaxly
}

# Default starting region
DEFAULT_STARTER_REGION: int = 0  # Kanto

# =============================================================================
# Route Configuration
# =============================================================================

# Route ranges per region (min_route, max_route)
REGION_ROUTES: dict[int, tuple[int, int]] = {
    0: (1, 25),  # Kanto
    1: (26, 48),  # Johto
    2: (101, 134),  # Hoenn
    3: (201, 230),  # Sinnoh
    4: (301, 323),  # Unova
    5: (401, 422),  # Kalos
    6: (501, 517),  # Alola
    7: (601, 610),  # Galar
    8: (701, 715),  # Paldea
}

# =============================================================================
# Effort Points (EVs) Constants - Pokeclicker exact values
# =============================================================================

# EP to EV conversion ratio (from GameConstants.ts:443)
EP_EV_RATIO: int = 1000  # EVs = effort_points / EP_EV_RATIO

# Resistant threshold (EVs needed); from PartyPokemon.ts:94
RESISTANT_EV_THRESHOLD: int = 50

# Base EP yields per capture method (from GameConstants.ts:428-441)
BASE_EP_YIELD: int = 100  # Standard route catch = 0.1 EVs
WANDERER_EP_YIELD: int = 200  # Wandering Pokemon = 0.2 EVs
DUNGEON_EP_YIELD: int = 300  # Dungeon catch = 0.3 EVs
STONE_EP_YIELD: int = 1000  # Evolution stone = 1.0 EV
SHOPMON_EP_YIELD: int = 1000  # Shop purchase = 1.0 EV
SAFARI_EP_YIELD: int = 1000  # Safari catch = 1.0 EV
BOSS_EP_YIELD: int = 1000  # Dungeon boss = 1.0 EV
ROAMER_EP_YIELD: int = 5000  # Roaming Pokemon = 5.0 EVs

# EP modifiers (from GameConstants.ts:434-441)
SHINY_EP_MODIFIER: int = 5  # Shiny catch = 5x EP
SHADOW_EP_MODIFIER: int = 2  # Shadow catch = 2x EP
REPEATBALL_EP_MODIFIER: int = 5  # Repeat Ball = 5x EP
DUNGEON_EP_MODIFIER: int = 3  # Dungeon multiplier
DUNGEON_BOSS_EP_MODIFIER: int = 10  # Dungeon boss multiplier
ROAMER_EP_MODIFIER: int = 50  # Roaming multiplier

# =============================================================================
# Hatchery/Breeding Constants - Pokeclicker exact values
# =============================================================================

# Egg step calculation (from Breeding.ts:463-468)
# Steps = eggCycles * EGG_CYCLE_MULTIPLIER
EGG_CYCLE_MULTIPLIER: int = 40

# Max hatchery slots (start with 1, can buy up to 4)
MAX_EGG_SLOTS: int = 4
DEFAULT_EGG_SLOTS: int = 1

# Attack bonus from hatching (from Egg.hatch() lines 134-136)
# Each hatch: attackBonusPercent += BREEDING_ATTACK_BONUS + calcium
BREEDING_ATTACK_BONUS: int = 25  # Base % attack increase per hatch
BREEDING_SHINY_ATTACK_MULTIPLIER: int = 2  # Shiny hatch = 2x bonus

# Steps per battle (from Breeding.ts:208-210)
# progressEggsBattle: sqrt(route) steps per defeat
# Simplified for Discord: use fixed amounts
HATCHERY_STEPS_PER_BATTLE: int = 5  # Base steps per battle

# Egg slot cost (Quest Points) - from Breeding.ts:484-486
# Cost = 500 * slot_number
EGG_SLOT_BASE_COST: int = 500

# =============================================================================
# Pokeball Constants - Exact Pokeclicker values (ItemList.ts:88-103)
# =============================================================================

# Pokeball prices (currency type, price)
# Format: {ball_type: (price, currency_type)}
# Currency: 0=PokéDollar, 3=QuestPoint (from enums.py)
POKEBALL_PRICES: dict[int, tuple[int, int]] = {
    1: (100, 0),  # Poké Ball: 100 PokéDollar
    2: (500, 0),  # Great Ball: 500 PokéDollar
    3: (2000, 0),  # Ultra Ball: 2000 PokéDollar
    4: (2500, 3),  # Master Ball: 2500 Quest Points
}

# Pokeball catch bonuses (from Pokeballs.ts:17-20)
POKEBALL_CATCH_BONUS: dict[int, int] = {
    0: 0,  # None
    1: 0,  # Poké Ball: +0%
    2: 5,  # Great Ball: +5%
    3: 10,  # Ultra Ball: +10%
    4: 100,  # Master Ball: +100% (always catch)
}

# Starter Pokéballs (from Pokeballs.ts constructor, quantity = 25)
STARTER_POKEBALL_COUNT: int = 25

# =============================================================================
# Gym Constants
# =============================================================================

# Time limit for gym battles in seconds
GYM_TIME_LIMIT: int = 30
