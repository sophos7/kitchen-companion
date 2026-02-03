"""Main FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.models.database import init_db
from src.services.scanner import scan_recipes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and scan recipes on startup."""
    init_db()
    scan_recipes()
    yield


app = FastAPI(
    title="Kitchen Companion",
    description="Recipe management, cooking view, and shopping list generation",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")

static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
