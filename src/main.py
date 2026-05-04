"""Main FastAPI application entry point."""

import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router, notify_recipe_update
from src.models.database import init_db
from src.services.scanner import scan_recipes, RECIPES_PATH
from src.services.watcher import RecipeWatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

watcher = None

_scan_lock = threading.Lock()

BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")


def on_recipe_change():
    """Handle recipe file changes."""
    with _scan_lock:
        scan_recipes()
        notify_recipe_update()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database, scan recipes, and start file watcher on startup."""
    global watcher

    init_db()
    scan_recipes()

    try:
        watcher = RecipeWatcher(RECIPES_PATH, on_recipe_change)
        watcher.start()
        logger.info("File watcher enabled - recipes will auto-refresh on changes")
    except Exception as e:
        logger.warning(f"File watcher could not be started: {e}")
        logger.info("Continuing without file watching - use manual refresh")

    yield

    if watcher:
        watcher.stop()


app = FastAPI(
    title="Kitchen Companion",
    description="Recipe management, cooking view, and shopping list generation",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix=f"{BASE_PATH}/api")

static_path = os.path.join(os.path.dirname(__file__), "static")
_index_path = os.path.join(static_path, "index.html")


def _render_index() -> str:
    with open(_index_path, "r", encoding="utf-8") as f:
        return f.read().replace("{{BASE_PATH}}", BASE_PATH)


@app.get(f"{BASE_PATH}/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(_render_index())


if BASE_PATH:
    @app.get(BASE_PATH, include_in_schema=False)
    async def index_no_slash() -> RedirectResponse:
        return RedirectResponse(url=f"{BASE_PATH}/")


app.mount(
    BASE_PATH or "/",
    StaticFiles(directory=static_path, html=False),
    name="static",
)
