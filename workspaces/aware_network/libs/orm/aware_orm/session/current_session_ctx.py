"""
Current Session Context Helper

This module provides unified access to the current SessionContext, with support for
accessing specific context types when multiple contexts are nested.

This allows scenarios like:
- Editing EnvironmentConfig while testing runtime instances
- Having both RuntimeContext and EnvironmentConfigContext active simultaneously
- Explicit selection between context types when needed
"""

from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, TYPE_CHECKING, Iterator
from uuid import UUID

from aware_orm.session.session_context import SessionContext
from aware_orm._support import logger

if TYPE_CHECKING:
    from aware_orm.session.session import Session

# Optional runtime SessionContext ContextVar injection.
#
# This keeps `aware_orm` independent of any particular runtime package while
# still allowing a runtime to expose its canonical SessionContext (and branch_id)
# to ORM helpers.
_runtime_ctx_var: ContextVar[Any] | None = None


def register_runtime_session_context_var(var: ContextVar[Any]) -> None:
    """Register a runtime-owned ContextVar that stores the active SessionContext."""
    global _runtime_ctx_var
    _runtime_ctx_var = var


def unregister_runtime_session_context_var() -> None:
    """Clear any previously registered runtime SessionContext ContextVar."""
    global _runtime_ctx_var
    _runtime_ctx_var = None


@contextmanager
def use_runtime_session_context_var(var: ContextVar[Any]) -> Iterator[None]:
    """Temporarily install a runtime SessionContext ContextVar (test helper)."""
    global _runtime_ctx_var
    prev = _runtime_ctx_var
    _runtime_ctx_var = var
    try:
        yield
    finally:
        _runtime_ctx_var = prev


# Local SessionContext for tests/CLI/tools that want explicit scoping without
# importing environment/runtime or structure/env contexts.
_local_ctx: ContextVar[SessionContext] = ContextVar("_local_session_ctx")


class LocalSessionContext(SessionContext):
    """Minimal SessionContext implementation for local scoping."""

    def __init__(self, session: "Session", branch_id: UUID | None = None):
        self._session = session
        self._branch_id = branch_id or session.branch_id

    @property
    def session(self) -> "Session":
        return self._session

    def set_session(self, new_session: "Session") -> "LocalSessionContext":
        return LocalSessionContext(new_session, self._branch_id)

    @property
    def branch_id(self) -> UUID:
        return self._branch_id


@contextmanager
def set_session_context(context: SessionContext) -> Iterator[SessionContext]:
    """Set a local SessionContext for the duration of the context manager."""
    token = _local_ctx.set(context)
    try:
        yield context
    finally:
        _local_ctx.reset(token)


@contextmanager
def set_session(session: "Session", *, branch_id: UUID | None = None) -> Iterator[SessionContext]:
    """Set a local SessionContext from a Session (convenience)."""
    ctx = LocalSessionContext(session=session, branch_id=branch_id)
    with set_session_context(ctx) as active:
        yield active


def has_local_session_context() -> bool:
    try:
        _local_ctx.get()
        return True
    except LookupError:
        return False


@contextmanager
def switch_session_in_local_context(new_session: "Session") -> Iterator[SessionContext]:
    """Replace the Session inside the current local SessionContext."""
    try:
        old_ctx = _local_ctx.get()
    except LookupError as exc:
        raise RuntimeError("No local SessionContext available for session switching") from exc

    new_ctx = old_ctx.set_session(new_session)
    token = _local_ctx.set(new_ctx)
    try:
        yield new_ctx
    finally:
        _local_ctx.reset(token)


@contextmanager
def switch_session_context(new_session: "Session") -> Iterator[SessionContext]:
    """Replace the Session in the active ORM SessionContext."""
    runtime_var = _runtime_ctx_var
    if runtime_var is not None:
        ctx = _try_get_context_var(runtime_var)
        if isinstance(ctx, SessionContext):
            token = runtime_var.set(ctx.set_session(new_session))
            try:
                yield runtime_var.get()
            finally:
                runtime_var.reset(token)
            return

    with switch_session_in_local_context(new_session) as ctx:
        yield ctx


def _try_get_context_var(var):
    """Safely try to get a context variable value."""
    try:
        return var.get()
    except LookupError:
        return None


def current_session_context() -> SessionContext | None:
    """
    1 RAIL CANONICAL session context via runtime (if registered).
    """

    runtime_var = _runtime_ctx_var
    if runtime_var is not None:
        ctx = _try_get_context_var(runtime_var)
        if isinstance(ctx, SessionContext):
            return ctx

    # Local SessionContext fallback (tests/CLI/tools).
    ctx = _try_get_context_var(_local_ctx)
    if ctx:
        return ctx

    return None


def current_session() -> Session | None:
    """
    Get the current Session from the runtime context.

    Examples:
        session = current_session()
    """
    ctx = current_session_context()
    if ctx:
        return ctx.session

    return None


def current_branch_id() -> UUID:
    """
    Get the current branch ID from the runtime context.
    """
    ctx = current_session_context()
    if ctx:
        return ctx.branch_id

    # Fallback to main branch if no context
    logger.debug("No SessionContext available, using main branch")
    return UUID("00000000-0000-0000-0000-000000000000")


def has_session_context() -> bool:
    """Check if the SessionContext is currently active."""
    return current_session_context() is not None


def require_session_context() -> SessionContext:
    """
    Ensure a SessionContext is available and return it.

    Raises:
        RuntimeError: If the SessionContext is not available
    """
    ctx = current_session_context()
    if ctx is None:
        raise RuntimeError("No SessionContext available. Code must run within the appropriate context scope.")
    return ctx
