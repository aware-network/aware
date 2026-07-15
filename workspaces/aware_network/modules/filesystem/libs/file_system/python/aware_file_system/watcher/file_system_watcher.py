"""
File System Watcher - Real-time file system monitoring for AWARE.

This module provides real-time file system monitoring with polling-based change detection,
mirroring the successful Dart implementation while integrating with Python's Repository
and ObjectConfigGraph for agent reactivity.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Set, Callable, Any
from enum import Enum

from aware_file_system.config import Config
from aware_file_system.models import FileMetadata, ChangeType, FileType

logger = logging.getLogger(__name__)

DEFAULT_IGNORED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".dylib",
    ".exe",
    ".o",
    ".a",
    ".lib",
    ".jar",
    ".class",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".wav",
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".db",
    ".sqlite",
    ".sqlite3",
}

DEFAULT_IGNORED_DIRS = {
    ".aware",  # Critical: Ignore .aware directory with blobs
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
    "build",
    "dist",
    ".egg-info",
}


class SimpleChangeDetector:
    """Simple change detector without circular imports."""

    @staticmethod
    def detect_changes(
        previous_state: Dict[str, FileMetadata], current_state: Dict[str, FileMetadata]
    ) -> Dict[ChangeType, list]:
        """Detect changes between two file system states."""
        current_files = set(current_state.keys())
        previous_files = set(previous_state.keys())

        changes = {
            ChangeType.create: list(current_files - previous_files),
            ChangeType.delete: list(previous_files - current_files),
            ChangeType.update: [
                file_path
                for file_path in current_files & previous_files
                if current_state[file_path].is_modified(previous_state[file_path])
            ],
        }

        return changes


class FileChangeEvent:
    """Event emitted when file system changes are detected."""

    def __init__(
        self,
        change_type: ChangeType,
        path: str,
        metadata: Optional[FileMetadata] = None,
    ):
        self.change_type = change_type
        self.path = path
        self.metadata = metadata
        if metadata and metadata.last_modified:
            ts = metadata.last_modified
        else:
            ts = datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        else:
            ts = ts.astimezone(timezone.utc)
        self.timestamp = ts

    def __repr__(self):
        return f"FileChangeEvent({self.change_type.name}, {self.path}, {self.timestamp})"


class FileSystemWatcher:
    """
    Real-time file system watcher with polling-based change detection.

    This watcher provides:
    1. Polling-based monitoring (5-second intervals matching Dart)
    2. Change detection for Created/Modified/Deleted files
    3. GitIgnore-style filtering for binary and system files
    4. Integration with Repository and ObjectConfigGraph
    5. Asynchronous event handling for agent reactivity
    """

    def __init__(
        self,
        config: Config,
        poll_interval: float = 5.0,
        cache_dir: Optional[str] = None,
        *,
        use_executor: bool = True,
    ):
        """
        Initialize the file system watcher.

        Args:
            config: Configuration for file system scanning
            poll_interval: Seconds between polls (default 5.0 matching Dart)
            cache_dir: Optional custom cache directory
        """
        self.config = config
        self.poll_interval = poll_interval
        self.root_path = Path(config.file_system.root_path).resolve()

        # We'll use a simplified approach without FileSystemIndex for now
        # to avoid circular imports
        self._cache_dir = cache_dir

        # State tracking
        self._last_state: Dict[str, FileMetadata] = {}
        self._is_running = False
        self._watch_task: Optional[asyncio.Task] = None
        self._initialized = False

        # Event handlers
        self._event_handlers: list[Callable[[FileChangeEvent], Any]] = []
        self._use_executor = use_executor

        # GitIgnore-style filtering (mirrors Dart implementation) with configurable overrides.
        filter_config = getattr(self.config, "filter", None)
        inherit_defaults = True
        custom_extensions: set[str] = set()
        custom_dirs: set[str] = set()

        if filter_config is not None:
            inherit_defaults = getattr(filter_config, "inherit_ignore_defaults", True)
            ext_values = getattr(filter_config, "ignored_extensions", None) or []
            dir_values = getattr(filter_config, "ignored_dirs", None) or []
            custom_extensions = {ext if ext.startswith(".") else f".{ext}" for ext in ext_values}
            custom_dirs = {entry.strip() for entry in dir_values if entry.strip()}

        base_extensions = set(DEFAULT_IGNORED_EXTENSIONS) if inherit_defaults else set()
        base_dirs = set(DEFAULT_IGNORED_DIRS) if inherit_defaults else set()

        self._ignored_extensions = base_extensions | custom_extensions
        self._ignored_dirs = base_dirs | custom_dirs

        logger.info(f"Initialized FileSystemWatcher for {self.root_path} with {poll_interval}s polling")

    def add_event_handler(self, handler: Callable[[FileChangeEvent], Any]) -> None:
        """
        Add an event handler for file change events.

        Args:
            handler: Callable that receives FileChangeEvent objects
        """
        self._event_handlers.append(handler)
        logger.debug(f"Added event handler: {handler}")

    def remove_event_handler(self, handler: Callable[[FileChangeEvent], Any]) -> None:
        """
        Remove an event handler.

        Args:
            handler: The handler to remove
        """
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)
            logger.debug(f"Removed event handler: {handler}")

    async def start(self) -> None:
        """Start watching the file system."""
        if self._is_running:
            logger.warning("FileSystemWatcher is already running")
            return

        # Initial scan to establish baseline
        logger.info("Performing initial file system scan...")
        await self.initialize(force=True)

        self._is_running = True

        # Start the watch loop
        self._watch_task = asyncio.create_task(self._watch_loop())
        logger.info(f"Started FileSystemWatcher with {self.poll_interval}s polling interval")

    async def stop(self) -> None:
        """Stop watching the file system."""
        if not self._is_running:
            logger.warning("FileSystemWatcher is not running")
            return

        self._is_running = False

        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
            self._watch_task = None

        logger.info("Stopped FileSystemWatcher")

    async def initialize(self, force: bool = False) -> None:
        """Perform the initial scan outside of the watch loop."""
        if self._initialized and not force:
            return
        await self._perform_initial_scan()
        self._initialized = True

    async def poll_once(self) -> Dict[ChangeType, list]:
        """
        Trigger a single scan for changes.

        Returns:
            Mapping of ChangeType to affected relative paths.
        """
        if not self._initialized:
            await self.initialize()
        return await self._check_for_changes()

    async def _perform_initial_scan(self) -> None:
        """Perform initial scan to establish baseline state."""
        try:
            # Simplified scanning without FileSystemIndex
            self._last_state = await self._scan_directory()
            logger.info(f"Initial scan complete: tracking {len(self._last_state)} files")

        except Exception as e:
            logger.error(f"Error during initial scan: {e}")
            raise

    async def _scan_directory(self) -> Dict[str, FileMetadata]:
        """Scan directory and build file metadata."""

        def _sync_scan():
            state = {}

            for root, dirs, files in os.walk(self.root_path):
                # Filter directories
                dirs[:] = [d for d in dirs if d not in self._ignored_dirs]

                for file_name in files:
                    file_path = Path(root) / file_name
                    rel_path = file_path.relative_to(self.root_path)
                    rel_path_str = str(rel_path)

                    if not self._should_ignore_file(rel_path_str):
                        try:
                            stat = file_path.stat()
                            metadata = FileMetadata(
                                path=rel_path_str,
                                name=file_name,
                                size=stat.st_size,
                                last_modified=datetime.fromtimestamp(stat.st_mtime),
                                file_type=FileType.TEXT,  # Simplified
                                mime_type="text/plain",  # Simplified
                                depth=len(rel_path.parts),
                                hash="",  # Skip hash for performance
                                content=b"",  # Skip content for performance
                            )
                            state[rel_path_str] = metadata
                        except Exception as e:
                            logger.debug(f"Error scanning {file_path}: {e}")

            return state

        if not self._use_executor:
            return _sync_scan()

        # Run synchronous scan in thread pool
        return await asyncio.to_thread(_sync_scan)

    async def _watch_loop(self) -> None:
        """Main watch loop that polls for changes."""
        while self._is_running:
            try:
                # Wait for poll interval
                await asyncio.sleep(self.poll_interval)

                if not self._is_running:
                    break

                # Check for changes
                await self._check_for_changes()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
                # Continue watching despite errors

    async def _check_for_changes(self) -> Dict[ChangeType, list]:
        """Check for file system changes and emit events."""
        try:
            # Scan current state
            current_state = await self._scan_directory()

            # Detect changes using our simple detector
            changes = SimpleChangeDetector.detect_changes(self._last_state, current_state)

            # Emit events for changes
            await self._emit_change_events(changes, current_state)

            # Update last state
            self._last_state = current_state
            return changes

        except Exception as e:
            logger.error(f"Error checking for changes: {e}")
            return {change_type: [] for change_type in ChangeType}

    async def _emit_change_events(
        self, changes: Dict[ChangeType, list], current_state: Dict[str, FileMetadata]
    ) -> None:
        """
        Emit events for detected changes.

        Args:
            changes: Dictionary of change types to file paths
            current_state: Current file metadata state
        """
        event_count = 0

        # Handle added files
        for file_path in changes.get(ChangeType.create, []):
            event = FileChangeEvent(
                change_type=ChangeType.create,
                path=file_path,
                metadata=current_state.get(file_path),
            )
            await self._notify_handlers(event)
            event_count += 1

        # Handle modified files
        for file_path in changes.get(ChangeType.update, []):
            event = FileChangeEvent(
                change_type=ChangeType.update,
                path=file_path,
                metadata=current_state.get(file_path),
            )
            await self._notify_handlers(event)
            event_count += 1

        # Handle deleted files
        for file_path in changes.get(ChangeType.delete, []):
            event = FileChangeEvent(
                change_type=ChangeType.delete,
                path=file_path,
                metadata=None,  # No metadata for deleted files
            )
            await self._notify_handlers(event)
            event_count += 1

        if event_count > 0:
            logger.debug(f"Emitted {event_count} change events")

    async def _notify_handlers(self, event: FileChangeEvent) -> None:
        """
        Notify all registered handlers of a change event.

        Args:
            event: The file change event to broadcast
        """
        for handler in self._event_handlers:
            try:
                # Support both sync and async handlers
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    await asyncio.to_thread(handler, event)
            except Exception as e:
                logger.error(f"Error in event handler {handler}: {e}")

    def _should_ignore_file(self, rel_path: str) -> bool:
        """
        Check if a file should be ignored based on GitIgnore-style rules.

        Args:
            rel_path: Relative path to check

        Returns:
            True if file should be ignored
        """
        path = Path(rel_path)

        # Check directory exclusions
        for part in path.parts:
            if part in self._ignored_dirs:
                return True

        # Check file extension
        if path.suffix in self._ignored_extensions:
            return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get watcher statistics.

        Returns:
            Dictionary with watcher stats
        """
        return {
            "is_running": self._is_running,
            "files_tracked": len(self._last_state),
            "poll_interval": self.poll_interval,
            "handlers_registered": len(self._event_handlers),
            "root_path": str(self.root_path),
        }


class RepositoryFileSystemWatcher:
    """
    File system watcher specifically integrated with Repository.

    This bridges FileSystemWatcher with Repository for ORM integration.
    """

    def __init__(self, repository, poll_interval: float = 5.0, *, use_executor: bool = True):
        """
        Initialize repository-aware file system watcher.

        Args:
            repository: Repository instance to monitor
            poll_interval: Seconds between polls
        """
        self.repository = repository

        # Create config from repository workspace
        from aware_file_system.config import Config, FileSystemConfig

        config = Config(file_system=FileSystemConfig(root_path=repository.workspace_root, generate_tree=False))

        # Initialize base watcher
        self.watcher = FileSystemWatcher(config, poll_interval=poll_interval, use_executor=use_executor)

        # Register our handler
        self.watcher.add_event_handler(self._handle_file_change)

        logger.info(f"Initialized RepositoryFileSystemWatcher for {repository.name}")

    async def _handle_file_change(self, event: FileChangeEvent) -> None:
        """
        Handle file change events and update Repository.

        This is where file system changes trigger ORM model updates,
        which then propagate to ObjectConfigGraph for agent reactivity.

        Args:
            event: File change event from watcher
        """
        logger.info(f"Repository {self.repository.name}: {event.change_type.name} - {event.path}")

        # Here we would integrate with Repository's change tracking
        # This would trigger:
        # 1. Repository update via ORM models
        # 2. ObjectConfigGraph change propagation
        # 3. Agent reactivity through OIG changes

        # For now, just log the change
        # Full integration would call repository methods like:
        # - await self.repository.apply_file_added(event.path, event.metadata)
        # - await self.repository.apply_file_modified(event.path, event.metadata)
        # - await self.repository.apply_file_deleted(event.path)

    async def start(self) -> None:
        """Start watching the repository."""
        await self.watcher.start()

    async def stop(self) -> None:
        """Stop watching the repository."""
        await self.watcher.stop()

    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics."""
        stats = self.watcher.get_stats()
        stats["repository_name"] = self.repository.name
        stats["repository_workspace"] = self.repository.workspace_root
        return stats
