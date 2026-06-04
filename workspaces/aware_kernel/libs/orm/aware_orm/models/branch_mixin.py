"""
Branch Mixin for handling branch-aware operations.

This mixin provides branch awareness and overlay functionality
for in-memory versioning and diff management.
"""

from __future__ import annotations

from typing import Self
from uuid import UUID

# Aware ORM
from aware_orm.helpers import get_main_branch_id, is_main_branch
from aware_orm.models.base_model import BaseORMModel

# Utils
from aware_orm._support import logger


class BranchMixin(BaseORMModel):
    """
    Focused mixin for branch awareness.

    This mixin inherits from BaseORMModel to ensure access to all ORM attributes
    and Pydantic functionality.

    Responsibilities:
    - Branch context management
    - Overlay creation and management
    - Branch-specific loading
    - Diff application

    Provides:
    - self._branch_id attribute (from BaseORMModel)
    - self.id property (from BaseORMModel)
    - model_dump(), model_validate() (from Pydantic via BaseORMModel)
    """

    def get_branch_id(self) -> UUID:
        """Get the branch ID for this instance."""
        try:
            return self._branch_id
        except AttributeError:
            return get_main_branch_id()

    def set_branch_id(self, value: UUID) -> None:
        """Set the branch ID for this instance."""
        self._branch_id = value

    @property
    def is_main_branch(self) -> bool:
        """Check if this instance is on the main branch."""
        return is_main_branch(self.get_branch_id())

    def create_branch_overlay(self, target_branch_id: UUID) -> Self:
        """
        Create a branch overlay of this instance for the target branch.

        Args:
            target_branch_id: The branch ID to create the overlay for

        Returns:
            A new instance with the target branch ID
        """
        # Create a deep copy for the branch overlay using Pydantic model_dump
        # Exclude private attributes by default to prevent session isolation issues
        overlay_data = self.model_dump(exclude_none=False, mode="python")

        # Create new instance using Pydantic model_validate
        overlay = self.__class__.model_validate(overlay_data)

        # Set the branch_id on the overlay (this will set _branch_id via method)
        overlay.set_branch_id(target_branch_id)

        # Mark as not new if based on existing entity
        if not self._is_new:
            overlay._is_new = False

        logger.debug(f"Created branch overlay for {self.__class__.__name__} {self.id} on branch {target_branch_id}")
        return overlay

    @classmethod
    async def load_with_branch_context(
        cls, obj_id: UUID, branch_id: UUID | None = None, cache_valid: bool = True
    ) -> Self | None:
        """
        Load an instance with branch context.

        For main branch: loads directly from database
        For other branches: loads main version and applies branch diffs

        Args:
            obj_id: Object ID to load
            branch_id: Branch to load from (defaults to current context)
            cache_valid: Whether to use cache

        Returns:
            Instance for the specified branch, or None if not found
        """
        from aware_orm.session.current_session_ctx import current_branch_id

        # Determine branch to use
        target_branch = branch_id or current_branch_id()

        # For main branch: load directly
        if is_main_branch(target_branch):
            return await cls._load_main_from_db(obj_id, cache_valid)
        else:
            # For non-main branches: create overlay from main + diffs
            return await cls._load_branch_overlay(obj_id, target_branch, cache_valid)

    @classmethod
    async def _load_main_from_db(cls, obj_id: UUID, cache_valid: bool) -> Self | None:
        """
        Load the main/canonical version from database.

        This should be implemented by the concrete class or a database mixin.
        """
        logger.warning(f"_load_main_from_db not implemented for {cls.__name__}")
        return None

    @classmethod
    async def _load_branch_overlay(cls, obj_id: UUID, branch_id: UUID, cache_valid: bool) -> Self | None:
        """
        Load a branch overlay by applying diffs to the main version.

        Args:
            obj_id: Object ID to load
            branch_id: Target branch ID
            cache_valid: Whether to use cache

        Returns:
            Branch overlay instance or None
        """
        # First, ensure we have the main version
        main_instance = await cls._load_main_from_db(obj_id, cache_valid)
        if main_instance is None:
            return None

        # Create overlay for the target branch
        overlay = main_instance.create_branch_overlay(branch_id)

        # Apply branch-specific diffs
        await cls._apply_branch_diffs_to_instance(overlay, branch_id)

        return overlay

    @classmethod
    async def _apply_branch_diffs_to_instance(cls, instance: BranchMixin, branch_id: UUID) -> None:
        """
        Apply branch-specific diffs to an instance overlay.

        This is a placeholder for future integration with the change/diff system.

        Args:
            instance: The instance to apply diffs to
            branch_id: The branch ID to apply diffs for
        """
        # TODO: Implement when change/diff system is integrated
        # This would:
        # 1. Query object_instance_change records for this branch
        # 2. Walk the change chain to get all diffs
        # 3. Apply attribute changes to the instance
        logger.debug(
            f"Branch diff application not yet implemented for {cls.__name__} " f"{instance.id} on branch {branch_id}"
        )

    def get_branch_lineage(self) -> list[UUID]:
        """
        Get the branch lineage for this instance.

        Returns the chain of branch IDs from main to current branch.
        This is useful for diff application and change tracking.
        """
        # TODO: Implement branch lineage tracking
        # For now, just return main -> current
        if self.is_main_branch:
            return [self.get_branch_id()]
        else:
            return [get_main_branch_id(), self.get_branch_id()]

    def has_branch_changes(self) -> bool:
        """
        Check if this instance has changes relative to the main branch.

        Returns:
            True if there are branch-specific changes
        """
        # TODO: Implement change detection
        # This would compare with main branch version
        return not self.is_main_branch

    async def merge_to_main(self) -> BranchMixin | None:
        """
        Merge this branch instance back to the main branch.

        This would create change records and update the main version.

        Returns:
            Updated main branch instance or None if merge failed
        """
        if self.is_main_branch:
            logger.debug(f"Instance {self.id} already on main branch")
            return self

        # TODO: Implement merge logic
        # This would:
        # 1. Calculate diffs between this instance and main
        # 2. Create change records
        # 3. Apply changes to main branch
        # 4. Return updated main instance

        logger.warning(f"merge_to_main not yet implemented for {self.__class__.__name__}")
        return None

    def create_change_record(self, target_branch_id: UUID | None = None) -> dict:
        """
        Create a change record for this instance relative to another branch.

        Args:
            target_branch_id: Branch to compare against (defaults to main)

        Returns:
            Change record dictionary
        """
        target_branch = target_branch_id or get_main_branch_id()

        # TODO: Implement change record creation
        # This would compare this instance with the target branch version
        # and create a structured diff

        return {
            "source_branch_id": str(self.get_branch_id()),
            "target_branch_id": str(target_branch),
            "object_id": str(self.id),
            "object_type": self.__class__.__name__,
            "changes": {},  # TODO: Calculate actual changes
            "timestamp": None,  # TODO: Add timestamp
        }
