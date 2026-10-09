"""
File System Change Events for Cache Coordination.

This module defines the event system for coordinating cache invalidation
across multiple index components.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Set, Optional, Dict, Any
import logging

from aware_file_system.models import ChangeType

logger = logging.getLogger(__name__)


@dataclass
class FileSystemChangeEvent:
    """Event representing file system changes detected by any component."""

    change_type: ChangeType  # CREATE, UPDATE, DELETE, MOVE
    affected_paths: Set[str]  # Relative paths affected
    timestamp: datetime  # When change was detected
    source_component: str  # Which component detected change
    additional_context: Optional[Dict[str, Any]] = None  # Extra metadata if needed

    def get_cache_invalidation_scope(self) -> Set[str]:
        """
        Determine which cache entries need invalidation.

        Strategy:
        - For file changes: invalidate file + parent directory caches
        - For directory changes: invalidate directory + all children
        - Conservative approach to ensure cache coherence

        Returns:
            Set of relative paths that need cache invalidation
        """
        scope = self.affected_paths.copy()

        for path in self.affected_paths:
            try:
                path_obj = Path(path)

                # Add parent directories for file changes
                parent = str(path_obj.parent)
                if parent != "." and parent != path:
                    scope.add(parent)

                # For directory changes, we'll let the coordinator handle
                # child invalidation based on its cache knowledge

            except Exception as e:
                logger.warning(f"Error calculating invalidation scope for {path}: {e}")
                # Conservative fallback: just the path itself
                continue

        logger.debug(f"Cache invalidation scope: {len(scope)} paths for {len(self.affected_paths)} changes")
        return scope

    def is_directory_change(self) -> bool:
        """Check if this event represents directory-level changes."""
        # Simple heuristic: if any path doesn't have an extension, assume directory
        for path in self.affected_paths:
            if not Path(path).suffix:
                return True
        return False

    def get_affected_directories(self) -> Set[str]:
        """Get all directory paths that might be affected by this change."""
        directories = set()

        for path in self.affected_paths:
            try:
                path_obj = Path(path)

                # Add parent directory
                parent = str(path_obj.parent)
                if parent != ".":
                    directories.add(parent)

                # If path itself appears to be a directory, add it
                if not path_obj.suffix:
                    directories.add(path)

            except Exception as e:
                logger.warning(f"Error extracting directories from {path}: {e}")
                continue

        return directories

    def __str__(self) -> str:
        """Human-readable representation of the event."""
        return (
            f"FileSystemChangeEvent(type={self.change_type.value}, "
            f"paths={len(self.affected_paths)}, source={self.source_component})"
        )


class EventEmitter:
    """Helper class for components to emit file system change events."""

    def __init__(self, component_name: str):
        self.component_name = component_name
        self.event_handlers = []

    def add_handler(self, handler):
        """Add an event handler (typically a CacheCoordinator)."""
        self.event_handlers.append(handler)

    def emit_change_event(
        self,
        change_type: ChangeType,
        affected_paths: Set[str],
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit a file system change event to all registered handlers."""
        if not self.event_handlers:
            return  # No handlers registered, nothing to do

        event = FileSystemChangeEvent(
            change_type=change_type,
            affected_paths=affected_paths,
            timestamp=datetime.now(),
            source_component=self.component_name,
            additional_context=additional_context,
        )

        for handler in self.event_handlers:
            try:
                handler.handle_change_event(event)
            except Exception as e:
                logger.error(f"Error in event handler {handler}: {e}")

        logger.debug(f"Emitted {event} to {len(self.event_handlers)} handlers")
