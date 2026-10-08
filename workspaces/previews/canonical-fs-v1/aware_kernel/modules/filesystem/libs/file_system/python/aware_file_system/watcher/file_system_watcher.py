"""
File System Watcher - Real-time file system monitoring for AWARE.

This module provides polling-based file system observation over the canonical
``FileSystemIndex`` scanning primitives. Repository lifecycle, semantic resolution,
and graph admission remain responsibilities of callers above this module.
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from aware_file_system.config import Config
from aware_file_system.index.file_metadata_cached import FileMetadataCached
from aware_file_system.index.file_system_index import FileSystemIndex
from aware_file_system.models import ChangeType, FileMetadata

logger = logging.getLogger(__name__)


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
        return (
            f"FileChangeEvent({self.change_type.name}, {self.path}, {self.timestamp})"
        )


class FileSystemWatcher:
    """
    Real-time file system watcher with polling-based change detection.

    This watcher provides:
    1. Polling-based monitoring (5-second intervals matching Dart)
    2. Change detection for Created/Modified/Deleted files
    3. One injectable ``FileSystemIndex`` scan/index/filter implementation
    4. Asynchronous event handling for an owning observer
    """

    def __init__(
        self,
        config: Config,
        poll_interval: float = 5.0,
        cache_dir: Optional[str] = None,
        *,
        use_executor: bool = True,
        index: Optional[FileSystemIndex] = None,
    ):
        """
        Initialize the file system watcher.

        Args:
            config: Configuration for file system scanning
            poll_interval: Seconds between polls (default 5.0 matching Dart)
            cache_dir: Optional custom cache directory
            index: Optional shared index. Its root must match ``config``.
        """
        self.config = config
        self.poll_interval = poll_interval
        self.root_path = Path(config.file_system.root_path).resolve()

        if index is not None and index.root_path != self.root_path:
            raise ValueError(
                "FileSystemWatcher index root does not match watcher root: "
                f"{index.root_path} != {self.root_path}"
            )
        self.index = index or FileSystemIndex(config, cache_dir=cache_dir)

        # State tracking
        self._last_state: Dict[str, FileMetadata] = {}
        self._is_running = False
        self._watch_task: Optional[asyncio.Task] = None
        self._initialized = False

        # Event handlers
        self._event_handlers: list[Callable[[FileChangeEvent], Any]] = []
        self._use_executor = use_executor

        logger.info(
            f"Initialized FileSystemWatcher for {self.root_path} with {poll_interval}s polling"
        )

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
        logger.info(
            f"Started FileSystemWatcher with {self.poll_interval}s polling interval"
        )

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
            _changes, self._last_state = await self._refresh_index()
            logger.info(
                f"Initial scan complete: tracking {len(self._last_state)} files"
            )

        except Exception as e:
            logger.error(f"Error during initial scan: {e}")
            raise

    async def _refresh_index(
        self,
    ) -> tuple[Dict[ChangeType, list], Dict[str, FileMetadata]]:
        """Refresh the shared index and return its delta plus lightweight metadata."""

        def refresh() -> tuple[Dict[ChangeType, list], Dict[str, FileMetadata]]:
            scan_result, cached_state = self.index.refresh_relative_metadata()
            state = {
                path: _observation_metadata(metadata)
                for path, metadata in cached_state.items()
            }
            changes = {
                ChangeType.create: sorted(scan_result.added),
                ChangeType.update: sorted(scan_result.modified),
                ChangeType.delete: sorted(scan_result.deleted),
            }
            return changes, state

        if not self._use_executor:
            return refresh()
        return await asyncio.to_thread(refresh)

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
        changes, current_state = await self._refresh_index()
        await self._emit_change_events(changes, current_state)
        self._last_state = current_state
        return changes

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
    Legacy convenience wrapper that derives a watcher root from a repository.

    The wrapper has no ORM, graph, or semantic-update behavior. New lifecycle
    owners should construct ``FileSystemWatcher`` directly with an injected
    ``FileSystemIndex``.
    """

    def __init__(
        self, repository, poll_interval: float = 5.0, *, use_executor: bool = True
    ):
        """
        Initialize repository-aware file system watcher.

        Args:
            repository: Repository instance to monitor
            poll_interval: Seconds between polls
        """
        self.repository = repository

        # Create config from repository workspace
        from aware_file_system.config import Config, FileSystemConfig

        config = Config(
            file_system=FileSystemConfig(
                root_path=repository.workspace_root, generate_tree=False
            )
        )

        # Initialize base watcher
        self.watcher = FileSystemWatcher(
            config, poll_interval=poll_interval, use_executor=use_executor
        )

        # Register our handler
        self.watcher.add_event_handler(self._handle_file_change)

        logger.info(f"Initialized RepositoryFileSystemWatcher for {repository.name}")

    async def _handle_file_change(self, event: FileChangeEvent) -> None:
        """
        Record a compatibility-level repository change notification.

        Args:
            event: File change event from watcher
        """
        logger.info(
            f"Repository {self.repository.name}: {event.change_type.name} - {event.path}"
        )

        # Repository semantics deliberately remain outside FileSystem.

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


def _observation_metadata(metadata: FileMetadataCached) -> FileMetadata:
    """Convert cached stat metadata without reading or hashing file content."""
    return FileMetadata(
        path=metadata.path,
        name=metadata.name,
        size=metadata.size,
        last_modified=metadata.last_modified,
        file_type=metadata.file_type,
        mime_type=metadata.mime_type,
        depth=metadata.depth,
        hash=metadata.hash or "",
        content=b"",
    )
