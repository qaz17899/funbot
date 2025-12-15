"""Shared UI utilities for Pokemon module.

Contains emoji mappings and other UI helpers used across multiple cogs.
Discord custom emoji IDs are used for pokeballs, currencies, and items.

Key naming conventions:
- Currency keys use snake_case to match Python conventions and Enum names
- Pokeball keys use PascalCase to match Discord emoji names
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

import discord

from funbot.pokemon.constants.enums import Currency, LootTier, Pokeball, Region
from funbot.pokemon.constants.game_constants import ROUTE_KILLS_NEEDED

if TYPE_CHECKING:
    from funbot.db.models.pokemon.route_data import RouteData

__all__ = (
    # Constants (alphabetical)
    "BADGE_EMOJI_IDS",
    "CURRENCY_EMOJI_IDS",
    "DUNGEON_STATUS_EMOJI",
    "DUNGEON_TILE_EMOJI",
    "GEM_EMOJI_IDS",
    "GYM_STATUS_EMOJI",
    "LOOT_TIER_EMOJIS",
    "POKEBALL_DISPLAY_NAMES",
    "POKEBALL_EMOJI_IDS",
    "POKECLICKER_BADGE_BASE_URL",
    "POKECLICKER_NPC_BASE_URL",
    "REGION_DISPLAY_NAMES",
    "ROUTE_STATUS_EMOJI",
    "TYPE_EMOJIS",
    # Classes
    "Emoji",
    # Functions (alphabetical)
    "build_progress_bar",
    "format_currency",
    "format_dungeon_choice",
    "format_gym_choice",
    "format_route_choice",
    "get_badge_emoji",
    "get_badge_image_url",
    "get_ball_emoji",
    "get_ball_partial_emoji",
    "get_currency_emoji",
    "get_gem_emoji",
    "get_leader_image_url",
    "get_loot_tier_emoji",
    "get_pokeball_name",
    "get_type_emoji",
)

# Pokeclicker asset URLs (moved from GymService)
POKECLICKER_NPC_BASE_URL = "https://raw.githubusercontent.com/pokeclicker/pokeclicker/develop/src/assets/images/npcs"
POKECLICKER_BADGE_BASE_URL = "https://raw.githubusercontent.com/pokeclicker/pokeclicker/develop/src/assets/images/badges"


class Emoji:
    """Common emoji constants for UI consistency."""

    # Status/Success indicators
    CHECK = "✅"
    CROSS = "❌"
    WARNING = "⚠️"

    # Pokemon-specific
    SHINY = "✨"
    POKERUS = "🦠"
    EGG = "🥚"
    HATCH = "🐣"

    # Actions
    BATTLE = "⚔️"
    CATCH = "🎯"
    MAP = "🗺️"
    EXP = "⭐"

    # Gender
    MALE = "♂"
    FEMALE = "♀"

    # Misc
    PROGRESS = "█"
    PROGRESS_EMPTY = "░"


# Pokemon type to emoji mapping (all 18 types)
TYPE_EMOJIS: dict[int, str] = {
    1: "⚪",  # Normal
    2: "🔥",  # Fire
    3: "💧",  # Water
    4: "⚡",  # Electric
    5: "🌿",  # Grass
    6: "❄️",  # Ice
    7: "👊",  # Fighting
    8: "☠️",  # Poison
    9: "🏔️",  # Ground
    10: "🪽",  # Flying
    11: "🔮",  # Psychic
    12: "🐛",  # Bug
    13: "🪨",  # Rock
    14: "👻",  # Ghost
    15: "🐉",  # Dragon
    16: "🌑",  # Dark
    17: "⚙️",  # Steel
    18: "🧚",  # Fairy
}


def get_type_emoji(type_id: int) -> str:
    """Get emoji for Pokemon type ID."""
    return TYPE_EMOJIS.get(type_id, "⚪")


# Route Status Emojis (used by RouteStatusService)
ROUTE_STATUS_EMOJI: dict[int, str] = {
    0: "🔒",  # LOCKED
    1: "⚔️",  # INCOMPLETE
    2: "📋",  # QUEST_AT_LOCATION
    3: "🆕",  # UNCAUGHT_POKEMON
    4: "✨",  # UNCAUGHT_SHINY
    5: "🌈",  # COMPLETED
}

# Dungeon Status Emojis (SSOT for dungeon list views and autocomplete)
DUNGEON_STATUS_EMOJI: dict[str, str] = {
    "LOCKED": "🔒",
    "AVAILABLE": "⚔️",
    "COMPLETED": "✅",
}

# Gym Status Emojis (SSOT for gym list views and autocomplete)
GYM_STATUS_EMOJI: dict[str, str] = {
    "AVAILABLE": "⚔️",  # Default state (Available to challenge)
    "COMPLETED": "🏅",  # Has badge
}

# Dungeon Tile Emojis (used by DungeonMapView)
DUNGEON_TILE_EMOJI: dict[str, str] = {
    "entrance": "🚪",
    "enemy": "👾",
    "chest": "📦",
    "boss": "👹",
    "empty": "⬜",
    "ladder": "🪜",
    "fog": "⬛",  # Unrevealed tile
    "player": "🧑",  # Player position
}

# Loot Tier Emojis
LOOT_TIER_EMOJIS: dict[LootTier, str] = {
    LootTier.COMMON: "⚪",
    LootTier.RARE: "🔵",
    LootTier.EPIC: "🟣",
    LootTier.LEGENDARY: "🟡",
    LootTier.MYTHIC: "🔴",
}

# Region Display Names (centralized, with localized names)
REGION_DISPLAY_NAMES: dict[int, str] = {
    Region.KANTO: "關都 Kanto",
    Region.JOHTO: "城都 Johto",
    Region.HOENN: "豐緣 Hoenn",
    Region.SINNOH: "神奧 Sinnoh",
    Region.UNOVA: "合眾 Unova",
    Region.KALOS: "卡洛斯 Kalos",
    Region.ALOLA: "阿羅拉 Alola",
    Region.GALAR: "伽勒爾 Galar",
    Region.PALDEA: "帕底亞 Paldea",
}

# Pokeball Display Names
POKEBALL_DISPLAY_NAMES: dict[int, str] = {
    Pokeball.NONE: "None",
    Pokeball.POKEBALL: "Poké Ball",
    Pokeball.GREATBALL: "Great Ball",
    Pokeball.ULTRABALL: "Ultra Ball",
    Pokeball.MASTERBALL: "Master Ball",
}


def get_pokeball_name(ball: int | Pokeball) -> str:
    """Get display name for a Pokeball type.

    Args:
        ball: Pokeball enum or integer value

    Returns:
        Display name string (e.g., "Poké Ball")
    """
    ball_val = int(ball)
    return POKEBALL_DISPLAY_NAMES.get(ball_val, "Unknown Ball")


def get_loot_tier_emoji(tier: str | LootTier) -> str:
    """Get emoji for loot tier.

    Args:
        tier: LootTier enum or string value

    Returns:
        Emoji string
    """
    if isinstance(tier, str):
        try:
            tier = LootTier(tier.lower())
        except ValueError:
            return "⚪"
    return LOOT_TIER_EMOJIS.get(tier, "⚪")


def build_progress_bar(
    current: int | float,
    maximum: int | float,
    width: int = 16,
    show_values: bool = True,
) -> str:
    """Build a visual progress/health bar.

    Centralized function for all progress bar rendering.

    Args:
        current: Current value
        maximum: Maximum value
        width: Number of characters in bar
        show_values: Whether to show "current/max" text

    Returns:
        Progress bar string like "████████░░░░░░░░ 432/693"
    """
    if maximum <= 0:
        bar = Emoji.PROGRESS_EMPTY * width
        return f"{bar} 0/0" if show_values else bar

    percent = max(0.0, min(1.0, current / maximum))
    filled = int(percent * width)
    empty = width - filled

    bar = Emoji.PROGRESS * filled + Emoji.PROGRESS_EMPTY * empty

    if not show_values:
        return bar

    # Format numbers with commas for integers
    if isinstance(current, int) and isinstance(maximum, int):
        return f"{bar} {current:,}/{maximum:,}"
    return f"{bar} {current:.1f}/{maximum:.1f}"


def format_currency(amount: int, currency: str | Currency) -> str:
    """Format currency amount with emoji and thousands separator.

    Centralized function for consistent currency display across all Views.

    Args:
        amount: The amount of currency
        currency: Currency enum or string key

    Returns:
        Formatted string (e.g., "1,000 💰")
    """
    emoji = get_currency_emoji(currency)
    return f"{amount:,} {emoji}"


# Discord custom emoji IDs for pokeballs
POKEBALL_EMOJI_IDS: dict[str, int] = {
    "None": 1449471351818551437,
    "Pokeball": 1449471357242052813,
    "Greatball": 1449471336874250440,
    "Ultraball": 1449471372874223688,
    "Masterball": 1449471346030678096,
    "Pokeballshiny": 1449471359007719606,
    "Premierball": 1449471360580456468,
    "Luxuryball": 1449471344415871157,
    "Quickball": 1449471362174550076,
    "Repeatball": 1449471364296867860,
    "Timerball": 1449471371280121876,
    "Nestball": 1449471349826519283,
    "Diveball": 1449471325470195712,
    "Duskball": 1449471327940378896,
    "Loveball": 1449471341098172587,
    "Moonball": 1449471348127826073,
    "Beastball": 1449471323939278950,
    "Fastball": 1449471334961774824,
    "Lureball": 1449471342847070308,
    "Safariball": 1449471367006261429,
    "Sportball": 1449471369384562951,
    "GSball": 1449471338749362197,
    "Parkball": 1449471353416585497,
    "Pinkball": 1449471354943307787,
    "Rocketball": 1449471365659885679,
}

# Pokeball enum value to emoji name mapping (Maps Enum to POKEBALL_EMOJI_IDS keys)
BALL_ENUM_TO_NAME: dict[int, str] = {
    Pokeball.NONE: "None",
    Pokeball.POKEBALL: "Pokeball",
    Pokeball.GREATBALL: "Greatball",
    Pokeball.ULTRABALL: "Ultraball",
    Pokeball.MASTERBALL: "Masterball",
}


def get_ball_emoji(ball: int | Pokeball) -> str:
    """Get Discord custom emoji for Pokeball type.

    Args:
        ball: Pokeball enum or integer value

    Returns:
        Discord custom emoji string
    """
    ball_val = int(ball)
    name = BALL_ENUM_TO_NAME.get(ball_val, "Pokeball")
    emoji_id = POKEBALL_EMOJI_IDS.get(name, POKEBALL_EMOJI_IDS["Pokeball"])
    return f"<:{name}:{emoji_id}>"


def get_ball_partial_emoji(ball: int | Pokeball) -> discord.PartialEmoji:
    """Get Discord PartialEmoji for Pokeball type.

    Encapsulates emoji ID lookup - View layer doesn't need to know about IDs.

    Args:
        ball: Pokeball enum or integer value

    Returns:
        discord.PartialEmoji object for use in SelectOption, etc.
    """
    ball_val = int(ball)
    name = BALL_ENUM_TO_NAME.get(ball_val, "Pokeball")
    emoji_id = POKEBALL_EMOJI_IDS.get(name, POKEBALL_EMOJI_IDS["Pokeball"])
    return discord.PartialEmoji(name=name, id=emoji_id)


# Discord custom emoji IDs for currencies
# Keys normalized to snake_case to match Enum names and Python conventions
CURRENCY_EMOJI_IDS: dict[str, int] = {
    # Primary currencies (match Currency enum)
    "money": 1449471872482672830,
    "pokedollar": 1449471872482672830,  # Alias for money
    "dungeon_token": 1449471868103819446,
    "battle_point": 1449471848046788639,
    "quest_point": 1449471874902921267,
    "farm_point": 1449471869454385235,
    "contest_token": 1449471864672878682,
    "diamond": 1449471866220581084,
    # Coin variants
    "coinyellow": 1449471860738887752,
    "coinwhite": 1449471859123945584,
    "coinred": 1449471857395896463,
    "coinpurple": 1449471855873364050,
    "coinorange": 1449471854145306647,
    "coingreen": 1449471852589355122,
    "coingray": 1449471851133927474,
    "coinblue": 1449471849770520647,
}

# Currency enum to emoji key mapping
_CURRENCY_ENUM_TO_KEY: dict[Currency, str] = {
    Currency.POKEDOLLAR: "money",
    Currency.DUNGEON_TOKEN: "dungeon_token",
    Currency.BATTLE_POINT: "battle_point",
    Currency.QUEST_POINT: "quest_point",
}


def get_currency_emoji(currency: str | Currency) -> str:
    """Get Discord custom emoji for currency type.

    Args:
        currency: Currency enum or string key (snake_case)

    Returns:
        Discord custom emoji string
    """
    if isinstance(currency, Currency):
        key = _CURRENCY_ENUM_TO_KEY.get(currency, "money")
    else:
        key = currency

    emoji_id = CURRENCY_EMOJI_IDS.get(key, CURRENCY_EMOJI_IDS["money"])
    return f"<:{key}:{emoji_id}>"


# Discord custom emoji IDs for type gems (18 types)
GEM_EMOJI_IDS: dict[str, int] = {
    "NormalGem": 1449472687545258164,
    "FireGem": 1449472677004968106,
    "WaterGem": 1449472697770971226,
    "ElectricGem": 1449472672504348783,
    "GrassGem": 1449472681664581632,
    "IceGem": 1449472685619941652,
    "FightingGem": 1449472675574452366,
    "PoisonGem": 1449472689088762030,
    "GroundGem": 1449472683149623508,
    "FlyingGem": 1449472678380441831,
    "PsychicGem": 1449472690732925109,
    "BugGem": 1449472667450343608,
    "RockGem": 1449472693450703150,
    "GhostGem": 1449472680012288082,
    "DragonGem": 1449472671023759390,
    "DarkGem": 1449472668998041792,
    "SteelGem": 1449472695216378158,
    "FairyGem": 1449472673993199717,
}

# Type ID to gem name mapping
TYPE_TO_GEM: dict[int, str] = {
    1: "NormalGem",
    2: "FireGem",
    3: "WaterGem",
    4: "ElectricGem",
    5: "GrassGem",
    6: "IceGem",
    7: "FightingGem",
    8: "PoisonGem",
    9: "GroundGem",
    10: "FlyingGem",
    11: "PsychicGem",
    12: "BugGem",
    13: "RockGem",
    14: "GhostGem",
    15: "DragonGem",
    16: "DarkGem",
    17: "SteelGem",
    18: "FairyGem",
}


def get_gem_emoji(type_id: int) -> str:
    """Get Discord custom emoji for type gem."""
    name = TYPE_TO_GEM.get(type_id, "NormalGem")
    emoji_id = GEM_EMOJI_IDS[name]
    return f"<:{name}:{emoji_id}>"


# Discord custom emoji IDs for badges (organized by region)
BADGE_EMOJI_IDS: dict[str, int] = {
    # Kanto (8 gyms)
    "Boulder": 1449473395191185439,
    "Cascade": 1449473400656629870,
    "Thunder": 1449473563672186972,
    "Rainbow": 1449473542583353406,
    "Soul": 1449473555564724407,
    "Marsh": 1449473497649774744,
    "Volcano": 1449473576985039030,
    "Earth": 1449473424224157707,
    # Johto (8 gyms)
    "Zephyr": 1449473586019434517,
    "Hive": 1449473478502645892,
    "Plain": 1449473526460317917,
    "Fog": 1449473440007585803,
    "Storm": 1449473562065764513,
    "Mineral": 1449473513315368960,
    "Glacier": 1449473467266105425,
    "Rising": 1449473545632481370,
    # Hoenn (8 gyms)
    "Stone": 1449473560660938805,
    "Knuckle": 1449473490770985061,
    "Dynamo": 1449473421128765441,
    "Heat": 1449473474430243056,
    "Balance": 1449473387201036369,
    "Feather": 1449473431774167080,
    "Mind": 1449473501152153842,
    "Rain": 1449473540977070250,
    # Orange League
    "CoralEye": 1449473408977862656,
    "Sea_Ruby": 1449473553282891897,
    "Spike_Shell": 1449473557305360655,
    "Jade_Star": 1449473487600095376,
    # Sinnoh (8 gyms)
    "Coal": 1449473405312307200,
    "Forest": 1449473442062798919,
    "Relic": 1449473543942308083,
    "Cobble": 1449473406826446958,
    "Fen": 1449473433183195236,
    "Mine": 1449473502498258996,
    "Icicle": 1449473484118822974,
    "Beacon": 1449473390577713324,
    # Unova (8 gyms)
    "Basic": 1449473388975231197,
    "Toxic": 1449473565739978842,
    "Insect": 1449473486010716160,
    "Bolt": 1449473392519413874,
    "Quake": 1449473537575354559,
    "Jet": 1449473488959180991,
    "Legend": 1449473492599832729,
    "Wave": 1449473583763165365,
    # Kalos (8 gyms)
    "Bug": 1449473396751601850,
    "Cliff": 1449473403798028358,
    "Rumble": 1449473549311148055,
    "Plant": 1449473528582635530,
    "Voltage": 1449473580738936934,
    "Fairy": 1449473427147849970,
    "Psychic": 1449473534228168815,
    "Iceberg": 1449473482369925222,
    # Alola (Island Stamps)
    "Melemele_Stamp": 1449473499487010948,
    "Akala_Stamp": 1449473383933808820,
    "Ula_Ula_Stamp": 1449473569829687429,
    "Poni_Stamp": 1449473532483604500,
    "Champion_Stamp": 1449473402040483971,
    # Magikarp Jump Leagues
    "Friend_League": 1449473446345052221,
    "Quick_League": 1449473539412459522,
    "Heavy_League": 1449473476552298517,
    "Great_League": 1449473469971435723,
    "Fast_League": 1449473430176006215,
    "Luxury_League": 1449473494227222624,
    "Heal_League": 1449473473012568134,
    "Ultra_League": 1449473571612266710,
    "E4_League": 1449473422521401394,
    "Master_League": 1449473495147774744,
    # Galar (10 gyms)
    "Galar_Grass": 1449473458697146388,
    "Galar_Water": 1449473463566860398,
    "Galar_Fire": 1449473455048228874,
    "Galar_Fighting": 1449473452401758238,
    "Galar_Ghost": 1449473457099374682,
    "Galar_Fairy": 1449473451034284152,
    "Galar_Rock": 1449473461935276134,
    "Galar_Ice": 1449473460127404202,
    "Galar_Dark": 1449473447926436001,
    "Galar_Dragon": 1449473449427996682,
    # Hisui (Nobles)
    "Noble_Kleavor": 1449473520626040974,
    "Noble_Lilligant": 1449473522949947623,
    "Noble_Arcanine": 1449473515383292027,
    "Noble_Electrode": 1449473518482751528,
    "Noble_Avalugg": 1449473517019201648,
    "Azure": 1449473385376645141,
    # Paldea Gyms
    "Bug_Gym": 1449473398270070805,
    "Grass_Gym": 1449473468578926743,
    "Electric_Gym": 1449473425784700928,
    "Water_Gym": 1449473582559268984,
    "Normal_Gym": 1449473524547846156,
    "Ghost_Gym": 1449473465538318397,
    "Psychic_Gym": 1449473535889117255,
    "Ice_Gym": 1449473480780284114,
    # Paldea Starfall Street
    "Dark_Star": 1449473411041726464,
    "Fire_Star": 1449473436849017073,
    "Poison_Star": 1449473530264686603,
    "Fairy_Star": 1449473428724781076,
    "Fighting_Star": 1449473434818969762,
    # Paldea Path of Legends (Titans)
    "Rock_Titan": 1449473547134308436,
    "Flying_Titan": 1449473438568939692,
    "Steel_Titan": 1449473558752530633,
    "Ground_Titan": 1449473471351357562,
    "Dragon_Titan": 1449473419564421120,
    # Paldea Story
    "Scarlet": 1449473551114436689,
    "Violet": 1449473574745145474,
    # Misc
    "Unknown": 1449473573017223301,
    "Trio": 1449473568068079708,
    "Freeze": 1449473443803435111,
}


def get_badge_emoji(badge_name: str) -> str:
    """Get Discord custom emoji for gym badge."""
    emoji_id = BADGE_EMOJI_IDS.get(badge_name, BADGE_EMOJI_IDS["Boulder"])
    return f"<:{badge_name}:{emoji_id}>"


# =============================================================================
# UI Formatting Functions (moved from Service layer for separation of concerns)
# =============================================================================


def get_leader_image_url(leader_name: str) -> str:
    """Get the URL for a gym leader's image.

    Moved from GymService to decouple Service from UI assets.

    Args:
        leader_name: Name of the gym leader (e.g., "Brock")

    Returns:
        URL to the leader's image on Pokeclicker GitHub
    """
    encoded_name = quote(leader_name)
    return f"{POKECLICKER_NPC_BASE_URL}/{encoded_name}.png"


def get_badge_image_url(badge_name: str) -> str:
    """Get the URL for a badge's image.

    Moved from GymService to decouple Service from UI assets.

    Args:
        badge_name: Name of the badge (e.g., "Boulder")

    Returns:
        URL to the badge's image on Pokeclicker GitHub
    """
    return f"{POKECLICKER_BADGE_BASE_URL}/{badge_name}.svg"


def format_route_choice(route: RouteData, status: int, kills: int) -> tuple[str, int]:
    """Format a route for autocomplete display.

    Moved from RouteStatusService to decouple Service from UI.

    Args:
        route: The route data
        status: RouteStatus integer value (0-5)
        kills: Kill count on this route

    Returns:
        Tuple of (display_name, route_number) for app_commands.Choice
    """
    emoji = ROUTE_STATUS_EMOJI.get(status, "❓")
    kills_display = f"({kills}/{ROUTE_KILLS_NEEDED})"

    # Add status-specific suffix
    # RouteStatus: 5=COMPLETED, 3=UNCAUGHT_POKEMON, 4=UNCAUGHT_SHINY
    suffix = ""
    if status == 5:  # COMPLETED
        suffix = " ✓"
    elif status == 3:  # UNCAUGHT_POKEMON
        suffix = " | 新"
    elif status == 4:  # UNCAUGHT_SHINY
        suffix = " | 閃"

    # Discord autocomplete has 100 char limit for name
    display = f"{emoji} {route.name} {kills_display}{suffix}"
    if len(display) > 100:
        display = display[:97] + "..."

    return display, route.number


def format_gym_choice(
    gym_name: str, gym_leader: str, is_elite: bool, has_badge: bool
) -> str:
    """Format a gym for autocomplete display.

    Args:
        gym_name: Name of the gym/town
        gym_leader: Name of the gym leader
        is_elite: Whether this is an Elite Four member
        has_badge: Whether player has the badge

    Returns:
        Display name string for app_commands.Choice
    """
    status = (
        GYM_STATUS_EMOJI["COMPLETED"] if has_badge else GYM_STATUS_EMOJI["AVAILABLE"]
    )
    elite_prefix = "👑 " if is_elite else ""

    display = f"{status} {elite_prefix}{gym_name} - {gym_leader}"
    if len(display) > 100:
        display = display[:97] + "..."

    return display


def format_dungeon_choice(dungeon_name: str, clears: int) -> str:
    """Format a dungeon for autocomplete display.

    Args:
        dungeon_name: Name of the dungeon
        clears: Number of times cleared

    Returns:
        Display name string for app_commands.Choice
    """
    status = (
        DUNGEON_STATUS_EMOJI["COMPLETED"]
        if clears > 0
        else DUNGEON_STATUS_EMOJI["AVAILABLE"]
    )
    suffix = f" ({clears}次)" if clears > 0 else ""

    display = f"{status} {dungeon_name}{suffix}"
    if len(display) > 100:
        display = display[:97] + "..."

    return display
