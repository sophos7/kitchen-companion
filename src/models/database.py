"""SQLite database models and initialization."""

import os
import sqlite3
from dataclasses import dataclass
from typing import Optional

DATA_PATH = os.environ.get("DATA_PATH", "data")
DB_PATH = os.path.join(DATA_PATH, "recipes.db")


@dataclass
class Recipe:
    """Recipe data model."""

    id: Optional[int]
    filename: str
    name: str
    servings: int
    file_modified: float
    raw_content: str
    parsed_at: float
    parse_error: Optional[str]


@dataclass
class Ingredient:
    """Ingredient data model."""

    id: Optional[int]
    recipe_id: int
    quantity: Optional[float]
    unit: Optional[str]
    name: str
    raw_text: str
    category: Optional[str]


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database schema."""
    os.makedirs(DATA_PATH, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            servings INTEGER DEFAULT 4,
            file_modified REAL NOT NULL,
            raw_content TEXT NOT NULL,
            parsed_at REAL NOT NULL,
            parse_error TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            quantity REAL,
            unit TEXT,
            name TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            category TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ingredients_recipe_id
        ON ingredients (recipe_id)
    """)

    conn.commit()
    conn.close()


def get_all_recipes() -> list[Recipe]:
    """Get all recipes from database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [Recipe(**dict(row)) for row in rows]


def get_recipe_by_id(recipe_id: int) -> Optional[Recipe]:
    """Get a recipe by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    row = cursor.fetchone()
    conn.close()
    return Recipe(**dict(row)) if row else None


def get_recipe_by_filename(filename: str) -> Optional[Recipe]:
    """Get a recipe by filename."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes WHERE filename = ?", (filename,))
    row = cursor.fetchone()
    conn.close()
    return Recipe(**dict(row)) if row else None


def upsert_recipe(recipe: Recipe) -> int:
    """Insert or update a recipe, returns recipe ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO recipes (filename, name, servings, file_modified, raw_content, parsed_at, parse_error)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(filename) DO UPDATE SET
            name = excluded.name,
            servings = excluded.servings,
            file_modified = excluded.file_modified,
            raw_content = excluded.raw_content,
            parsed_at = excluded.parsed_at,
            parse_error = excluded.parse_error
    """, (
        recipe.filename,
        recipe.name,
        recipe.servings,
        recipe.file_modified,
        recipe.raw_content,
        recipe.parsed_at,
        recipe.parse_error,
    ))

    cursor.execute("SELECT id FROM recipes WHERE filename = ?", (recipe.filename,))
    recipe_id = cursor.fetchone()[0]

    conn.commit()
    conn.close()
    return recipe_id


def delete_recipe(filename: str) -> None:
    """Delete a recipe and its ingredients by filename."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM recipes WHERE filename = ?", (filename,))
    row = cursor.fetchone()
    if row:
        recipe_id = row[0]
        cursor.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()


def get_all_filenames() -> set[str]:
    """Get all recipe filenames in database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM recipes")
    filenames = {row[0] for row in cursor.fetchall()}
    conn.close()
    return filenames


def delete_ingredients_for_recipe(recipe_id: int) -> None:
    """Delete all ingredients for a recipe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))
    conn.commit()
    conn.close()


def insert_ingredient(ingredient: Ingredient) -> int:
    """Insert an ingredient, returns ingredient ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ingredients (recipe_id, quantity, unit, name, raw_text, category)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        ingredient.recipe_id,
        ingredient.quantity,
        ingredient.unit,
        ingredient.name,
        ingredient.raw_text,
        ingredient.category,
    ))
    ingredient_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ingredient_id


def get_ingredients_for_recipe(recipe_id: int) -> list[Ingredient]:
    """Get all ingredients for a recipe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ingredients WHERE recipe_id = ?", (recipe_id,))
    rows = cursor.fetchall()
    conn.close()
    return [Ingredient(**dict(row)) for row in rows]


def get_ingredients_for_recipes(recipe_ids: list[int]) -> list[Ingredient]:
    """Get all ingredients for multiple recipes."""
    if not recipe_ids:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(recipe_ids))
    cursor.execute(
        f"SELECT * FROM ingredients WHERE recipe_id IN ({placeholders})",
        recipe_ids,
    )
    rows = cursor.fetchall()
    conn.close()
    return [Ingredient(**dict(row)) for row in rows]
