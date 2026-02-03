"""Category configuration for store aisle grouping."""

import os
from functools import lru_cache

CATEGORIES_PATH = os.environ.get("CATEGORIES_PATH", "categories.txt")

# Default category order for sorting
CATEGORY_ORDER = [
    "produce",
    "dairy",
    "meat",
    "seafood",
    "bakery",
    "frozen",
    "canned",
    "pasta",
    "rice",
    "condiments",
    "oils",
    "spices",
    "baking",
    "beverages",
    "snacks",
    "other",
]


@lru_cache(maxsize=1)
def _load_categories() -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Load categories from config file. Cached."""
    categories = []
    try:
        with open(CATEGORIES_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if ":" in line:
                        category, patterns = line.split(":", 1)
                        category = category.strip().lower()
                        pattern_list = tuple(
                            p.strip().lower()
                            for p in patterns.split(",")
                            if p.strip()
                        )
                        if pattern_list:
                            categories.append((category, pattern_list))
    except FileNotFoundError:
        pass
    return tuple(categories)


def reload_categories() -> None:
    """Clear cache and reload categories."""
    _load_categories.cache_clear()


def get_category(ingredient_name: str) -> str:
    """Get category for an ingredient.

    Uses case-insensitive partial matching.
    First matching category wins.
    Returns "other" if no match.
    """
    name_lower = ingredient_name.lower()
    for category, patterns in _load_categories():
        for pattern in patterns:
            if pattern in name_lower:
                return category
    return "other"


def get_category_order(category: str) -> int:
    """Get sort order for a category."""
    try:
        return CATEGORY_ORDER.index(category.lower())
    except ValueError:
        return len(CATEGORY_ORDER)


def sort_by_category(items: list[dict]) -> list[dict]:
    """Sort items by category, then alphabetically within category.

    Items should have 'name' and optionally 'category' keys.
    """
    def sort_key(item):
        category = item.get("category", get_category(item.get("name", "")))
        name = item.get("name", "").lower()
        return (get_category_order(category), name)

    return sorted(items, key=sort_key)
