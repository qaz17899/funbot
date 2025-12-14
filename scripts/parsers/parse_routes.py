"""Parse Pokeclicker RouteData.ts into structured JSON.

This parser uses BRACKET COUNTING to correctly handle nested requirements like:
  OneFromManyRequirement([
    new RouteKillRequirement(10, Region.kanto, 1),
    new TemporaryBattleRequirement('Blue 2')
  ])

Usage:
    python scripts/parse_routes.py > routes_data.json
"""

from __future__ import annotations

import contextlib
import json
import re
import sys
from pathlib import Path
from typing import Any


# =============================================================================
# ENUM MAPPINGS
# =============================================================================

REGION_MAP = {
    "Region.kanto": 0,
    "Region.johto": 1,
    "Region.hoenn": 2,
    "Region.sinnoh": 3,
    "Region.unova": 4,
    "Region.kalos": 5,
    "Region.alola": 6,
    "Region.galar": 7,
    "Region.hisui": 8,
    "Region.paldea": 9,
}

# SubRegion mappings - all regions
SUBREGION_MAP = {
    # Kanto
    "KantoSubRegions.Kanto": 0,
    "KantoSubRegions.Sevii123": 1,
    "KantoSubRegions.Sevii4567": 2,
    # Johto
    "JohtoSubRegions.Johto": 0,
    # Hoenn
    "HoennSubRegions.Hoenn": 0,
    "HoennSubRegions.Orre": 1,
    # Sinnoh
    "SinnohSubRegions.Sinnoh": 0,
    # Unova
    "UnovaSubRegions.Unova": 0,
    # Kalos
    "KalosSubRegions.Kalos": 0,
    # Alola
    "AlolaSubRegions.MelemeleIsland": 0,
    "AlolaSubRegions.AkalaIsland": 1,
    "AlolaSubRegions.UlaulaIsland": 2,
    "AlolaSubRegions.PoniIsland": 3,
    "AlolaSubRegions.MagikarpJump": 4,
    # Galar
    "GalarSubRegions.SouthGalar": 0,
    "GalarSubRegions.NorthGalar": 1,
    "GalarSubRegions.IsleofArmor": 2,
    "GalarSubRegions.CrownTundra": 3,
    # Hisui
    "HisuiSubRegions.Hisui": 0,
    # Paldea
    "PaldeaSubRegions.Paldea": 0,
    "PaldeaSubRegions.Kitakami": 1,
    "PaldeaSubRegions.BlueberryAcademy": 2,
}


# =============================================================================
# BRACKET-AWARE ARGUMENT PARSER
# =============================================================================


def parse_arguments(arg_string: str) -> list[str]:
    """
    Split arguments respecting brackets and quotes.

    Handles: `arg1, arg2, new Class(arg3, arg4), [item1, item2]`
    Returns: ['arg1', 'arg2', 'new Class(arg3, arg4)', '[item1, item2]']
    """
    args = []
    current_arg = ""
    bracket_level = 0
    square_level = 0
    in_string = False
    string_char = None
    prev_char = ""

    for char in arg_string:
        # Track string state - handle escaped quotes
        if char in ("'", '"', "`") and prev_char != "\\":
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None

        # Track bracket levels
        if not in_string:
            if char == "(":
                bracket_level += 1
            elif char == ")":
                bracket_level -= 1
            elif char == "[":
                square_level += 1
            elif char == "]":
                square_level -= 1

        # Split on top-level commas only
        if char == "," and bracket_level == 0 and square_level == 0 and not in_string:
            args.append(current_arg.strip())
            current_arg = ""
        else:
            current_arg += char

        prev_char = char

    if current_arg.strip():
        args.append(current_arg.strip())

    return args


def safe_int(value: str, default: int = 0) -> int:
    """Safely convert string to int."""
    try:
        # Handle GameConstants.AchievementOption.less type values
        if "." in value and not value.replace(".", "").replace("-", "").isdigit():
            return default
        return int(value.strip())
    except (ValueError, AttributeError):
        return default


# =============================================================================
# RECURSIVE REQUIREMENT PARSER
# =============================================================================


def parse_requirement(req_string: str) -> dict[str, Any] | None:
    """
    Recursively parse a requirement expression.

    Input: 'new RouteKillRequirement(10, Region.kanto, 1)'
    Output: {'type': 'RouteKillRequirement', 'params': {...}, 'children': []}
    """
    req_string = req_string.strip()
    if not req_string:
        return None

    # Match: new ClassName(args...)
    match = re.match(r"new\s+(\w+)\((.*)\)$", req_string, re.DOTALL)
    if not match:
        return None

    req_type = match.group(1)
    args_str = match.group(2)
    args = parse_arguments(args_str)

    node: dict[str, Any] = {"type": req_type, "params": {}, "children": []}

    # Handle logical containers (OR/AND)
    if req_type in ("OneFromManyRequirement", "MultiRequirement"):
        # First argument is an array: [new Req1(), new Req2()]
        if args and args[0].strip().startswith("["):
            array_content = args[0].strip()[1:-1]  # Remove [ ]
            child_strs = parse_arguments(array_content)
            for child_str in child_strs:
                child_node = parse_requirement(child_str)
                if child_node:
                    node["children"].append(child_node)
        return node

    # Parse specific requirement types
    if req_type == "RouteKillRequirement":
        # RouteKillRequirement(amount, region, route)
        if len(args) >= 3:
            node["params"] = {
                "amount": int(args[0]),
                "region": REGION_MAP.get(args[1].strip(), args[1].strip()),
                "route": int(args[2]),
            }

    elif req_type == "GymBadgeRequirement":
        # GymBadgeRequirement(BadgeEnums.Boulder)
        if args:
            badge = args[0].strip()
            # Extract just the badge name
            if "." in badge:
                badge = badge.split(".")[-1]
            node["params"] = {"badge": badge}

    elif req_type == "ClearDungeonRequirement":
        # ClearDungeonRequirement(amount, getDungeonIndex('Mt. Moon'))
        if len(args) >= 2:
            amount = int(args[0])
            dungeon_match = re.search(r"getDungeonIndex\(['\"]([^'\"]+)['\"]\)", args[1])
            dungeon_name = dungeon_match.group(1) if dungeon_match else args[1]
            node["params"] = {"amount": amount, "dungeon": dungeon_name}

    elif req_type == "TemporaryBattleRequirement":
        # TemporaryBattleRequirement('Blue 2')
        if args:
            battle = args[0].strip().strip("'\"")
            node["params"] = {"battle": battle}

    elif req_type == "QuestLineCompletedRequirement":
        # QuestLineCompletedRequirement('Celio\'s Errand')
        if args:
            quest = args[0].strip().strip("'\"")
            node["params"] = {"quest": quest}

    elif req_type == "QuestLineStepCompletedRequirement":
        # QuestLineStepCompletedRequirement('Bill\'s Errand', step, optional)
        if len(args) >= 2:
            quest = args[0].strip().strip("'\"")
            step = safe_int(args[1])
            node["params"] = {"quest": quest, "step": step}

    elif req_type == "ObtainedPokemonRequirement":
        # ObtainedPokemonRequirement('Sunkern')
        if args:
            pokemon = args[0].strip().strip("'\"")
            node["params"] = {"pokemon": pokemon}

    elif req_type == "WeatherRequirement":
        # WeatherRequirement([WeatherType.Clear, WeatherType.Overcast])
        node["params"] = {"raw": args[0] if args else ""}

    elif req_type == "DayOfWeekRequirement":
        # DayOfWeekRequirement([DayOfWeek.Monday])
        node["params"] = {"raw": args[0] if args else ""}

    elif req_type == "SpecialEventRequirement":
        # SpecialEventRequirement('Lunar New Year')
        if args:
            event = args[0].strip().strip("'\"")
            node["params"] = {"event": event}

    else:
        # Unknown requirement type - store raw args
        node["params"] = {"raw_args": args}

    return node


# =============================================================================
# ROUTE PARSER
# =============================================================================


def parse_pokemon_block(rest: str) -> dict[str, list]:
    """Parse the RoutePokemon block to extract land/water/headbutt/special."""
    pokemon: dict[str, list] = {"land": [], "water": [], "headbutt": [], "special": []}

    # Parse simple arrays: land: ['Pidgey', 'Rattata', 'Farfetch\'d']
    for key in ("land", "water", "headbutt"):
        pattern = rf"{key}:\s*\[([^\]]*)\]"
        match = re.search(pattern, rest, re.DOTALL)
        if match:
            content = match.group(1)
            # Extract quoted strings - handle escaped quotes
            # Match 'name' or "name" including escaped quotes inside
            names = []
            # Pattern: 'anything' or "anything" with proper handling
            for name_match in re.finditer(
                r"'((?:[^'\\]|\\.)*)'" + r'|"((?:[^"\\]|\\.)*)"', content
            ):
                name = name_match.group(1) or name_match.group(2)
                # Unescape the name (replace \' with ')
                name = name.replace("\\'", "'").replace('\\"', '"')
                if name.strip():
                    names.append(name)
            pokemon[key] = names

    # Parse special: [new SpecialRoutePokemon(...)]
    special_match = re.search(r"special:\s*\[(.*?)\](?=,?\s*\})", rest, re.DOTALL)
    if special_match:
        content = special_match.group(1).strip()
        if content:
            # Each SpecialRoutePokemon is complex - store as raw for now
            special_items = parse_arguments(content)
            for item in special_items:
                if "SpecialRoutePokemon" in item:
                    # Extract pokemon names and requirement
                    names_match = re.search(r"\[([^\]]+)\]", item)
                    if names_match:
                        names = re.findall(r"['\"]([^'\"]+)['\"]", names_match.group(1))
                        # Extract requirement (everything after the first array)
                        req_match = re.search(r"\],\s*(.+)\)$", item, re.DOTALL)
                        req_node = None
                        if req_match:
                            req_node = parse_requirement(req_match.group(1).strip())
                        pokemon["special"].append({"pokemon": names, "requirement": req_node})

    return pokemon


def parse_routes(file_content: str) -> list[dict]:
    """Parse all Routes.add(...) calls from RouteData.ts."""
    routes = []

    # Pattern to match Routes.add(new RegionRoute(...));
    # This is tricky because arguments can span multiple lines
    pattern = re.compile(
        r"Routes\.add\(new RegionRoute\(\s*"
        r"'([^']+)',\s*"  # routeName
        r"([^,]+),\s*"  # region
        r"(\d+),\s*"  # number
        r"(.*?)"  # rest of arguments
        r"\)\);",
        re.DOTALL,
    )

    for match in pattern.finditer(file_content):
        route_name = match.group(1)
        region_str = match.group(2).strip()
        route_number = int(match.group(3))
        rest = match.group(4)

        route_data: dict[str, Any] = {
            "name": route_name,
            "region": REGION_MAP.get(region_str, region_str),
            "region_str": region_str,
            "number": route_number,
            "pokemon": parse_pokemon_block(rest),
            "requirements": [],
            "order_number": route_number,  # Default
            "sub_region": None,
            "route_health": None,
        }

        # Extract requirements array [new Req1(), new Req2()]
        # Requirements come after RoutePokemon block which ends with })
        # We need bracket-aware extraction since OneFromManyRequirement contains []
        req_start = re.search(r"\}\),?\s*\[", rest)
        if req_start:
            # Find matching closing bracket using bracket counting
            start_pos = req_start.end()
            bracket_level = 1
            pos = start_pos
            while pos < len(rest) and bracket_level > 0:
                char = rest[pos]
                if char == "[":
                    bracket_level += 1
                elif char == "]":
                    bracket_level -= 1
                pos += 1

            if bracket_level == 0:
                req_content = rest[start_pos : pos - 1].strip()
                if req_content:
                    req_strs = parse_arguments(req_content)
                    for req_str in req_strs:
                        req_node = parse_requirement(req_str)
                        if req_node:
                            route_data["requirements"].append(req_node)

        # Extract order_number (optional float after requirements)
        order_match = re.search(r"\],\s*([\d.]+)\s*,", rest)
        if order_match:
            try:
                route_data["order_number"] = float(order_match.group(1))
            except ValueError:
                pass

        # Extract sub_region and track which one
        sub_region_name = None
        for sr_name, sr_id in SUBREGION_MAP.items():
            if sr_name in rest:
                route_data["sub_region"] = sr_id
                sub_region_name = sr_name
                break

        # Extract trailing args: ignore_in_calculations (bool) and route_health (int)
        # These come after the subRegion in the format: SubRegion, true, 37487
        if sub_region_name:
            # Find position of subRegion in rest and look for trailing args
            sr_pos = rest.find(sub_region_name)
            if sr_pos != -1:
                trailing = rest[sr_pos + len(sub_region_name) :]
                # Match: , true, 37487 or just , 37487 or , true
                trailing_match = re.search(
                    r",\s*(true|false|undefined)?\s*(?:,\s*(\d+))?\s*\)?", trailing
                )
                if trailing_match:
                    ignore_val = trailing_match.group(1)
                    health_val = trailing_match.group(2)
                    if ignore_val == "true":
                        route_data["ignore_in_calculations"] = True
                    elif ignore_val == "false":
                        route_data["ignore_in_calculations"] = False
                    if health_val:
                        route_data["route_health"] = int(health_val)

        routes.append(route_data)

    return routes


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """Parse RouteData.ts and output JSON."""
    route_data_path = (
        Path(__file__).parent.parent
        / "reference"
        / "pokeclicker-develop"
        / "src"
        / "modules"
        / "routes"
        / "RouteData.ts"
    )

    if not route_data_path.exists():
        print(f"Error: {route_data_path} not found", file=sys.stderr)
        return

    content = route_data_path.read_text(encoding="utf-8")
    routes = parse_routes(content)

    print(f"Parsed {len(routes)} routes", file=sys.stderr)

    # Write to file with UTF-8 encoding
    output_path = Path(__file__).parent / "routes_data.json"
    output_path.write_text(json.dumps(routes, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Output written to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
