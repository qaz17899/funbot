"""Parse Pokeclicker GymList.ts to JSON - FINAL VERSION with 100% accurate Badge IDs.

Uses official BadgeEnums.ts ordering from Pokeclicker source.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# 100% ACCURATE Badge Enum mapping from official BadgeEnums.ts
# TypeScript enum auto-increments from 0
BADGE_ENUMS = {
    # Line 2: 'None' = 0
    "None": 0,
    # Kanto (lines 4-16) = 1-13
    "Boulder": 1,
    "Cascade": 2,
    "Thunder": 3,
    "Rainbow": 4,
    "Soul": 5,
    "Marsh": 6,
    "Volcano": 7,
    "Earth": 8,
    "Elite_Lorelei": 9,
    "Elite_Bruno": 10,
    "Elite_Agatha": 11,
    "Elite_Lance": 12,
    "Elite_KantoChampion": 13,
    # Johto (lines 18-30) = 14-26
    "Zephyr": 14,
    "Hive": 15,
    "Plain": 16,
    "Fog": 17,
    "Storm": 18,
    "Mineral": 19,
    "Glacier": 20,
    "Rising": 21,
    "Elite_Will": 22,
    "Elite_Koga": 23,
    "Elite_Bruno2": 24,
    "Elite_Karen": 25,
    "Elite_JohtoChampion": 26,
    # Hoenn (lines 32-44) = 27-39
    "Stone": 27,
    "Knuckle": 28,
    "Dynamo": 29,
    "Heat": 30,
    "Balance": 31,
    "Feather": 32,
    "Mind": 33,
    "Rain": 34,
    "Elite_Sidney": 35,
    "Elite_Phoebe": 36,
    "Elite_Glacia": 37,
    "Elite_Drake": 38,
    "Elite_HoennChampion": 39,
    # Orange Islands (lines 46-50) = 40-44
    "Coral-Eye": 40,
    "Sea_Ruby": 41,
    "Spike_Shell": 42,
    "Jade_Star": 43,
    "Elite_OrangeChampion": 44,
    # Orre (lines 52-60) = 45-53 <- THIS ORDER IS KEY!
    "Elite_F_Disk": 45,
    "Elite_L_Disk": 46,
    "Elite_R_Disk": 47,
    "Elite_U_Disk": 48,
    "Elite_ColosseumLovrina": 49,
    "Elite_ColosseumSnattle": 50,
    "Elite_ColosseumGorigan": 51,
    "Elite_ColosseumArdos": 52,
    "Elite_ColosseumEldes": 53,
    # Sinnoh (lines 62-74) = 54-66
    "Coal": 54,
    "Forest": 55,
    "Relic": 56,
    "Cobble": 57,
    "Fen": 58,
    "Mine": 59,
    "Icicle": 60,
    "Beacon": 61,
    "Elite_Aaron": 62,
    "Elite_Bertha": 63,
    "Elite_Flint": 64,
    "Elite_Lucian": 65,
    "Elite_SinnohChampion": 66,
    # Unova (lines 76-88) = 67-79
    "Basic": 67,
    "Toxic": 68,
    "Insect": 69,
    "Bolt": 70,
    "Quake": 71,
    "Jet": 72,
    "Legend": 73,
    "Wave": 74,
    "Elite_Shauntal": 75,
    "Elite_Marshal": 76,
    "Elite_Grimsley": 77,
    "Elite_Caitlin": 78,
    "Elite_UnovaChampion": 79,
    # Kalos (lines 90-102) = 80-92
    "Bug": 80,
    "Cliff": 81,
    "Rumble": 82,
    "Plant": 83,
    "Voltage": 84,
    "Fairy": 85,
    "Psychic": 86,
    "Iceberg": 87,
    "Elite_Malva": 88,
    "Elite_Siebold": 89,
    "Elite_Wikstrom": 90,
    "Elite_Drasna": 91,
    "Elite_KalosChampion": 92,
    # Alola (lines 104-112) = 93-101
    "Melemele_Stamp": 93,
    "Akala_Stamp": 94,
    "Ula_Ula_Stamp": 95,
    "Poni_Stamp": 96,
    "Elite_Olivia": 97,
    "Elite_Acerola": 98,
    "Elite_Molayne": 99,
    "Elite_Kahili": 100,
    "Champion_Stamp": 101,
    # Magikarp Jump (lines 114-123) = 102-111
    "Friend_League": 102,
    "Quick_League": 103,
    "Heavy_League": 104,
    "Great_League": 105,
    "Fast_League": 106,
    "Luxury_League": 107,
    "Heal_League": 108,
    "Ultra_League": 109,
    "E4_League": 110,
    "Master_League": 111,
    # Galar (lines 125-138) = 112-125
    "Galar_Grass": 112,
    "Galar_Water": 113,
    "Galar_Fire": 114,
    "Galar_Fighting": 115,
    "Galar_Ghost": 116,
    "Galar_Fairy": 117,
    "Galar_Rock": 118,
    "Galar_Ice": 119,
    "Galar_Dark": 120,
    "Galar_Dragon": 121,
    "Elite_Marnie": 122,
    "Elite_Bede": 123,
    "Elite_Hop": 124,
    "Elite_GalarChampion": 125,
    # Armor (lines 140-143) = 126-129
    "Elite_ArmorPoison": 126,
    "Elite_ArmorPsychic": 127,
    "Elite_ArmorMatron": 128,
    "Elite_ArmorChampion": 129,
    # Crown (line 145) = 130
    "Elite_CrownChampion": 130,
    # Hisui (lines 147-152) = 131-136
    "Noble_Kleavor": 131,
    "Noble_Lilligant": 132,
    "Noble_Arcanine": 133,
    "Noble_Electrode": 134,
    "Noble_Avalugg": 135,
    "Azure": 136,
    # Paldea Victory Road (lines 154-167) = 137-150
    "Bug_Gym": 137,
    "Grass_Gym": 138,
    "Electric_Gym": 139,
    "Water_Gym": 140,
    "Normal_Gym": 141,
    "Ghost_Gym": 142,
    "Psychic_Gym": 143,
    "Ice_Gym": 144,
    "Elite_Rika": 145,
    "Elite_Poppy": 146,
    "Elite_Larry": 147,
    "Elite_Hassel": 148,
    "Elite_PaldeaChampion": 149,
    "Elite_Nemona": 150,
    # Starfall Street (lines 169-175) = 151-157
    "Dark_Star": 151,
    "Fire_Star": 152,
    "Poison_Star": 153,
    "Fairy_Star": 154,
    "Fighting_Star": 155,
    "Elite_Clavell": 156,
    "Elite_Penny": 157,
    # Path of Legends (lines 177-182) = 158-163
    "Rock_Titan": 158,
    "Flying_Titan": 159,
    "Steel_Titan": 160,
    "Ground_Titan": 161,
    "Dragon_Titan": 162,
    "Elite_Arven": 163,
    # The Way Home (lines 184-185) = 164-165
    "Scarlet": 164,
    "Violet": 165,
}


def get_region_from_badge_id(badge_id: int | None) -> int:
    """Derive region from badge ID ranges - based on official BadgeEnums.ts order."""
    if badge_id is None:
        return 0  # Default to Kanto

    # Official order from BadgeEnums.ts:
    if 1 <= badge_id <= 13:
        return 0  # Kanto
    if 14 <= badge_id <= 26:
        return 1  # Johto
    if 27 <= badge_id <= 39:
        return 2  # Hoenn
    if 40 <= badge_id <= 44:
        return 0  # Orange Islands (part of Kanto)
    if 45 <= badge_id <= 53:
        return 10  # Orre
    if 54 <= badge_id <= 66:
        return 3  # Sinnoh
    if 67 <= badge_id <= 79:
        return 4  # Unova
    if 80 <= badge_id <= 92:
        return 5  # Kalos
    if 93 <= badge_id <= 101:
        return 6  # Alola
    if 102 <= badge_id <= 111:
        return 6  # Magikarp Jump (Alola sub)
    if 112 <= badge_id <= 130:
        return 7  # Galar + DLC
    if 131 <= badge_id <= 136:
        return 8  # Hisui
    if 137 <= badge_id <= 165:
        return 9  # Paldea

    return 0  # Default


def find_matching_bracket(
    content: str, start: int, open_char: str = "(", close_char: str = ")"
) -> int:
    """Find the position of the matching closing bracket."""
    depth = 1
    pos = start
    in_string = False
    string_char = None

    while pos < len(content) and depth > 0:
        char = content[pos]

        # Handle string detection
        if char in "'\"`" and (pos == 0 or content[pos - 1] != "\\"):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None

        if not in_string:
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1

        pos += 1

    return pos - 1 if depth == 0 else -1


def extract_gym_args(gym_content: str) -> list[str]:
    """Extract constructor arguments using bracket counting."""
    args = []
    current_arg_start = 0
    depth = 0
    in_string = False
    string_char = None

    i = 0
    while i < len(gym_content):
        char = gym_content[i]

        # Handle strings
        if char in "'\"`" and (i == 0 or gym_content[i - 1] != "\\"):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None

        if not in_string:
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
            elif char == "," and depth == 0:
                args.append(gym_content[current_arg_start:i].strip())
                current_arg_start = i + 1

        i += 1

    # Last argument
    last_arg = gym_content[current_arg_start:].strip()
    if last_arg:
        args.append(last_arg)

    return args


def parse_pokemon_array(arr_content: str) -> list[dict]:
    """Parse GymPokemon array."""
    pokemon = []
    pattern = r"new\s+GymPokemon\s*\(\s*['\"]([^'\"]+)['\"],\s*(\d+),\s*(\d+)"
    for match in re.finditer(pattern, arr_content):
        pokemon.append(
            {
                "name": match.group(1).replace("\\'", "'"),
                "max_health": int(match.group(2)),
                "level": int(match.group(3)),
            }
        )
    return pokemon


def clean_string(s: str) -> str:
    """Clean string: handle concatenation and quotes."""
    s = s.strip()

    # Handle string concatenation: 'part1' + 'part2'
    if "' +" in s or "+ '" in s or '" +' in s or '+ "' in s:
        s = re.sub(r"['\"]\\s*\\+\\s*\\n?\\s*['\"]", "", s)

    # Remove outer quotes
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        s = s[1:-1]

    # Unescape
    s = s.replace("\\'", "'").replace('\\"', '"').replace("\\n", "\n")

    return s


def parse_badge(badge_str: str) -> tuple[str | None, int | None]:
    """Parse badge enum to name and ID."""
    badge_str = badge_str.strip()

    # Match: BadgeEnums.Name or BadgeEnums['Name']
    match = re.match(r"BadgeEnums\.(\w+)", badge_str)
    if match:
        name = match.group(1)
        return name, BADGE_ENUMS.get(name)

    match = re.match(r"BadgeEnums\[['\"]([\w\-]+)['\"]\]", badge_str)
    if match:
        name = match.group(1)
        return name, BADGE_ENUMS.get(name)

    return None, None


def parse_requirement_tree(req_str: str) -> list[dict]:
    """Parse requirements array recursively."""
    requirements = []
    req_str = req_str.strip()

    if not req_str or req_str == "[]":
        return requirements

    # Remove outer brackets
    if req_str.startswith("[") and req_str.endswith("]"):
        req_str = req_str[1:-1].strip()

    if not req_str:
        return requirements

    # Split by top-level commas
    parts = []
    depth = 0
    current = ""
    in_string = False
    string_char = None

    for i, char in enumerate(req_str):
        if char in "'\"`" and (i == 0 or req_str[i - 1] != "\\"):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False

        if not in_string:
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append(current.strip())
                current = ""
                continue

        current += char

    if current.strip():
        parts.append(current.strip())

    # Parse each requirement
    for part in parts:
        req = parse_single_requirement(part.strip())
        if req:
            requirements.append(req)

    return requirements


def parse_single_requirement(req_str: str) -> dict | None:
    """Parse a single requirement."""
    if not req_str.startswith("new "):
        return None

    # Extract type
    type_match = re.match(r"new\s+(\w+)\s*\(", req_str)
    if not type_match:
        return None

    req_type = type_match.group(1)

    # Find the arguments
    paren_start = req_str.find("(")
    if paren_start == -1:
        return None

    paren_end = find_matching_bracket(req_str, paren_start + 1, "(", ")")
    if paren_end == -1:
        return None

    args_str = req_str[paren_start + 1 : paren_end]

    result = {"type": req_type, "params": {}, "children": []}

    # Parse based on type
    if req_type == "RouteKillRequirement":
        match = re.match(r"(\d+),\s*GameConstants\.Region\.(\w+),\s*(\d+)", args_str)
        if match:
            result["params"] = {
                "amount": int(match.group(1)),
                "region": match.group(2),
                "route": int(match.group(3)),
            }

    elif req_type == "GymBadgeRequirement":
        badge_name, badge_id = parse_badge(args_str.split(",")[0])
        result["params"] = {"badge": badge_name, "badge_id": badge_id}

    elif req_type == "TemporaryBattleRequirement":
        match = re.match(r"['\"]([^'\"]+)['\"]", args_str)
        if match:
            result["params"] = {"battle": match.group(1)}

    elif req_type == "ClearDungeonRequirement":
        # Use (?:[^'\\]|\\.)* to handle escaped quotes like Team Rocket\'s Hideout
        match = re.match(
            r"(\d+),\s*(?:GameConstants\.)?getDungeonIndex\s*\(\s*'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"",
            args_str,
        )
        if match:
            dungeon_name = match.group(2) or match.group(3)
            # Unescape the string
            dungeon_name = dungeon_name.replace("\\'", "'").replace('\\"', '"')
            result["params"] = {"clears": int(match.group(1)), "dungeon": dungeon_name}

    elif req_type == "QuestLineCompletedRequirement":
        # Handle escaped quotes like Bill\'s Errand
        match = re.match(r"'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"", args_str)
        if match:
            quest_name = match.group(1) or match.group(2)
            quest_name = quest_name.replace("\\'", "'").replace('\\"', '"')
            result["params"] = {"quest": quest_name}

    elif req_type == "QuestLineStepCompletedRequirement":
        match = re.match(r"'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\",\s*(\d+)", args_str)
        if match:
            quest_name = match.group(1) or match.group(2)
            quest_name = quest_name.replace("\\'", "'").replace('\\"', '"')
            step = int(match.group(3)) if match.group(3) else 0
            result["params"] = {"quest": quest_name, "step": step}

    elif req_type in ("MultiRequirement", "OneFromManyRequirement"):
        # Find inner array
        arr_match = re.search(r"\[(.*)\]", args_str, re.DOTALL)
        if arr_match:
            result["children"] = parse_requirement_tree("[" + arr_match.group(1) + "]")

    else:
        # Generic: store raw
        result["params"] = {"raw": args_str[:200]}

    return result


def parse_gyms(content: str) -> list[dict]:
    """Parse all gyms from GymList.ts."""
    gyms = []

    # Find all gym definitions - supports ['Name'] (with escapes), .Name, and inline comments
    # Note: (?:[^'\\]|\\.)+ handles escaped characters like \'
    pattern = r"GymList(?:\['((?:[^'\\]|\\.)*)'\]|\"((?:[^\"\\]|\\.)*)\"|\.([a-zA-Z0-9_]+))\s*=\s*new\s+Gym\s*\("

    for match in re.finditer(pattern, content):
        # group(1) is ['Name'], group(2) is .Name - take whichever matched
        town = match.group(1) or match.group(2) or match.group(3)
        gym_start = match.end()

        # Find the end of this Gym() call
        gym_end = find_matching_bracket(content, gym_start, "(", ")")
        if gym_end == -1:
            print(f"Warning: Could not find end of Gym for {town}")
            continue

        gym_content = content[gym_start:gym_end]

        # Strip inline comments (// ...) from TypeScript before parsing
        # This handles cases like: new Gym( //comment
        gym_content = re.sub(r"//[^\n]*\n", "\n", gym_content)

        # Extract arguments
        args = extract_gym_args(gym_content)

        if len(args) < 6:
            print(f"Warning: Not enough args for {town}: {len(args)} args")
            continue

        gym_data = {
            "town": town,
            "leader": clean_string(args[0]) if args[0] else None,
            "town_arg": clean_string(args[1]) if len(args) > 1 else town,
            "pokemon": parse_pokemon_array(args[2]) if len(args) > 2 else [],
            "badge": None,
            "badge_id": None,
            "money_reward": None,
            "defeat_message": None,
            "requirements": [],
            "region": 0,  # Will be set from badge
            "is_elite": "Elite" in town or "Champion" in town,
        }

        # Badge (arg 3)
        if len(args) > 3:
            badge_name, badge_id = parse_badge(args[3])
            gym_data["badge"] = badge_name
            gym_data["badge_id"] = badge_id

        # Money reward (arg 4)
        if len(args) > 4:
            try:
                gym_data["money_reward"] = int(args[4].strip())
            except ValueError:
                pass

        # Defeat message (arg 5)
        if len(args) > 5:
            gym_data["defeat_message"] = clean_string(args[5])

        # Requirements (arg 6)
        if len(args) > 6:
            gym_data["requirements"] = parse_requirement_tree(args[6])

        # Derive region from badge ID
        gym_data["region"] = get_region_from_badge_id(gym_data["badge_id"])

        # Remove temporary field
        del gym_data["town_arg"]

        gyms.append(gym_data)

    return gyms


def main() -> None:
    """Parse GymList.ts and output JSON."""
    # Use pre-cleaned file (comments stripped) for easier parsing
    gym_list_path = Path(__file__).parent / "GymList_cleaned.ts"

    # If cleaned version doesn't exist, fall back to original
    if not gym_list_path.exists():
        gym_list_path = (
            Path(__file__).parent.parent
            / "reference"
            / "pokeclicker-develop"
            / "src"
            / "scripts"
            / "gym"
            / "GymList.ts"
        )

    if not gym_list_path.exists():
        print(f"Error: {gym_list_path} not found")
        return

    content = gym_list_path.read_text(encoding="utf-8")
    gyms = parse_gyms(content)

    print(f"Parsed {len(gyms)} gyms")

    # Stats by region
    region_counts: dict[int, int] = {}
    for g in gyms:
        r = g["region"]
        region_counts[r] = region_counts.get(r, 0) + 1

    for r in sorted(region_counts.keys()):
        print(f"  Region {r}: {region_counts[r]} gyms")

    # Check for issues
    empty_req = sum(1 for g in gyms if not g["requirements"])
    null_badge = sum(1 for g in gyms if g["badge_id"] is None)
    print(f"  Empty requirements: {empty_req}")
    print(f"  Null badge_id: {null_badge}")

    # Output to JSON file
    output_path = Path(__file__).parent / "gyms_data.json"
    output_path.write_text(json.dumps(gyms, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Output written to {output_path}")


if __name__ == "__main__":
    main()
