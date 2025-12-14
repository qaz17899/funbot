"""Parse Pokeclicker Dungeon.ts to JSON - FINAL VERSION.

Uses official RegionDungeons mapping from GameConstants.ts for 100% accurate region assignment.
Also handles dungeons not in the official list (events, etc.) by marking them as region -1.

Usage:
    python scripts/parse_dungeons.py
    # Outputs: scripts/dungeons_data.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Official dungeon-region mapping from GameConstants.ts (lines 1540-1804)
# This is extracted directly from the source for 100% accuracy
DUNGEON_REGIONS = {
    # Kanto (region 0) - 23 dungeons
    "Viridian Forest": 0,
    "Mt. Moon": 0,
    "Diglett's Cave": 0,
    "Rock Tunnel": 0,
    "Rocket Game Corner": 0,
    "Pokémon Tower": 0,
    "Silph Co.": 0,
    "Power Plant": 0,
    "Seafoam Islands": 0,
    "Pokémon Mansion": 0,
    "Mt. Ember Summit": 0,
    "Berry Forest": 0,
    "New Island": 0,
    "Victory Road": 0,
    "Cerulean Cave": 0,
    "Ruby Path": 0,
    "Icefall Cave": 0,
    "Sunburst Island": 0,
    "Lost Cave": 0,
    "Pattern Bush": 0,
    "Altering Cave": 0,
    "Tanoby Ruins": 0,
    "Pinkan Mountain": 0,
    # Johto (region 1) - 17 dungeons
    "Sprout Tower": 1,
    "Ruins of Alph": 1,
    "Union Cave": 1,
    "Slowpoke Well": 1,
    "Ilex Forest": 1,
    "Burned Tower": 1,
    "Olivine Lighthouse": 1,
    "Tin Tower": 1,
    "Whirl Islands": 1,
    "Mt. Mortar": 1,
    "Team Rocket's Hideout": 1,
    "Radio Tower": 1,
    "Ice Path": 1,
    "Dark Cave": 1,
    "Tohjo Falls": 1,
    "Victory Road Johto": 1,
    "Mt. Silver": 1,
    # Hoenn (region 2) - 38 dungeons (includes Orre)
    "Petalburg Woods": 2,
    "Rusturf Tunnel": 2,
    "Granite Cave": 2,
    "Fiery Path": 2,
    "Meteor Falls": 2,
    "Mt. Chimney Crater": 2,
    "Jagged Pass": 2,
    "New Mauville": 2,
    "Weather Institute": 2,
    "Mt. Pyre": 2,
    "Magma Hideout": 2,
    "Aqua Hideout": 2,
    "Shoal Cave": 2,
    "Seafloor Cavern": 2,
    "Sealed Chamber": 2,
    "Cave of Origin": 2,
    "Sky Pillar": 2,
    "Victory Road Hoenn": 2,
    "Near Space": 2,
    # Orre (in Hoenn region)
    "Phenac City Battles": 2,
    "Pyrite Town Battles": 2,
    "Pyrite Colosseum": 2,
    "Pyrite Building": 2,
    "Pyrite Cave": 2,
    "Relic Cave": 2,
    "Mt. Battle": 2,
    "The Under": 2,
    "Cipher Lab": 2,
    "Realgam Tower Battles": 2,
    "Realgam Colosseum": 2,
    "Snagem Hideout": 2,
    "Deep Colosseum": 2,
    "Phenac Stadium": 2,
    "Under Colosseum": 2,
    "Gateon Port Battles": 2,
    "Cipher Key Lair": 2,
    "Citadark Isle": 2,
    "Citadark Isle Dome": 2,
    # Sinnoh (region 3) - 24 dungeons
    "Oreburgh Gate": 3,
    "Valley Windworks": 3,
    "Eterna Forest": 3,
    "Old Chateau": 3,
    "Team Galactic Eterna Building": 3,
    "Wayward Cave": 3,
    "Mt. Coronet South": 3,
    "Solaceon Ruins": 3,
    "Iron Island": 3,
    "Lake Valor": 3,
    "Lake Verity": 3,
    "Mt. Coronet North": 3,
    "Lake Acuity": 3,
    "Team Galactic HQ": 3,
    "Spear Pillar": 3,
    "Distortion World": 3,
    "Victory Road Sinnoh": 3,
    "Sendoff Spring": 3,
    "Fullmoon Island": 3,
    "Newmoon Island": 3,
    "Flower Paradise": 3,
    "Snowpoint Temple": 3,
    "Stark Mountain": 3,
    "Hall of Origin": 3,
    # Unova (region 4) - 23 dungeons
    "Floccesy Ranch": 4,
    "Liberty Garden": 4,
    "Castelia Sewers": 4,
    "Relic Passage": 4,
    "Relic Castle": 4,
    "Lostlorn Forest": 4,
    "Chargestone Cave": 4,
    "Mistralton Cave": 4,
    "Celestial Tower": 4,
    "Reversal Mountain": 4,
    "Seaside Cave": 4,
    "Plasma Frigate": 4,
    "Giant Chasm": 4,
    "Cave of Being": 4,
    "Abundant Shrine": 4,
    "Victory Road Unova": 4,
    "Twist Mountain": 4,
    "Dragonspiral Tower": 4,
    "Moor of Icirrus": 4,
    "Pledge Grove": 4,
    "Pinwheel Forest": 4,
    "Dreamyard": 4,
    "P2 Laboratory": 4,
    # Kalos (region 5) - 13-15 dungeons
    "Santalune Forest": 5,
    "Connecting Cave": 5,
    "Glittering Cave": 5,
    "Reflection Cave": 5,
    "Sea Spirit's Den": 5,
    "Kalos Power Plant": 5,
    "Poké Ball Factory": 5,
    "Lost Hotel": 5,
    "Frost Cavern": 5,
    "Team Flare Secret HQ": 5,
    "Terminus Cave": 5,
    "Pokémon Village": 5,
    "Victory Road Kalos": 5,
    # Alola (region 6) - 30-32 dungeons
    "Trainers' School": 6,
    "Hau'oli Cemetery": 6,
    "Verdant Cavern": 6,
    "Melemele Meadow": 6,
    "Seaward Cave": 6,
    "Ten Carat Hill": 6,
    "Pikachu Valley": 6,
    "Paniola Ranch": 6,
    "Brooklet Hill": 6,
    "Wela Volcano Park": 6,
    "Lush Jungle": 6,
    "Diglett's Tunnel": 6,
    "Memorial Hill": 6,
    "Malie Garden": 6,
    "Hokulani Observatory": 6,
    "Thrifty Megamart": 6,
    "Ula'ula Meadow": 6,
    "Po Town": 6,
    "Aether Foundation": 6,
    "Exeggutor Island Hill": 6,
    "Vast Poni Canyon": 6,
    "Mina's Houseboat": 6,
    "Mount Lanakila": 6,
    "Lake of the Sunne and Moone": 6,
    "Ruins of Conflict": 6,
    "Ruins of Life": 6,
    "Ruins of Abundance": 6,
    "Ruins of Hope": 6,
    "Poni Meadow": 6,
    "Resolution Cave": 6,
    # Galar (region 7) - 22 dungeons
    "Slumbering Weald Shrine": 7,
    "Galar Mine": 7,
    "Galar Mine No. 2": 7,
    "Glimwood Tangle": 7,
    "Rose Tower": 7,
    "Energy Plant": 7,
    "Dusty Bowl": 7,
    "Courageous Cavern": 7,
    "Brawlers' Cave": 7,
    "Warm-Up Tunnel": 7,
    "Tower of Darkness": 7,
    "Tower of Waters": 7,
    "Roaring-Sea Caves": 7,
    "Rock Peak Ruins": 7,
    "Iron Ruins": 7,
    "Iceberg Ruins": 7,
    "Split-Decision Ruins": 7,
    "Lakeside Cave": 7,
    "Dyna Tree Hill": 7,
    "Tunnel to the Top": 7,
    "Crown Shrine": 7,
    "Max Lair": 7,
    # Hisui (region 8) - 23 dungeons
    "Floaro Gardens": 8,
    "Oreburrow Tunnel": 8,
    "Heartwood": 8,
    "Ancient Solaceon Ruins": 8,
    "Shrouded Ruins": 8,
    "Veilstone Cape": 8,
    "Firespit Island": 8,
    "Ancient Wayward Cave": 8,
    "Ancient Quarry": 8,
    "Primeval Grotto": 8,
    "Clamberclaw Cliffs": 8,
    "Celestica Ruins": 8,
    "Sacred Plaza": 8,
    "Avalugg's Legacy": 8,
    "Ice Column Chamber": 8,
    "Icepeak Cavern": 8,
    "Ancient Snowpoint Temple": 8,
    "Seaside Hollow": 8,
    "Ancient Lake Verity": 8,
    "Ancient Lake Valor": 8,
    "Ancient Lake Acuity": 8,
    "Temple of Sinnoh": 8,
    "Turnback Cave": 8,
    # Paldea (region 9) - 8 dungeons
    "Inlet Grotto": 9,
    "Glaseado Mountain": 9,
    "Grasswither Shrine": 9,
    "Icerend Shrine": 9,
    "Groundblight Shrine": 9,
    "Firescourge Shrine": 9,
    "Area Zero": 9,
    "Area Zero Depths": 9,
}


def get_dungeon_region(name: str) -> int:
    """Get region for a dungeon using official mapping, -1 if not found (event dungeon)."""
    return DUNGEON_REGIONS.get(name, -1)


def extract_pokemon_names(enemy_block: str) -> list[dict]:
    """Extract pokemon from enemy list."""
    pokemon = []

    # Match: {pokemon: 'Name', options: {...}}
    detailed_pattern = (
        r"\{pokemon:\s*['\"]([^'\"]+)['\"](?:,\s*options:\s*\{[^}]*weight:\s*(\d+))?[^}]*\}"
    )
    for match in re.finditer(detailed_pattern, enemy_block):
        name = match.group(1)
        weight = int(match.group(2)) if match.group(2) else 1
        pokemon.append({"name": name, "weight": weight, "is_boss": False})

    # Match simple: 'PokemonName' (without details)
    simple_pattern = r"(?<!\w)['\"]([A-Z][a-z]+(?:\s[A-Z]?[a-z]+)*(?:\s?\([^)]+\))?)['\"](?!\s*:)"
    for match in re.finditer(simple_pattern, enemy_block):
        name = match.group(1)
        # Skip if already found
        if not any(p["name"] == name for p in pokemon):
            pokemon.append({"name": name, "weight": 1, "is_boss": False})

    return pokemon


def extract_boss_pokemon(boss_block: str) -> list[dict]:
    """Extract boss pokemon from boss list."""
    bosses = []

    # Match: new DungeonBossPokemon('Name', health, level, ...)
    pattern = r"new\s+DungeonBossPokemon\s*\(\s*['\"]([^'\"]+)['\"],\s*(\d+),\s*(\d+)"
    for match in re.finditer(pattern, boss_block):
        bosses.append(
            {
                "name": match.group(1),
                "health": int(match.group(2)),
                "level": int(match.group(3)),
                "is_boss": True,
            }
        )

    return bosses


def extract_loot_table(loot_block: str) -> dict:
    """Extract loot table from dungeon."""
    loot = {"common": [], "rare": [], "epic": [], "legendary": [], "mythic": []}

    for tier in loot.keys():
        # Match tier: [...]
        pattern = rf"{tier}:\s*\[(.*?)\]"
        match = re.search(pattern, loot_block, re.DOTALL)
        if match:
            tier_content = match.group(1)
            # Extract items: {loot: 'ItemName', weight: N}
            item_pattern = r"\{loot:\s*['\"]([^'\"]+)['\"](?:,\s*weight:\s*(\d+))?"
            for item_match in re.finditer(item_pattern, tier_content):
                item_name = item_match.group(1)
                weight = int(item_match.group(2)) if item_match.group(2) else 1
                loot[tier].append({"item": item_name, "weight": weight})

    return loot


def parse_dungeons(content: str) -> list[dict]:
    """Parse all dungeons from Dungeon.ts content."""
    dungeons = []

    # Match: dungeonList['Dungeon Name'] = new Dungeon(...)
    # Support escaped quotes in names
    pattern = r"dungeonList\['((?:[^'\\]|\\.)*)'\]\s*=\s*new\s+Dungeon\s*\("

    matches = list(re.finditer(pattern, content))

    for i, match in enumerate(matches):
        raw_name = match.group(1)
        # Unescape the name
        name = raw_name.replace("\\'", "'").replace('\\"', '"')
        start_pos = match.end()

        # Find end of this dungeon definition
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(content)

        dungeon_content = content[start_pos:end_pos]

        # Determine region using official mapping
        region = get_dungeon_region(name)

        dungeon_data = {
            "name": name,
            "region": region,
            "pokemon": [],
            "bosses": [],
            "loot": {},
            "base_health": None,
            "token_cost": None,
        }

        # Extract base health - number after loot table closing }
        health_match = re.search(r"\},\s*(\d+),", dungeon_content)
        if health_match:
            dungeon_data["base_health"] = int(health_match.group(1))

        # Extract token cost - number near end before );
        token_match = re.search(r"\],\s*(\d+),\s*\d+\s*\)", dungeon_content)
        if token_match:
            dungeon_data["token_cost"] = int(token_match.group(1))

        # Find enemy list (first major [...] block)
        bracket_depth = 0
        enemy_start = None
        enemy_end = None

        for j, char in enumerate(dungeon_content):
            if char == "[":
                if bracket_depth == 0:
                    enemy_start = j
                bracket_depth += 1
            elif char == "]":
                bracket_depth -= 1
                if bracket_depth == 0 and enemy_start is not None:
                    enemy_end = j + 1
                    break

        if enemy_start is not None and enemy_end is not None:
            enemy_block = dungeon_content[enemy_start:enemy_end]
            dungeon_data["pokemon"] = extract_pokemon_names(enemy_block)

        # Find loot table {...}
        loot_match = re.search(
            r"\{(?:\s*common:|\s*rare:|\s*epic:|\s*legendary:|\s*mythic:)", dungeon_content
        )
        if loot_match:
            loot_start = loot_match.start()
            # Find matching }
            bracket_depth = 0
            loot_end = loot_start
            for j, char in enumerate(dungeon_content[loot_start:]):
                if char == "{":
                    bracket_depth += 1
                elif char == "}":
                    bracket_depth -= 1
                    if bracket_depth == 0:
                        loot_end = loot_start + j + 1
                        break

            loot_block = dungeon_content[loot_start:loot_end]
            dungeon_data["loot"] = extract_loot_table(loot_block)

        # Find boss list - [...] after the base health number
        if health_match:
            after_health = dungeon_content[health_match.end() :]
            boss_bracket = 0
            boss_start = None
            boss_end = None

            for j, char in enumerate(after_health):
                if char == "[":
                    if boss_bracket == 0:
                        boss_start = j
                    boss_bracket += 1
                elif char == "]":
                    boss_bracket -= 1
                    if boss_bracket == 0 and boss_start is not None:
                        boss_end = j + 1
                        break

            if boss_start is not None and boss_end is not None:
                boss_block = after_health[boss_start:boss_end]
                dungeon_data["bosses"] = extract_boss_pokemon(boss_block)

        dungeons.append(dungeon_data)

    return dungeons


def main() -> None:
    """Parse Dungeon.ts and output JSON."""
    dungeon_path = (
        Path(__file__).parent.parent
        / "reference"
        / "pokeclicker-develop"
        / "src"
        / "scripts"
        / "dungeons"
        / "Dungeon.ts"
    )

    if not dungeon_path.exists():
        print(f"Error: {dungeon_path} not found")
        return

    content = dungeon_path.read_text(encoding="utf-8")
    dungeons = parse_dungeons(content)

    print(f"Parsed {len(dungeons)} dungeons")

    # Stats
    regions: dict[int, int] = {}
    for d in dungeons:
        r = d["region"]
        regions[r] = regions.get(r, 0) + 1

    for r, count in sorted(regions.items()):
        region_name = (
            [
                "Kanto",
                "Johto",
                "Hoenn",
                "Sinnoh",
                "Unova",
                "Kalos",
                "Alola",
                "Galar",
                "Hisui",
                "Paldea",
            ][r]
            if r >= 0
            else "Event/Special"
        )
        print(f"  Region {r} ({region_name}): {count} dungeons")

    # Count unmapped
    unmapped = sum(1 for d in dungeons if d["region"] == -1)
    if unmapped:
        print(f"  Unmapped (events): {unmapped}")

    # Output to JSON file
    output_path = Path(__file__).parent / "dungeons_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dungeons, f, indent=2, ensure_ascii=False)

    print(f"Output written to {output_path}")


if __name__ == "__main__":
    main()
