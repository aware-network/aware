"""
Cache Coordinator for managing cache invalidation across multiple index systems.

This module provides the central coordination logic for synchronizing cache
invalidation between FileSystemIndex and RepositoryIndex components.
"""

from typing import List, Protocol, Set, Optional, Dict, Any
from datetime import datetime
import logging

from aware_file_system.coordination.events import FileSystemChangeEvent

logger = logging.getLogger(__name__)


class CacheableIndex(Protocol):
    """
    Protocol interface for cacheable index components.

    Any index that wants to participate in coordinated cache management
    must implement this interface.
    """

    def invalidate_paths(self, paths: Set[str]) -> None:
        """
        Invalidate cache entries for specific paths.

        Args:
            paths: Set of relative paths that need cache invalidation
        """
        ...

    def invalidate_all(self) -> None:
        """
        Invalidate entire cache (fallback for error conditions).

        This should be used sparingly, only when selective invalidation fails.
        """
        ...


class IndexRegistration:
    """Information about a registered index."""

    def __init__(self, index: CacheableIndex, name: str):
        self.index = index
        self.name = name
        self.registered_at = datetime.now()
        self.invalidation_count = 0
        self.last_invalidation: Optional[datetime] = None
        self.error_count = 0


class CacheCoordinator:
    """
    Central coordinator for cache invalidation across multiple index systems.

    This class receives file system change events and coordinates cache
    invalidation across all registered index components.
    """

    def __init__(self, max_event_history: int = 1000):
        self.registered_indexes: List[IndexRegistration] = []
        self.event_history: List[FileSystemChangeEvent] = []
        self.max_event_history = max_event_history

        # Performance metrics
        self.total_events_processed = 0
        self.total_invalidations_coordinated = 0
        self.last_coordination_time: Optional[datetime] = None

        logger.debug("CacheCoordinator initialized")

    def register_index(self, index: CacheableIndex, name: str) -> None:
        """
        Register an index for coordinated cache management.

        Args:
            index: Index implementing CacheableIndex protocol
            name: Human-readable name for logging and debugging
        """
        registration = IndexRegistration(index, name)
        self.registered_indexes.append(registration)

        logger.debug(f"Registered {name} for cache coordination ({len(self.registered_indexes)} total)")

    def unregister_index(self, index: CacheableIndex) -> bool:
        """
        Unregister an index from coordination.

        Args:
            index: Index to unregister

        Returns:
            True if index was found and removed, False otherwise
        """
        for i, registration in enumerate(self.registered_indexes):
            if registration.index is index:
                removed = self.registered_indexes.pop(i)
                logger.info(f"Unregistered {removed.name} from cache coordination")
                return True

        return False

    def handle_change_event(self, event: FileSystemChangeEvent) -> None:
        """
        Process file system change event and coordinate cache invalidation.

        This is the main coordination method that:
        1. Analyzes the change event
        2. Determines cache invalidation scope
        3. Coordinates invalidation across all registered indexes
        4. Handles errors gracefully with fallback strategies

        Args:
            event: File system change event to process
        """
        if not self.registered_indexes:
            logger.debug("No indexes registered, skipping coordination")
            return

        self.total_events_processed += 1
        self.last_coordination_time = datetime.now()

        # Add to event history (with rotation)
        self.event_history.append(event)
        if len(self.event_history) > self.max_event_history:
            self.event_history.pop(0)

        try:
            # Get cache invalidation scope from the event
            invalidation_scope = event.get_cache_invalidation_scope()

            if not invalidation_scope:
                logger.debug(f"No cache invalidation needed for {event}")
                return

            logger.debug(
                f"Coordinating cache invalidation for {len(invalidation_scope)} paths from {event.source_component}"
            )

            # Coordinate invalidation across all registered indexes
            successful_invalidations = 0
            failed_invalidations = 0

            for registration in self.registered_indexes:
                try:
                    registration.index.invalidate_paths(invalidation_scope)
                    registration.invalidation_count += 1
                    registration.last_invalidation = datetime.now()
                    successful_invalidations += 1

                except Exception as e:
                    logger.warning(f"Cache invalidation failed for {registration.name}: {e}")
                    registration.error_count += 1
                    failed_invalidations += 1

                    # Fallback to full invalidation for safety
                    try:
                        logger.info(f"Attempting full cache invalidation for {registration.name}")
                        registration.index.invalidate_all()
                        successful_invalidations += 1
                    except Exception as fallback_error:
                        logger.error(f"Full cache invalidation also failed for {registration.name}: {fallback_error}")
                        # At this point, we can't help this index - continue with others

            self.total_invalidations_coordinated += successful_invalidations

            if successful_invalidations > 0:
                logger.debug(f"Successfully coordinated cache invalidation: {successful_invalidations} indexes")
            if failed_invalidations > 0:
                logger.warning(f"Failed cache invalidation for {failed_invalidations} indexes")

        except Exception as e:
            logger.error(f"Error in cache coordination for {event}: {e}")
            # Emergency fallback: try to invalidate all caches
            self._emergency_full_invalidation("coordination error")

    def _emergency_full_invalidation(self, reason: str) -> None:
        """
        Emergency fallback: invalidate all caches completely.

        This is used when coordination logic itself fails to ensure
        cache coherence is not compromised.

        Args:
            reason: Human-readable reason for emergency invalidation
        """
        logger.warning(f"Performing emergency full cache invalidation: {reason}")

        for registration in self.registered_indexes:
            try:
                registration.index.invalidate_all()
                logger.debug(f"Emergency invalidation successful for {registration.name}")
            except Exception as e:
                logger.error(f"Emergency invalidation failed for {registration.name}: {e}")
                # Not much we can do at this point except log the error

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get coordination statistics for monitoring and debugging.

        Returns:
            Dictionary with performance and error statistics
        """
        now = datetime.now()

        # Calculate index statistics
        index_stats = []
        for registration in self.registered_indexes:
            stats = {
                "name": registration.name,
                "registered_at": registration.registered_at.isoformat(),
                "invalidation_count": registration.invalidation_count,
                "error_count": registration.error_count,
                "last_invalidation": (
                    registration.last_invalidation.isoformat() if registration.last_invalidation else None
                ),
            }
            index_stats.append(stats)

        return {
            "registered_indexes": len(self.registered_indexes),
            "total_events_processed": self.total_events_processed,
            "total_invalidations_coordinated": self.total_invalidations_coordinated,
            "event_history_size": len(self.event_history),
            "last_coordination_time": (
                self.last_coordination_time.isoformat() if self.last_coordination_time else None
            ),
            "index_statistics": index_stats,
        }

    def get_recent_events(self, limit: Optional[int] = 10) -> List[FileSystemChangeEvent]:
        """
        Get recent change events for debugging.

        Args:
            limit: Maximum number of events to return (None for all)

        Returns:
            List of recent events, most recent first
        """
        events = list(reversed(self.event_history))
        if limit is not None:
            events = events[:limit]
        return events

    def clear_event_history(self) -> int:
        """
        Clear event history to free memory.

        Returns:
            Number of events that were cleared
        """
        count = len(self.event_history)
        self.event_history.clear()
        logger.debug(f"Cleared {count} events from coordination history")
        return count
