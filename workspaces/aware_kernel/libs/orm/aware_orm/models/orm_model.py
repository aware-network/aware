"""
Complete ORM Model Implementation

This module provides the complete ORMModel that combines all mixins
to create a full-featured ORM model with:
- Core model functionality (BaseORMModel)
- CRUD operations (CRUDMixin)
- Relationship management (RelationshipMixin)
- Branch awareness (BranchMixin)
- Query convenience methods (QueryMixin)

Also provides convenience classes for common use cases.
"""

from __future__ import annotations

from typing import Self

# Mixins
from aware_orm.models.crud_mixin import CRUDMixin
from aware_orm.models.relationship_mixin import RelationshipMixin
from aware_orm.models.branch_mixin import BranchMixin
from aware_orm.models.query_mixin import QueryMixin

# Execution guard
from aware_orm.session.execution_guard import (
    is_push_allowed,
    is_relationship_propagation_allowed,
)

from aware_orm._support import logger


class ORMModel(QueryMixin, CRUDMixin, RelationshipMixin, BranchMixin):
    """
    Complete modular ORM model combining all functionality.

    This class provides the full ORM feature set by inheriting from all mixins:

    1. BaseORMModel (via QueryMixin): Core attributes (id), ClassConfig binding
    2. QueryMixin: Convenience query methods (get, get_list, get_by_id, etc.)
    3. CRUDMixin: Database persistence (push, upsert, delete_via_session)
    4. RelationshipMixin: Relationship discovery and lazy loading
    5. BranchMixin: Branch awareness and overlay creation

    Usage:
        class User(ORMModel):
            name: str
            email: str

        # Convenience methods (via QueryMixin)
        user = await User.get_by_id(user_id)
        users = await User.get_list(filters=[eq("status", "active")], limit=10, offset=0)
        user = await User.get(field_name="email", field_value="alice@example.com")

        # Persistence (via CRUDMixin)
        user = User(name="Alice", email="alice@example.com")
        await user.push()

        # Session integration
        async with create_session() as session:
            user = User(name="Bob", email="bob@example.com")
            await user.push()  # Queued for transaction
            await session.commit()  # Executed atomically
    """

    # ==================== Enhanced Push with Full Pipeline ====================
    async def push(self) -> None:
        """
        Enhanced push method with full modular support and graceful no-db handling.

        This method leverages the three core capabilities:
        1. Relationship propagation (RelationshipMixin)
        2. ClassConfig-aware persistence (CRUDMixin)
        3. Branch-aware operations (BranchMixin)

        Enhanced with session-level no-database handling for bootstrap scenarios.
        """
        if not is_push_allowed():
            raise PermissionError(
                "Domain handlers must not call ORMModel.push(). "
                "Mutate in-memory state only; the runtime owns persistence staging and commits."
            )
        try:
            # 1. Start propagation (RelationshipMixin)
            self._start_propagation()

            # 2. Propagate IDs through relationships (RelationshipMixin)
            if is_relationship_propagation_allowed():
                self.propagate_ids()

            # 3. Use CRUDMixin for actual persistence
            await super().push()
        except Exception as e:
            logger.error(f"Error in enhanced push for {self.__class__.__name__} {self.id}: {e}")
            raise

    # ==================== Integration Methods ====================
    async def refresh_from_db(self) -> Self:
        """
        Refresh this instance from the database using the repository pattern.
        """
        if not self.id:
            raise ValueError("Cannot refresh instance without ID")

        # Get by id without using the identity map
        refreshed = await self.get_by_id(self.id, cache_valid=False)

        if refreshed:
            # Update this instance with refreshed data
            for field_name, value in refreshed.model_dump().items():
                if not field_name.startswith("_") and hasattr(self, field_name):
                    setattr(self, field_name, value)
            logger.debug(f"Refreshed {self.__class__.__name__} {self.id} from database")
        else:
            logger.warning(f"No data found when refreshing {self.__class__.__name__} {self.id}")

        return self

    def __str__(self) -> str:
        """Enhanced string representation."""
        branch_info = f" (branch: {self.get_branch_id()})" if not self.is_main_branch else ""
        return f"{self.__class__.__name__}(id={self.id}){branch_info}"
