"""Read-only git status check for the recipes directory.

Surfaces uncommitted changes in the recipes directory so the UI can
remind the user to commit and push from the host. The app itself
never runs git write operations.
"""

import logging
import os
import subprocess
import time

logger = logging.getLogger(__name__)


def _recipes_path() -> str:
    """Resolved at call time so tests can monkeypatch RECIPES_PATH."""
    return os.environ.get("RECIPES_PATH", "recipes")

GIT_TIMEOUT_SECONDS = 3
CACHE_TTL_SECONDS = 5
MAX_FILES_IN_RESPONSE = 20

_cache: dict | None = None
_cache_expires_at: float = 0.0


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=_recipes_path(),
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def _parse_porcelain(stdout: str) -> tuple[list[str], list[str], list[str]]:
    """Parse `git status --porcelain=v1` output into (untracked, modified, deleted)."""
    untracked: list[str] = []
    modified: list[str] = []
    deleted: list[str] = []

    for line in stdout.splitlines():
        if len(line) < 3:
            continue
        code, path = line[:2], line[3:]

        # Renames have format "R  old -> new"; only the new path is reported.
        if " -> " in path:
            path = path.split(" -> ", 1)[1]

        if code == "??":
            untracked.append(path)
        elif "D" in code:
            deleted.append(path)
        else:
            modified.append(path)

    return untracked, modified, deleted


def _build_unavailable_response() -> dict:
    return {
        "available": False,
        "clean": True,
        "untracked_count": 0,
        "modified_count": 0,
        "deleted_count": 0,
        "untracked": [],
    }


def _compute_status() -> dict:
    if not os.path.isdir(_recipes_path()):
        return _build_unavailable_response()

    try:
        check = _run_git(["rev-parse", "--is-inside-work-tree"])
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.debug("git unavailable for recipes status: %s", exc)
        return _build_unavailable_response()

    if check.returncode != 0 or check.stdout.strip() != "true":
        return _build_unavailable_response()

    try:
        result = _run_git(["status", "--porcelain=v1", "--untracked-files=normal"])
    except subprocess.TimeoutExpired:
        logger.warning("git status timed out for recipes path")
        return _build_unavailable_response()

    if result.returncode != 0:
        logger.warning("git status failed: %s", result.stderr.strip())
        return _build_unavailable_response()

    untracked, modified, deleted = _parse_porcelain(result.stdout)

    return {
        "available": True,
        "clean": not (untracked or modified or deleted),
        "untracked_count": len(untracked),
        "modified_count": len(modified),
        "deleted_count": len(deleted),
        "untracked": sorted(untracked)[:MAX_FILES_IN_RESPONSE],
    }


def get_recipe_git_status() -> dict:
    """Return a snapshot of the recipes directory's git status.

    Result is cached briefly to avoid spawning git on every poll. The
    cache is process-local so it does not survive restarts.
    """
    global _cache, _cache_expires_at

    now = time.monotonic()
    if _cache is not None and now < _cache_expires_at:
        return _cache

    status = _compute_status()
    _cache = status
    _cache_expires_at = now + CACHE_TTL_SECONDS
    return status


def invalidate_cache() -> None:
    """Clear the cached status so the next call recomputes immediately."""
    global _cache, _cache_expires_at
    _cache = None
    _cache_expires_at = 0.0
