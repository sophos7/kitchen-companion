"""Tests for src/services/git_status.py."""

import os
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def isolated_recipes_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Point RECIPES_PATH at a fresh temp directory with a clean status cache."""
    recipes_dir = tmp_path / "recipes"
    recipes_dir.mkdir()

    monkeypatch.setenv("RECIPES_PATH", str(recipes_dir))

    from src.services import git_status

    git_status.invalidate_cache()
    yield recipes_dir
    git_status.invalidate_cache()


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
        },
    )


def _init_repo(path: Path) -> None:
    _git(path, "init", "-q", "-b", "main")
    (path / ".gitkeep").write_text("")
    _git(path, "add", ".gitkeep")
    _git(path, "commit", "-q", "-m", "initial")


def test_returns_unavailable_when_not_a_git_repo(isolated_recipes_dir: Path) -> None:
    from src.services.git_status import get_recipe_git_status

    status = get_recipe_git_status()

    assert status["available"] is False
    assert status["clean"] is True
    assert status["untracked_count"] == 0


def test_returns_unavailable_when_recipes_dir_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RECIPES_PATH", str(tmp_path / "does-not-exist"))

    from src.services import git_status

    git_status.invalidate_cache()
    status = git_status.get_recipe_git_status()

    assert status["available"] is False
    assert status["clean"] is True


def test_clean_repo_reports_clean(isolated_recipes_dir: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git binary not available")

    _init_repo(isolated_recipes_dir)

    from src.services.git_status import get_recipe_git_status, invalidate_cache

    invalidate_cache()
    status = get_recipe_git_status()

    assert status["available"] is True
    assert status["clean"] is True
    assert status["untracked_count"] == 0
    assert status["modified_count"] == 0
    assert status["deleted_count"] == 0


def test_untracked_recipe_is_reported(isolated_recipes_dir: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git binary not available")

    _init_repo(isolated_recipes_dir)
    (isolated_recipes_dir / "new-dish.md").write_text("# New Dish\n")

    from src.services.git_status import get_recipe_git_status, invalidate_cache

    invalidate_cache()
    status = get_recipe_git_status()

    assert status["available"] is True
    assert status["clean"] is False
    assert status["untracked_count"] == 1
    assert "new-dish.md" in status["untracked"]
    assert status["modified_count"] == 0
    assert status["deleted_count"] == 0


def test_modified_and_deleted_files_reported(isolated_recipes_dir: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git binary not available")

    _init_repo(isolated_recipes_dir)
    tracked_modified = isolated_recipes_dir / "kept.md"
    tracked_modified.write_text("original\n")
    tracked_deleted = isolated_recipes_dir / "gone.md"
    tracked_deleted.write_text("doomed\n")
    _git(isolated_recipes_dir, "add", "kept.md", "gone.md")
    _git(isolated_recipes_dir, "commit", "-q", "-m", "seed")

    tracked_modified.write_text("changed\n")
    tracked_deleted.unlink()

    from src.services.git_status import get_recipe_git_status, invalidate_cache

    invalidate_cache()
    status = get_recipe_git_status()

    assert status["available"] is True
    assert status["clean"] is False
    assert status["modified_count"] == 1
    assert status["deleted_count"] == 1
    assert status["untracked_count"] == 0


def test_untracked_list_is_capped_to_20(isolated_recipes_dir: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git binary not available")

    _init_repo(isolated_recipes_dir)
    for i in range(25):
        (isolated_recipes_dir / f"recipe-{i:02d}.md").write_text(f"# Recipe {i}\n")

    from src.services.git_status import get_recipe_git_status, invalidate_cache

    invalidate_cache()
    status = get_recipe_git_status()

    assert status["untracked_count"] == 25
    assert len(status["untracked"]) == 20


def test_cache_returns_same_value_within_ttl(isolated_recipes_dir: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git binary not available")

    _init_repo(isolated_recipes_dir)

    from src.services.git_status import get_recipe_git_status, invalidate_cache

    invalidate_cache()
    first = get_recipe_git_status()

    (isolated_recipes_dir / "added-after-cache.md").write_text("# Hidden\n")
    cached = get_recipe_git_status()

    assert cached == first
    assert cached["clean"] is True

    invalidate_cache()
    fresh = get_recipe_git_status()
    assert fresh["clean"] is False
    assert fresh["untracked_count"] == 1
