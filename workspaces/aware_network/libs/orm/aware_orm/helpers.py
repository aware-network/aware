"""Branch helper functions for ORM operations."""

from __future__ import annotations

from uuid import UUID


# ==================== Constants ====================

# Main branch UUID constant - replaces _get_main_branch() functions
MAIN_BRANCH_ID = UUID("00000000-0000-0000-0000-000000000000")


def is_main_branch(branch_id: UUID) -> bool:
    """
    Check if a branch ID represents the main branch.

    Args:
        branch_id: The branch ID to check

    Returns:
        True if the branch ID is the main branch, False otherwise
    """
    return branch_id == MAIN_BRANCH_ID


def get_main_branch_id() -> UUID:
    """
    Get the main branch UUID.

    This function replaces the various _get_main_branch() methods.

    Returns:
        The main branch UUID constant
    """
    return MAIN_BRANCH_ID
