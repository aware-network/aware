"""
Session module for ORM operations.

This module provides session management, context resolution, and Unit of Work patterns.
"""

from .session import Session, create_session, switch_session, scratch_uow
from .session_context import SessionContext
from .current_session_ctx import (
    current_session,
    current_session_context,
    current_branch_id,
    set_session_context,
    set_session,
    switch_session_context,
    has_session_context,
    require_session_context,
)
from aware_orm.cache.identity_map import (
    IdentityMap,
    SessionScopedIdentityMap,
    global_identity_map_registry,
)

__all__ = [
    "Session",
    "SessionContext",
    "create_session",
    "switch_session",
    "scratch_uow",
    "current_session",
    "current_session_context",
    "current_branch_id",
    "set_session_context",
    "set_session",
    "switch_session_context",
    "has_session_context",
    "require_session_context",
    "IdentityMap",
    "SessionScopedIdentityMap",
    "global_identity_map_registry",
]
