"""Unit conversion to metric - manual implementation for Python 3.14 compatibility."""

from typing import Optional

# Conversion factors to metric base units
# Weight conversions (to grams)
WEIGHT_TO_GRAMS = {
    "oz": 28.3495,
    "lb": 453.592,
    "g": 1.0,
    "kg": 1000.0,
}

# Volume conversions (to milliliters)
VOLUME_TO_ML = {
    "cup": 236.588,
    "tbsp": 14.787,
    "tsp": 4.929,
    "fl oz": 29.574,
    "ml": 1.0,
    "l": 1000.0,
}

# Units that cannot be converted
NON_CONVERTIBLE = {"clove", "bunch", "pinch", "to taste", "can", "package"}

# Thresholds for using larger units
WEIGHT_THRESHOLD = 1000  # g -> kg
VOLUME_THRESHOLD = 1000  # ml -> l


def convert_to_metric(
    quantity: Optional[float],
    unit: Optional[str],
) -> tuple[Optional[float], Optional[str]]:
    """Convert quantity and unit to metric.

    Returns (quantity, unit) tuple.
    Non-convertible units are returned as-is.
    """
    if quantity is None or unit is None:
        return quantity, unit

    unit_lower = unit.lower().strip()

    # Non-convertible units
    if unit_lower in NON_CONVERTIBLE:
        return quantity, unit

    # Already metric
    if unit_lower in {"g", "kg", "ml", "l"}:
        return quantity, unit_lower

    # Weight conversion
    if unit_lower in WEIGHT_TO_GRAMS:
        grams = quantity * WEIGHT_TO_GRAMS[unit_lower]
        if grams >= WEIGHT_THRESHOLD:
            return round(grams / 1000, 2), "kg"
        return round(grams, 0), "g"

    # Volume conversion
    if unit_lower in VOLUME_TO_ML:
        ml = quantity * VOLUME_TO_ML[unit_lower]
        if ml >= VOLUME_THRESHOLD:
            return round(ml / 1000, 2), "l"
        return round(ml, 0), "ml"

    # Unknown unit - return as-is
    return quantity, unit


def format_quantity(quantity: Optional[float], unit: Optional[str]) -> str:
    """Format quantity and unit for display."""
    if quantity is None and unit is None:
        return ""
    if quantity is None:
        return unit or ""
    if unit is None:
        # Count items (e.g., "2 onions")
        if quantity == int(quantity):
            return str(int(quantity))
        return str(quantity)

    # Format with unit
    if quantity == int(quantity):
        return f"{int(quantity)}{unit}"
    return f"{quantity}{unit}"
