"""Recipe folder scanner and database sync."""

import os
import time
import frontmatter

from src.models.database import (
    Recipe,
    Ingredient,
    get_all_filenames,
    get_recipe_by_filename,
    upsert_recipe,
    delete_recipe,
    delete_ingredients_for_recipe,
    insert_ingredient,
)
from src.services.parser import parse_recipe
from src.services.categories import get_category

RECIPES_PATH = os.environ.get("RECIPES_PATH", "recipes")


def scan_recipes() -> dict:
    """Scan recipes folder and sync with database.

    Returns:
        Dict with scan results:
            - added: list of filenames
            - updated: list of filenames
            - deleted: list of filenames
            - errors: list of filenames with parse errors
    """
    results = {
        "added": [],
        "updated": [],
        "deleted": [],
        "errors": [],
    }

    # Get current files in folder
    current_files = set()
    try:
        for filename in os.listdir(RECIPES_PATH):
            if filename.endswith(".md") and not filename.startswith("00-"):
                current_files.add(filename)
    except FileNotFoundError:
        return results

    # Get files in database
    db_files = get_all_filenames()

    # Find deleted files
    for filename in db_files - current_files:
        delete_recipe(filename)
        results["deleted"].append(filename)

    # Process current files
    for filename in current_files:
        filepath = os.path.join(RECIPES_PATH, filename)
        file_modified = os.path.getmtime(filepath)

        # Check if needs update
        existing = get_recipe_by_filename(filename)
        if existing and existing.file_modified >= file_modified:
            # No changes
            continue

        # Read and parse
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        
        # Parse frontmatter
        post = frontmatter.loads(content)
        category = post.get('category')
        tags = post.get('tags', [])
        
        # Convert tags list to comma-separated string
        tags_str = ','.join(tags) if isinstance(tags, list) else tags if tags else None
        
        # Parse recipe content (without frontmatter)
        parsed = parse_recipe(filename, post.content)

        # Create recipe record
        recipe = Recipe(
            id=None,
            filename=filename,
            name=parsed.name,
            servings=parsed.servings,
            file_modified=file_modified,
            raw_content=content,
            parsed_at=time.time(),
            parse_error=parsed.error,
            category=category,
            tags=tags_str,
        )

        recipe_id = upsert_recipe(recipe)

        # Track result
        if existing:
            results["updated"].append(filename)
        else:
            results["added"].append(filename)

        if parsed.error:
            results["errors"].append(filename)

        # Delete old ingredients and insert new ones
        delete_ingredients_for_recipe(recipe_id)

        for ing in parsed.ingredients:
            ingredient = Ingredient(
                id=None,
                recipe_id=recipe_id,
                quantity=ing.quantity,
                unit=ing.unit,
                name=ing.name,
                raw_text=ing.raw_text,
                category=get_category(ing.name),
            )
            insert_ingredient(ingredient)

    return results
