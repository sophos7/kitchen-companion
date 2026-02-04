"""File system watcher for automatic recipe updates."""

import logging
import threading
from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class RecipeFileHandler(FileSystemEventHandler):
    """Handler for recipe file system events."""

    def __init__(self, on_change_callback: Callable[[], None], debounce_seconds: float = 1.0):
        """Initialize the handler.

        Args:
            on_change_callback: Function to call when changes are detected
            debounce_seconds: Delay before triggering callback to group rapid changes
        """
        self.on_change_callback = on_change_callback
        self.debounce_seconds = debounce_seconds
        self._debounce_timer = None
        self._lock = threading.Lock()

    def _trigger_callback(self):
        """Trigger the callback after debounce delay."""
        with self._lock:
            if self._debounce_timer:
                self._debounce_timer.cancel()

            self._debounce_timer = threading.Timer(
                self.debounce_seconds,
                self._execute_callback
            )
            self._debounce_timer.daemon = True  # Don't block process exit
            self._debounce_timer.start()

    def _execute_callback(self):
        """Execute the callback."""
        try:
            logger.info("Recipe file changes detected, triggering refresh")
            self.on_change_callback()
        except Exception as e:
            logger.error(f"Error in file watcher callback: {e}")

    def on_any_event(self, event: FileSystemEvent):
        """Handle any file system event."""
        # Ignore directory events and non-.md files
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix != '.md':
            return

        # Ignore template files
        if path.name.startswith('00-'):
            return

        # Ignore hidden files and temporary files
        if path.name.startswith('.') or path.name.endswith('~'):
            return

        logger.debug(f"Recipe file event: {event.event_type} - {event.src_path}")
        self._trigger_callback()


class RecipeWatcher:
    """Watches the recipes directory for changes."""

    def __init__(self, recipes_path: str, on_change_callback: Callable[[], None]):
        """Initialize the watcher.

        Args:
            recipes_path: Path to the recipes directory
            on_change_callback: Function to call when changes are detected
        """
        self.recipes_path = recipes_path
        self.observer = Observer()
        self.observer.daemon = True  # Don't block process exit
        self.handler = RecipeFileHandler(on_change_callback)
        self._started = False

    def start(self):
        """Start watching the recipes directory."""
        if self._started:
            logger.warning("Recipe watcher already started")
            return

        try:
            self.observer.schedule(self.handler, self.recipes_path, recursive=False)
            self.observer.start()
            self._started = True
            logger.info(f"Recipe watcher started for: {self.recipes_path}")
        except Exception as e:
            logger.error(f"Failed to start recipe watcher: {e}")

    def stop(self):
        """Stop watching the recipes directory."""
        if not self._started:
            return

        try:
            # Cancel any pending debounce timer
            with self.handler._lock:
                if self.handler._debounce_timer:
                    self.handler._debounce_timer.cancel()
                    self.handler._debounce_timer = None

            self.observer.stop()
            self.observer.join(timeout=2)
            self._started = False
            logger.info("Recipe watcher stopped")
        except Exception as e:
            logger.error(f"Error stopping recipe watcher: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
