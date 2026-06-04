# -----
# !!! TODO: REMOVE !!!!!!
"""
Common helper functions for ORM operations.

This module contains canonical implementations of utility functions that were
previously duplicated across multiple ORM modules. By centralizing these
functions, we ensure consistency and avoid drift between implementations.
"""

from __future__ import annotations
from typing import Any
from uuid import UUID
from datetime import datetime

from aware_orm._support import logger


# ==================== Constants ====================

# Main branch UUID constant - replaces _get_main_branch() functions
MAIN_BRANCH_ID = UUID("00000000-0000-0000-0000-000000000000")


# ==================== Utility Functions ====================


def collect_primitive_and_enum_values_fallback(model) -> dict[str, Any]:
    """
    Fallback method to collect primitive values when SQL metadata is unavailable.

    This is the canonical implementation that replaces all the duplicated
    _collect_primitive_and_enum_values_fallback() methods across the codebase.

    Uses Pydantic model data with sensible filtering to extract database-suitable values.

    Args:
        model: The model instance to extract values from

    Returns:
        Dictionary of field names to primitive values suitable for database storage
    """
    logger.debug(f"Using fallback primitive value collection for {model.__class__.__name__}")

    # Get all model data if model_dump is available
    if hasattr(model, "model_dump"):
        model_data = model.model_dump(exclude_none=False, exclude_unset=False)
    elif hasattr(model, "__dict__"):
        model_data = model.__dict__
    else:
        logger.warning(f"Cannot extract data from {model.__class__.__name__} - no model_dump or __dict__")
        return {}

    values = {}

    # Filter to reasonable database columns
    for field_name, value in model_data.items():
        # Skip private attributes
        if field_name.startswith("_"):
            continue

        # Skip complex objects and lists (likely relationships)
        if isinstance(value, (dict, list)):
            continue

        # Convert UUID to string for database storage
        if isinstance(value, UUID):
            value = str(value)

        # Include basic types that can be stored in database
        # datetime objects should be included for DateTime fields
        if value is None or isinstance(value, (str, int, float, bool, datetime)):
            values[field_name] = value
            logger.debug(f"Fallback: Added {field_name} = {value}")
        else:
            logger.debug(f"Fallback: Skipping field {field_name} due to type: {type(value)}")

    logger.debug(f"Fallback collected {len(values)} values: {list(values.keys())}")
    return values


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
