"""Ingredient combining and scaling logic."""

from collections import defaultdict
from typing import Optional

import inflect

from src.services.converter import convert_to_metric, format_quantity
from src.services.categories import get_category, sort_by_category

inflect_engine = inflect.engine()


def singularize(word: str) -> str:
    """Convert plural word to singular form."""
    # Handle common cases inflect might miss
    if word.lower().endswith("ies"):
        return word[:-3] + "y"

    singular = inflect_engine.singular_noun(word)
    if singular:
        return singular
    return word


def normalize_ingredient_name(name: str) -> str:
    """Normalize ingredient name for matching.

    - Lowercase
    - Singularize
    - Strip extra whitespace
    """
    name = name.lower().strip()

    # Split into words and singularize each
    words = name.split()
    normalized_words = []
    for word in words:
        # Only singularize the main noun (usually last word)
        # But be careful with compound nouns
        normalized_words.append(word)

    # Singularize the last word (main ingredient)
    if normalized_words:
        normalized_words[-1] = singularize(normalized_words[-1])

    return " ".join(normalized_words)


def combine_ingredients(
    ingredients: list[dict],
    recipe_multipliers: dict[int, float],
) -> list[dict]:
    """Combine and scale ingredients from multiple recipes.

    Args:
        ingredients: List of ingredient dicts with keys:
            - recipe_id: int
            - quantity: Optional[float]
            - unit: Optional[str]
            - name: str
        recipe_multipliers: Dict mapping recipe_id to multiplier
            (target_servings / base_servings)

    Returns:
        List of combined ingredient dicts with keys:
            - name: str (original form, not normalized)
            - quantity: Optional[float]
            - unit: Optional[str]
            - display: str (formatted "name quantity")
            - category: str
    """
    # Group by normalized name and unit
    grouped: dict[tuple[str, Optional[str]], list[dict]] = defaultdict(list)

    for ing in ingredients:
        recipe_id = ing.get("recipe_id")
        multiplier = recipe_multipliers.get(recipe_id, 1.0)

        quantity = ing.get("quantity")
        unit = ing.get("unit")
        name = ing.get("name", "")

        # Apply scaling
        if quantity is not None:
            quantity = quantity * multiplier

        # Convert to metric
        quantity, unit = convert_to_metric(quantity, unit)

        # Normalize for grouping
        norm_name = normalize_ingredient_name(name)

        grouped[(norm_name, unit)].append({
            "quantity": quantity,
            "unit": unit,
            "name": name,  # Keep original for display
            "norm_name": norm_name,
        })

    # Combine quantities
    combined = []
    for (norm_name, unit), items in grouped.items():
        total_quantity = None
        display_name = items[0]["name"]  # Use first occurrence's name

        # Sum quantities
        for item in items:
            q = item.get("quantity")
            if q is not None:
                if total_quantity is None:
                    total_quantity = 0
                total_quantity += q

        # Format for display (name first, quantity at end)
        quantity_str = format_quantity(total_quantity, unit)
        if quantity_str:
            display = f"{display_name} {quantity_str}"
        else:
            display = display_name

        category = get_category(display_name)

        combined.append({
            "name": display_name,
            "quantity": total_quantity,
            "unit": unit,
            "display": display,
            "category": category,  # Actually stores zone name
        })

    # Sort by zone (category field contains zone name)
    return sort_by_category(combined)
