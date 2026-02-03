"""Markdown recipe parser and ingredient extraction."""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedIngredient:
    """Parsed ingredient data."""

    quantity: Optional[float]
    unit: Optional[str]
    name: str
    raw_text: str


@dataclass
class ParsedRecipe:
    """Parsed recipe data."""

    name: str
    servings: int
    ingredients: list[ParsedIngredient]
    raw_content: str
    error: Optional[str] = None


# Regex patterns for parsing
SERVINGS_PATTERN = re.compile(r"^Servings:\s*(\d+)", re.IGNORECASE | re.MULTILINE)
TITLE_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)
INGREDIENTS_SECTION = re.compile(
    r"##\s*Ingredients\s*\n(.*?)(?=\n##|\Z)",
    re.IGNORECASE | re.DOTALL,
)

# Quantity patterns
FRACTION_MAP = {
    "1/4": 0.25,
    "1/3": 0.333,
    "1/2": 0.5,
    "2/3": 0.667,
    "3/4": 0.75,
}

QUANTITY_PATTERN = re.compile(
    r"^(?:[-*]\s*)?"  # Optional bullet
    r"(?:"
    r"(\d+)\s+(\d+/\d+)"  # Mixed fraction: 1 1/2
    r"|(\d+/\d+)"  # Simple fraction: 1/2
    r"|(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)"  # Range: 2-3
    r"|(\d+(?:\.\d+)?)"  # Simple number: 2 or 2.5
    r")?\s*"
    r"((?:fl\s*oz|oz|lb|lbs?|pounds?|g|kg|ml|l|liters?|cups?|tbsp|tablespoons?|tsp|teaspoons?|cloves?|bunch|pinch|can|cans?|package|pkg)(?:\s|$))?"  # Unit
    r"(.+)$",  # Ingredient name
    re.IGNORECASE,
)

# Known units for normalization
UNIT_ALIASES = {
    "tbsp": "tbsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tsp": "tsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "cup": "cup",
    "cups": "cup",
    "oz": "oz",
    "fl oz": "fl oz",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    "g": "g",
    "kg": "kg",
    "ml": "ml",
    "l": "l",
    "liter": "l",
    "liters": "l",
    "clove": "clove",
    "cloves": "clove",
    "bunch": "bunch",
    "pinch": "pinch",
    "can": "can",
    "cans": "can",
    "package": "package",
    "pkg": "package",
}


def parse_fraction(fraction_str: str) -> float:
    """Parse a fraction string to float."""
    if fraction_str in FRACTION_MAP:
        return FRACTION_MAP[fraction_str]
    try:
        num, denom = fraction_str.split("/")
        return float(num) / float(denom)
    except (ValueError, ZeroDivisionError):
        return 0.0


def parse_quantity(match: re.Match) -> tuple[Optional[float], Optional[str], str]:
    """Extract quantity, unit, and name from regex match."""
    groups = match.groups()

    quantity = None

    # Mixed fraction: 1 1/2
    if groups[0] and groups[1]:
        quantity = float(groups[0]) + parse_fraction(groups[1])
    # Simple fraction: 1/2
    elif groups[2]:
        quantity = parse_fraction(groups[2])
    # Range: 2-3 (use higher value)
    elif groups[3] and groups[4]:
        quantity = float(groups[4])
    # Simple number
    elif groups[5]:
        quantity = float(groups[5])

    # Unit
    unit = None
    if groups[6]:
        unit_raw = groups[6].strip().lower()
        unit = UNIT_ALIASES.get(unit_raw, unit_raw)

    # Name (clean up)
    name = groups[7].strip() if groups[7] else ""
    # Remove trailing commas and preparation notes like ", diced"
    name = re.sub(r",\s*$", "", name)

    return quantity, unit, name


def parse_ingredient_line(line: str) -> Optional[ParsedIngredient]:
    """Parse a single ingredient line."""
    line = line.strip()
    if not line:
        return None

    # Skip comment lines
    if line.startswith("#"):
        return None

    # Handle "to taste" items
    if "to taste" in line.lower():
        # Extract ingredient name before "to taste"
        name = re.sub(r"\s*to\s+taste.*$", "", line, flags=re.IGNORECASE)
        name = re.sub(r"^[-*]\s*", "", name).strip()
        return ParsedIngredient(
            quantity=None,
            unit="to taste",
            name=name,
            raw_text=line,
        )

    match = QUANTITY_PATTERN.match(line)
    if match:
        quantity, unit, name = parse_quantity(match)
        if name:
            return ParsedIngredient(
                quantity=quantity,
                unit=unit,
                name=name,
                raw_text=line,
            )

    # Fallback: treat entire line as ingredient name
    name = re.sub(r"^[-*]\s*", "", line).strip()
    if name:
        return ParsedIngredient(
            quantity=None,
            unit=None,
            name=name,
            raw_text=line,
        )

    return None


def parse_recipe(filename: str, content: str) -> ParsedRecipe:
    """Parse a markdown recipe file."""
    # Extract title from first # heading or filename
    title_match = TITLE_PATTERN.search(content)
    if title_match:
        name = title_match.group(1).strip()
    else:
        # Use filename without extension
        name = filename.rsplit(".", 1)[0].replace("-", " ").replace("_", " ").title()

    # Extract servings
    servings_match = SERVINGS_PATTERN.search(content)
    servings = int(servings_match.group(1)) if servings_match else 4

    # Extract ingredients section
    ingredients_match = INGREDIENTS_SECTION.search(content)
    if not ingredients_match:
        return ParsedRecipe(
            name=name,
            servings=servings,
            ingredients=[],
            raw_content=content,
            error="Missing '## Ingredients' section",
        )

    ingredients_text = ingredients_match.group(1)
    ingredients = []

    for line in ingredients_text.split("\n"):
        parsed = parse_ingredient_line(line)
        if parsed:
            ingredients.append(parsed)

    if not ingredients:
        return ParsedRecipe(
            name=name,
            servings=servings,
            ingredients=[],
            raw_content=content,
            error="No ingredients found in '## Ingredients' section",
        )

    return ParsedRecipe(
        name=name,
        servings=servings,
        ingredients=ingredients,
        raw_content=content,
    )
