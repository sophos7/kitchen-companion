"""FastAPI routes for Kitchen Companion."""

import asyncio
import os
import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.models.database import (
    get_all_recipes,
    get_recipe_by_id,
    get_ingredients_for_recipes,
)
from src.services.scanner import scan_recipes, RECIPES_PATH
from src.services.combiner import combine_ingredients
from src.services.pantry import filter_pantry_items, reload_pantry
from src.services.categories import reload_categories
from src.services.exporter import recipe_to_html, shopping_list_to_text, inject_timer_buttons
from src.services.additional_items import get_additional_items, reload_additional_items

router = APIRouter()

# Event queue for SSE notifications
recipe_update_subscribers = []


def notify_recipe_update():
    """Notify all connected clients that recipes have been updated."""
    for queue in recipe_update_subscribers:
        try:
            queue.put_nowait({"type": "recipe_update"})
        except asyncio.QueueFull:
            pass


class RecipeResponse(BaseModel):
    """Recipe data for API response."""

    id: int
    name: str
    servings: int
    has_error: bool
    error_message: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None  # Comma-separated string


class RecipeDetailResponse(BaseModel):
    """Full recipe detail for viewing."""

    id: int
    name: str
    servings: int
    raw_content: str
    html_content: str
    timers: list[dict]
    has_error: bool
    error_message: Optional[str] = None


class RecipeSelection(BaseModel):
    """Recipe selection with target servings."""

    recipe_id: int
    target_servings: int


class ShoppingListRequest(BaseModel):
    """Request body for generating shopping list."""

    selections: list[RecipeSelection]
    include_pantry: list[str] = []
    additional_items: list[str] = []


class ShoppingListResponse(BaseModel):
    """Shopping list response."""

    shopping_items: list[dict]
    pantry_items: list[str]
    formatted_text: str


class ScanResponse(BaseModel):
    """Response from recipe scan."""

    added: list[str]
    updated: list[str]
    deleted: list[str]
    errors: list[str]


class UploadRecipeRequest(BaseModel):
    """Request body for uploading a new recipe."""

    filename: str
    content: str


class UploadRecipeResponse(BaseModel):
    """Response from recipe upload."""

    filename: str
    message: str


@router.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy"}


@router.get("/recipes", response_model=list[RecipeResponse])
async def list_recipes():
    """Get all recipes."""
    recipes = get_all_recipes()
    return [
        RecipeResponse(
            id=r.id,
            name=r.name,
            servings=r.servings,
            has_error=r.parse_error is not None,
            error_message=r.parse_error,
            category=r.category,
            tags=r.tags,
        )
        for r in recipes
    ]


@router.get("/additional-items")
async def list_additional_items():
    """Get list of additional non-recipe shopping items."""
    return {"items": get_additional_items()}


@router.get("/config")
async def get_config():
    """Get runtime configuration for frontend."""
    return {
        "datadog": {
            "applicationId": os.environ.get("DD_RUM_APP_ID", ""),
            "clientToken": os.environ.get("DD_RUM_CLIENT_TOKEN", ""),
            "service": os.environ.get("DD_RUM_SERVICE", "kitchen-companion"),
            "env": os.environ.get("DD_RUM_ENV", "production"),
            "version": os.environ.get("DD_RUM_VERSION", "1.0.0"),
            "enabled": bool(os.environ.get("DD_RUM_APP_ID") and os.environ.get("DD_RUM_CLIENT_TOKEN")),
        }
    }


@router.get("/recipes/{recipe_id}", response_model=RecipeDetailResponse)
async def get_recipe(recipe_id: int):
    """Get recipe details including HTML for email and timer metadata."""
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Process content for timers
    content_with_timers, detected_timers = inject_timer_buttons(recipe.raw_content)

    # Convert to HTML
    html_content = recipe_to_html(recipe.raw_content)

    return RecipeDetailResponse(
        id=recipe.id,
        name=recipe.name,
        servings=recipe.servings,
        raw_content=recipe.raw_content,
        html_content=html_content,
        timers=detected_timers,
        has_error=recipe.parse_error is not None,
        error_message=recipe.parse_error,
    )


@router.post("/shopping-list", response_model=ShoppingListResponse)
async def generate_shopping_list(request: ShoppingListRequest):
    """Generate combined shopping list from selected recipes."""
    # Check if we have any selections at all
    if not request.selections and not request.additional_items:
        return ShoppingListResponse(
            shopping_items=[],
            pantry_items=[],
            formatted_text="",
        )

    combined = []
    
    # Process recipe ingredients if any recipes selected
    if request.selections:
        # Get recipe info for servings calculation
        recipe_ids = [s.recipe_id for s in request.selections]
        recipes = {r.id: r for r in get_all_recipes() if r.id in recipe_ids}

        # Calculate multipliers
        multipliers = {}
        for sel in request.selections:
            recipe = recipes.get(sel.recipe_id)
            if recipe:
                if recipe.servings > 0:
                    multipliers[sel.recipe_id] = sel.target_servings / recipe.servings
                else:
                    multipliers[sel.recipe_id] = 1.0  # Default to no scaling

        # Get ingredients
        ingredients = get_ingredients_for_recipes(recipe_ids)
        ingredient_dicts = [
            {
                "recipe_id": i.recipe_id,
                "quantity": i.quantity,
                "unit": i.unit,
                "name": i.name,
            }
            for i in ingredients
        ]

        # Combine ingredients
        combined = combine_ingredients(ingredient_dicts, multipliers)

    # Filter pantry items
    shopping_items, pantry_items = filter_pantry_items(combined)
    
    # Add selected additional items (with zones)
    from src.services.categories import get_category, sort_by_category
    
    for item in request.additional_items:
        zone = get_category(item)
        shopping_items.append({
            "name": item,
            "quantity": None,
            "unit": None,
            "display": item,
            "category": zone,
        })
    
    # Re-sort all items by zone after adding additional items
    shopping_items = sort_by_category(shopping_items)

    # Format text output
    formatted_text = shopping_list_to_text(shopping_items, request.include_pantry)

    return ShoppingListResponse(
        shopping_items=shopping_items,
        pantry_items=pantry_items,
        formatted_text=formatted_text,
    )


@router.post("/refresh", response_model=ScanResponse)
async def refresh_recipes():
    """Rescan recipes folder and update database."""
    reload_pantry()
    reload_categories()
    reload_additional_items()
    results = scan_recipes()
    return ScanResponse(**results)


MAX_RECIPE_CONTENT_LENGTH = 100_000  # 100KB


@router.post("/recipes/upload", response_model=UploadRecipeResponse)
async def upload_recipe(request: UploadRecipeRequest):
    """Upload a new recipe to the recipes folder."""
    filename = request.filename.strip()
    content = request.content

    # Validate filename
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Validate content length
    if len(content) > MAX_RECIPE_CONTENT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Recipe content too large (max {MAX_RECIPE_CONTENT_LENGTH // 1000}KB)"
        )

    # Ensure .md extension
    if not filename.endswith('.md'):
        filename += '.md'

    # Sanitize filename (allow only alphanumeric, dash, underscore)
    safe_filename = re.sub(r'[^a-zA-Z0-9\-_.]', '-', filename)
    if safe_filename.startswith('00-'):
        raise HTTPException(
            status_code=400,
            detail="Filename cannot start with '00-' (reserved for templates)"
        )

    # Validate content has ingredients section
    if '## ingredients' not in content.lower():
        raise HTTPException(
            status_code=400,
            detail="Recipe must have an '## Ingredients' section"
        )

    # Check if file already exists
    filepath = os.path.join(RECIPES_PATH, safe_filename)
    if os.path.exists(filepath):
        raise HTTPException(
            status_code=400,
            detail=f"Recipe '{safe_filename}' already exists"
        )

    # Write file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save recipe: {e}"
        )

    return UploadRecipeResponse(
        filename=safe_filename,
        message=f"Recipe '{safe_filename}' saved successfully"
    )


@router.get("/events")
async def recipe_update_events():
    """Server-Sent Events endpoint for recipe updates."""
    async def event_generator():
        queue = asyncio.Queue(maxsize=10)
        recipe_update_subscribers.append(queue)

        try:
            while True:
                # Send heartbeat every 30 seconds to keep connection alive
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {event['type']}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            raise
        finally:
            if queue in recipe_update_subscribers:
                recipe_update_subscribers.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
