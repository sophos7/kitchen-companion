"""Additional items configuration for non-recipe shopping list items."""

import os
from functools import lru_cache

ADDITIONAL_ITEMS_PATH = os.environ.get("ADDITIONAL_ITEMS_PATH", "config/additional-items.txt")


@lru_cache(maxsize=1)
def _load_additional_items() -> tuple[str, ...]:
    """Load additional items from config file. Cached.
    
    Returns tuple of item names (one per line).
    """
    items = []
    try:
        with open(ADDITIONAL_ITEMS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    items.append(line)
    except FileNotFoundError:
        pass
    return tuple(items)


def reload_additional_items() -> None:
    """Clear cache and reload additional items."""
    _load_additional_items.cache_clear()


def get_additional_items() -> list[str]:
    """Get list of additional items."""
    return list(_load_additional_items())
