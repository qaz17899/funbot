"""Shared UI utilities for Pokemon module.

Contains emoji mappings and other UI helpers used across multiple cogs.
Discord custom emoji IDs are used for pokeballs, currencies, and items.
"""

from __future__ import annotations

__all__ = (
    "CURRENCY_EMOJI_IDS",
    "POKEBALL_EMOJI_IDS",
    "TYPE_EMOJIS",
    "get_ball_emoji",
    "get_currency_emoji",
    "get_type_emoji",
)


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

# Pokeball enum value to emoji name mapping
BALL_ENUM_TO_NAME: dict[int, str] = {
    0: "None",
    1: "Pokeball",
    2: "Greatball",
    3: "Ultraball",
    4: "Masterball",
}


def get_ball_emoji(ball_id: int) -> str:
    """Get Discord custom emoji for Pokeball type."""
    name = BALL_ENUM_TO_NAME.get(ball_id, "Pokeball")
    emoji_id = POKEBALL_EMOJI_IDS[name]
    return f"<:{name}:{emoji_id}>"


# Discord custom emoji IDs for currencies
CURRENCY_EMOJI_IDS: dict[str, int] = {
    "money": 1449471872482672830,
    "battlePoint": 1449471848046788639,
    "dungeonToken": 1449471868103819446,
    "questPoint": 1449471874902921267,
    "farmPoint": 1449471869454385235,
    "contestToken": 1449471864672878682,
    "diamond": 1449471866220581084,
    "coinyellow": 1449471860738887752,
    "coinwhite": 1449471859123945584,
    "coinred": 1449471857395896463,
    "coinpurple": 1449471855873364050,
    "coinorange": 1449471854145306647,
    "coingreen": 1449471852589355122,
    "coingray": 1449471851133927474,
    "coinblue": 1449471849770520647,
}


def get_currency_emoji(currency: str) -> str:
    """Get Discord custom emoji for currency type."""
    emoji_id = CURRENCY_EMOJI_IDS.get(currency, CURRENCY_EMOJI_IDS["money"])
    return f"<:{currency}:{emoji_id}>"


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
