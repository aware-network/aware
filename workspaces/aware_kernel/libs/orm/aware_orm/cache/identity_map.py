"""
Identity Map implementation for object identity management.

This module provides identity mapping functionality to ensure
that only one instance of any object exists per session.
"""

# @doc-ref: ../../docs/cache/identity_map.md
# @test-ref: ../../tests/cache/test_identity_map.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from aware_orm._support import logger
from aware_orm.helpers import MAIN_BRANCH_ID

if TYPE_CHECKING:
    from aware_orm.models.base_model import BaseORMModel

# Type variable for generic model types
T = TypeVar("T", bound="BaseORMModel")


class IdentityMap:
    """
    Identity map for ensuring object identity within a session.

    The identity map ensures that only one instance of any object
    exists within a session scope, preventing inconsistencies and
    ensuring referential integrity.

    Works with BranchMixin-based objects to support branch overlays.
    """

    def __init__(self):
        """Initialize empty identity map."""
        # Use strong references for session-scoped objects
        self._objects: dict[tuple[type, UUID], BaseORMModel] = {}

    def get(self, cls: type[T], obj_id: UUID) -> T | None:
        """
        Get an object from the identity map.

        Args:
            cls: The class type
            obj_id: The object ID

        Returns:
            The cached object instance or None if not found
        """
        key = (cls, obj_id)
        obj = self._objects.get(key)

        if obj:
            logger.debug(f"Retrieved {cls.__name__} {obj_id} from identity map")
            return obj

        return None

    def add(self, obj: BaseORMModel) -> None:
        """
        Add an object to the identity map.

        Args:
            obj: The object to add (must be a BaseORMModel-based object)
        """
        if not hasattr(obj, "id") or not hasattr(obj, "__class__"):
            logger.warning(f"Cannot add object without id or class to identity map: {obj}")
            return

        obj_id = getattr(obj, "id")
        if not obj_id:
            logger.warning(f"Cannot add object with None id to identity map: {obj}")
            return

        cls = obj.__class__
        key = (cls, obj_id)

        # Check if already exists
        existing = self._objects.get(key)
        if existing and existing is not obj:
            # ==================== SMART IDENTITY CONFLICT DETECTION ====================
            # Check if the objects have identical data before warning
            if hasattr(obj, "is_data_identical") and hasattr(existing, "is_data_identical"):
                if obj.is_data_identical(existing):
                    # Objects have identical data - this is normal during deserialization
                    logger.debug(
                        f"Identity map: {cls.__name__} {obj_id} has identical data to existing instance - using existing"
                    )
                    # Keep the existing instance to maintain referential integrity
                    return
                else:
                    # Objects have different data - this is a real conflict
                    # !! WARNING: SILENCED FOR NOW - CAREFUL
                    logger.debug(
                        f"Identity conflict for {cls.__name__} {obj_id}: data differs, replacing existing instance"
                    )
                    logger.debug(f"  Existing hash: {existing.get_data_hash()[:8]}...")
                    logger.debug(f"  New hash: {obj.get_data_hash()[:8]}...")
            else:
                # Fallback to old behavior for objects without data comparison
                logger.warning(
                    f"Identity conflict for {cls.__name__} {obj_id}: replacing existing instance (no data comparison available)"
                )

        self._objects[key] = obj

        logger.debug(f"Added {cls.__name__} {obj_id} to identity map")

    def remove(self, cls: type, obj_id: UUID) -> BaseORMModel | None:
        """
        Remove an object from the identity map.

        Args:
            cls: The class type
            obj_id: The object ID

        Returns:
            The removed object or None if not found
        """
        key = (cls, obj_id)
        obj = self._objects.pop(key, None)

        if obj:
            logger.debug(f"Removed {cls.__name__} {obj_id} from identity map")

        return obj

    def contains(self, cls: type, obj_id: UUID) -> bool:
        """
        Check if an object is in the identity map.

        Args:
            cls: The class type
            obj_id: The object ID

        Returns:
            True if the object is cached
        """
        key = (cls, obj_id)
        return key in self._objects

    def clear(self) -> None:
        """Clear all objects from the identity map."""
        count = len(self._objects)
        self._objects.clear()
        logger.debug(f"Cleared identity map ({count} objects)")

    def size(self) -> int:
        """Get the number of objects in the identity map."""
        return len(self._objects)

    def get_all_objects(self) -> list[BaseORMModel]:
        """Get all objects in the identity map."""
        return list(self._objects.values())

    def get_objects_by_type(self, cls: type[T]) -> list[T]:
        """
        Get all objects of a specific type.

        Args:
            cls: The class type to filter by

        Returns:
            List of objects of the specified type
        """
        result = []
        for (obj_cls, obj_id), obj in self._objects.items():
            if obj_cls == cls:
                result.append(obj)  # type: ignore
        return result

    def get_statistics(self) -> dict[str, Any]:
        """
        Get statistics about the identity map.

        Returns:
            Dictionary with statistics
        """
        type_counts = {}
        for (obj_cls, obj_id), obj in self._objects.items():
            type_name = obj_cls.__name__
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            "total_objects": len(self._objects),
            "type_counts": type_counts,
        }

    def _cache_key(self, cls: type, obj_id: UUID) -> tuple[type, UUID]:
        """Create identity map cache key from (cls, obj_id)."""
        return (cls, obj_id)


class SessionScopedIdentityMap(IdentityMap):
    """
    Session-scoped identity map that includes branch awareness.

    This identity map is aware of branch context and can isolate
    objects by branch when needed.
    """

    def __init__(self, branch_id: UUID | None = None):
        """
        Initialize session-scoped identity map.

        Args:
            branch_id: The branch ID this identity map is scoped to
        """
        super().__init__()
        self.branch_id = branch_id or MAIN_BRANCH_ID

    def get_branch_id(self) -> UUID:
        """Get the branch ID for this identity map."""
        return self.branch_id

    def is_main_branch(self) -> bool:
        """Check if this identity map is for the main branch."""
        return self.branch_id == MAIN_BRANCH_ID

    def add(self, obj: BaseORMModel) -> None:
        """
        Add an object to the identity map with branch awareness.

        The object's branch_id should match this identity map's branch_id
        for proper isolation.
        """
        # Check branch compatibility if object has branch awareness
        obj_branch_id = obj.get_branch_id()
        if obj_branch_id != self.branch_id:
            logger.warning(
                f"Object: {obj.__class__.__name__} {obj.id} branch {obj_branch_id} differs from identity map branch {self.branch_id}. "
                f"Adding anyway for session management."
            )

        # Call parent add method (which now has smart conflict detection)
        super().add(obj)

    def merge_from_main(self, main_identity_map: SessionScopedIdentityMap) -> None:
        """
        Merge objects from the main branch identity map.

        This is useful for creating branch overlays that include
        objects from the main branch.

        Args:
            main_identity_map: The main branch identity map to merge from
        """
        if not main_identity_map.is_main_branch():
            logger.warning("merge_from_main called with non-main branch identity map")
            return

        merged_count = 0
        for (cls, obj_id), obj in main_identity_map._objects.items():
            # Only merge if we don't already have this object
            if not self.contains(cls, obj_id):
                # Create branch overlay using BranchMixin functionality if available
                if hasattr(obj, "create_branch_overlay"):
                    overlay = obj.create_branch_overlay(self.branch_id)
                    self.add(overlay)
                    merged_count += 1
                else:
                    # If no branch overlay capability, just add as-is
                    self.add(obj)
                    merged_count += 1

        logger.debug(f"Merged {merged_count} objects from main branch to branch {self.branch_id}")

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics including branch information."""
        stats = super().get_statistics()
        stats["branch_id"] = str(self.branch_id)
        stats["is_main_branch"] = self.is_main_branch()
        return stats


class GlobalIdentityMapRegistry:
    """
    Global registry for identity maps across different sessions and branches.

    This is primarily for debugging and monitoring purposes.
    """

    def __init__(self):
        self._session_maps: dict[str, IdentityMap] = {}

    def register_session_map(self, session_id: str, identity_map: IdentityMap) -> None:
        """Register an identity map for a session."""
        self._session_maps[session_id] = identity_map
        logger.debug(f"Registered identity map for session {session_id}")

    def unregister_session_map(self, session_id: str) -> None:
        """Unregister an identity map for a session."""
        if session_id in self._session_maps:
            del self._session_maps[session_id]
            logger.debug(f"Unregistered identity map for session {session_id}")

    def get_session_map(self, session_id: str) -> IdentityMap | None:
        """Get the identity map for a session."""
        return self._session_maps.get(session_id)

    def get_global_statistics(self) -> dict[str, Any]:
        """Get statistics for all registered identity maps."""
        stats = {"total_sessions": len(self._session_maps), "sessions": {}}

        total_objects = 0
        for session_id, identity_map in self._session_maps.items():
            session_stats = identity_map.get_statistics()
            stats["sessions"][session_id] = session_stats
            total_objects += session_stats["total_objects"]

        stats["total_objects_across_sessions"] = total_objects
        return stats

    def clear_all(self) -> None:
        """Clear all registered identity maps."""
        for identity_map in self._session_maps.values():
            identity_map.clear()
        self._session_maps.clear()
        logger.debug("Cleared all identity maps from global registry")


# Global registry instance
global_identity_map_registry = GlobalIdentityMapRegistry()
