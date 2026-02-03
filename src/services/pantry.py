"""Pantry configuration and ingredient filtering."""

import os
from functools import lru_cache

PANTRY_PATH = os.environ.get("PANTRY_PATH", "config/pantry.txt")


@lru_cache(maxsize=1)
def _load_pantry_items() -> tuple[str, ...]:
    """Load pantry items from config file. Cached."""
    items = []
    try:
        with open(PANTRY_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    items.append(line.lower())
    except FileNotFoundError:
        pass
    return tuple(items)


def reload_pantry() -> None:
    """Clear cache and reload pantry items."""
    _load_pantry_items.cache_clear()


def get_pantry_items() -> list[str]:
    """Get list of pantry item patterns."""
    return list(_load_pantry_items())


def is_pantry_item(ingredient_name: str) -> bool:
    """Check if an ingredient matches a pantry item pattern.

    Uses case-insensitive partial matching.
    """
    name_lower = ingredient_name.lower()
    for pattern in _load_pantry_items():
        if pattern in name_lower:
            return True
    return False


def filter_pantry_items(
    ingredients: list[dict],
) -> tuple[list[dict], list[str]]:
    """Separate ingredients into shopping list and pantry items.

    Args:
        ingredients: List of ingredient dicts with 'name' key

    Returns:
        Tuple of (shopping_items, pantry_item_names)
        - shopping_items: ingredients not matching pantry
        - pantry_item_names: deduplicated names of pantry matches
    """
    shopping = []
    pantry_names = set()

    for ing in ingredients:
        name = ing.get("name", "")
        if is_pantry_item(name):
            pantry_names.add(name)
        else:
            shopping.append(ing)

    return shopping, sorted(pantry_names)
