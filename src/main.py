"""Main FastAPI application entry point."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.routes import router, notify_recipe_update
from src.models.database import init_db
from src.services.scanner import scan_recipes, RECIPES_PATH
from src.services.watcher import RecipeWatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global watcher instance
watcher = None


def on_recipe_change():
    """Handle recipe file changes."""
    scan_recipes()
    notify_recipe_update()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database, scan recipes, and start file watcher on startup."""
    global watcher
    
    # Initialize database and scan recipes
    init_db()
    scan_recipes()
    
    # Start file watcher
    try:
        watcher = RecipeWatcher(RECIPES_PATH, on_recipe_change)
        watcher.start()
        logger.info("File watcher enabled - recipes will auto-refresh on changes")
    except Exception as e:
        logger.warning(f"File watcher could not be started: {e}")
        logger.info("Continuing without file watching - use manual refresh")
    
    yield
    
    # Cleanup
    if watcher:
        watcher.stop()


app = FastAPI(
    title="Kitchen Companion",
    description="Recipe management, cooking view, and shopping list generation",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")

static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
