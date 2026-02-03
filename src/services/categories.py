"""Zone configuration for store layout grouping."""

import os
from functools import lru_cache

CATEGORIES_PATH = os.environ.get("CATEGORIES_PATH", "categories.txt")


@lru_cache(maxsize=1)
def _load_zones() -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Load zones from config file. Cached.
    
    Format: zone1: pattern1, pattern2
            zone2: pattern1, pattern2
    
    Returns list of (zone_name, patterns) tuples in order.
    """
    zones = []
    try:
        with open(CATEGORIES_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if ":" in line:
                        zone, patterns = line.split(":", 1)
                        zone = zone.strip()  # Keep original case for zone names
                        pattern_list = tuple(
                            p.strip().lower()
                            for p in patterns.split(",")
                            if p.strip()
                        )
                        if pattern_list:
                            zones.append((zone, pattern_list))
    except FileNotFoundError:
        pass
    return tuple(zones)


def reload_categories() -> None:
    """Clear cache and reload zones (keeping function name for compatibility)."""
    _load_zones.cache_clear()


def get_category(ingredient_name: str) -> str:
    """Get zone for an ingredient (keeping function name for compatibility).

    Uses case-insensitive partial matching.
    First matching zone wins.
    Returns "unzoned" if no match.
    """
    name_lower = ingredient_name.lower()
    for zone, patterns in _load_zones():
        for pattern in patterns:
            if pattern in name_lower:
                return zone
    return "unzoned"


def get_category_order(zone: str) -> int:
    """Get sort order for a zone.
    
    Zones are sorted by their definition order in the file.
    Unzoned items go last.
    """
    zones = _load_zones()
    for idx, (zone_name, _) in enumerate(zones):
        if zone_name == zone:
            return idx
    
    # Unzoned items go last
    return len(zones)


def sort_by_category(items: list[dict]) -> list[dict]:
    """Sort items by zone, then alphabetically within zone.

    Items should have 'name' and optionally 'category' keys.
    """
    def sort_key(item):
        zone = item.get("category", get_category(item.get("name", "")))
        name = item.get("name", "").lower()
        return (get_category_order(zone), name)

    return sorted(items, key=sort_key)
