#!/usr/bin/env python3
"""CLI tool to analyze ingredient zones and find unzoned items."""

import sys
from collections import Counter
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models.database import init_db, get_all_recipes, get_ingredients_for_recipes
from src.services.categories import get_category, _load_zones
from src.services.additional_items import get_additional_items


def analyze_zones():
    """Analyze all recipe ingredients and show zone distribution."""
    print("Kitchen Companion - Zone Analyzer")
    print("=" * 60)
    print()
    
    # Initialize database
    init_db()
    
    # Load zones
    zones = _load_zones()
    if not zones:
        print("⚠️  No zones configured in categories.txt")
        print("   Create categories.txt with zone definitions")
        return
    
    print(f"📋 Loaded {len(zones)} zones from categories.txt")
    print()
    
    # Get all recipes
    recipes = get_all_recipes()
    if not recipes:
        print("⚠️  No recipes found in database")
        print("   Add some recipes and run refresh")
        return
    
    recipe_ids = [r.id for r in recipes]
    ingredients = get_ingredients_for_recipes(recipe_ids)
    
    # Get additional items
    additional_items = get_additional_items()
    
    total_items = len(ingredients) + len(additional_items)
    if total_items == 0:
        print("⚠️  No ingredients or additional items found")
        return
    
    print(f"🔍 Analyzing {len(ingredients)} recipe ingredients + {len(additional_items)} additional items")
    print()
    
    # Categorize ingredients
    zoned_items = Counter()
    unzoned_items = Counter()
    zone_distribution = Counter()
    
    # Process recipe ingredients
    for ing in ingredients:
        name = ing.name
        zone = get_category(name)
        
        if zone == "unzoned":
            unzoned_items[name] += 1
        else:
            zoned_items[name] += 1
            zone_distribution[zone] += 1
    
    # Process additional items
    for item in additional_items:
        zone = get_category(item)
        
        if zone == "unzoned":
            unzoned_items[item] += 1
        else:
            zoned_items[item] += 1
            zone_distribution[zone] += 1
    
    # Display zone distribution
    print("📊 Zone Distribution:")
    print("-" * 60)
    for zone, count in sorted(zone_distribution.items(), key=lambda x: x[0]):
        print(f"  {zone:20s} {count:3d} ingredients")
    
    total_zoned = sum(zoned_items.values())
    total_unzoned = sum(unzoned_items.values())
    total = total_zoned + total_unzoned
    
    print()
    print(f"  {'Total zoned':20s} {total_zoned:3d} ({total_zoned/total*100:.1f}%)")
    print(f"  {'Unzoned':20s} {total_unzoned:3d} ({total_unzoned/total*100:.1f}%)")
    print()
    
    # Display unzoned items
    if unzoned_items:
        print("⚠️  Unzoned Items (add these to categories.txt):")
        print("-" * 60)
        
        # Sort by frequency (most common first), then alphabetically
        sorted_unzoned = sorted(
            unzoned_items.items(),
            key=lambda x: (-x[1], x[0].lower())
        )
        
        for name, count in sorted_unzoned:
            recipes_text = "recipe" if count == 1 else "recipes"
            print(f"  • {name:40s} (in {count} {recipes_text})")
        
        print()
        print(f"💡 Total: {len(unzoned_items)} unique unzoned ingredients")
        print()
        print("To add these to zones:")
        print("  1. Edit categories.txt")
        print("  2. Add items to appropriate zones")
        print("  3. Example: zone2: bell pepper, onion, tomato, <new item>")
        
    else:
        print("✅ All ingredients are zoned!")
        print()
    
    # Show zone coverage summary
    unique_zoned = len(zoned_items)
    unique_unzoned = len(unzoned_items)
    unique_total = unique_zoned + unique_unzoned
    
    print()
    print("📈 Coverage Summary:")
    print("-" * 60)
    print(f"  Unique ingredients:    {unique_total}")
    print(f"  Zoned:                 {unique_zoned} ({unique_zoned/unique_total*100:.1f}%)")
    print(f"  Unzoned:               {unique_unzoned} ({unique_unzoned/unique_total*100:.1f}%)")


def show_zones():
    """Show all configured zones and their patterns."""
    print("Kitchen Companion - Zone Configuration")
    print("=" * 60)
    print()
    
    zones = _load_zones()
    if not zones:
        print("⚠️  No zones configured in categories.txt")
        return
    
    print(f"📋 {len(zones)} zones configured:")
    print()
    
    for zone, patterns in zones:
        print(f"  {zone}:")
        # Wrap patterns nicely
        pattern_str = ", ".join(patterns)
        if len(pattern_str) > 70:
            # Split into multiple lines
            words = pattern_str.split(", ")
            line = "    "
            for word in words:
                if len(line) + len(word) > 70:
                    print(line)
                    line = "    "
                line += word + ", "
            if line.strip():
                print(line.rstrip(", "))
        else:
            print(f"    {pattern_str}")
        print()


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze ingredient zones and find unzoned items",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python zones.py                 # Analyze and show unzoned items
  python zones.py --show-zones    # Show current zone configuration
        """
    )
    
    parser.add_argument(
        "--show-zones",
        action="store_true",
        help="Show configured zones instead of analyzing"
    )
    
    args = parser.parse_args()
    
    try:
        if args.show_zones:
            show_zones()
        else:
            analyze_zones()
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
