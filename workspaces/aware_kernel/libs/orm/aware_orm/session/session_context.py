"""
Session Context base class for unified ORM context system.

This provides the essential interface that any context must implement
to work with the ORM system.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aware_orm.session.session import Session
    from aware_history_ontology.branch.branch import Branch


class SessionContext(ABC):
    """
    Abstract base class for contexts that provide ORM session and branch information.

    Both RuntimeContext and EnvironmentConfigContext inherit from this to ensure
    they can work seamlessly with the ORM system.
    """

    @property
    @abstractmethod
    def session(self) -> "Session":
        """Get the active session for this context."""
        pass

    @abstractmethod
    def set_session(self, new_session: "Session") -> "SessionContext":
        """
        Create a new context with the given session.

        This should return a new context instance with the updated session,
        maintaining immutability of the original context.

        Args:
            new_session: The new session to use

        Returns:
            A new SessionContext instance with the updated session
        """
        pass

    @property
    @abstractmethod
    def branch_id(self) -> UUID:
        """Get the branch ID for this context."""
        pass

    @property
    def branch(self) -> "Branch":
        """
        Get the full Branch object (optional convenience method).

        Default implementation creates a Branch from branch_id.
        Contexts can override this if they have the full Branch object available.
        """
        # Lazy import to avoid circular dependencies
        try:
            from aware_history_ontology.branch.branch import Branch

            return Branch(id=self.branch_id)
        except ImportError:
            # Fallback if Branch class not available
            raise NotImplementedError("Branch class not available and no override provided")
