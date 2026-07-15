# Standard Imports
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from aware_meta.runtime.handler_context import current_handler_context
from aware_orm.session.current_session_ctx import (
    current_session_context,
    set_session,
    switch_session_context,
)


@dataclass(frozen=True, slots=True)
class IdentityInvocationContext:
    """Identity-owned view of the active domain invocation context."""

    actor_id: UUID
    environment_id: UUID | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    object_instance_graph_branch_id: UUID | None = None


_CURRENT_IDENTITY_INVOCATION_CONTEXT: ContextVar[IdentityInvocationContext | None] = (
    ContextVar(
        "aware_identity_invocation_context",
        default=None,
    )
)


def current_actor_id() -> UUID:
    """Return the current actor_id or raise if missing."""
    actor_id = current_invocation_context().actor_id
    if actor_id is None:
        raise PermissionError("ActorContext missing: actor_id not set")
    return actor_id


def current_branch_id() -> UUID:
    """Return the current domain branch id or raise if missing."""

    branch_id = current_invocation_context().branch_id
    if branch_id is None:
        raise PermissionError("InvocationContext missing: branch_id not set")
    return branch_id


def current_invocation_context() -> IdentityInvocationContext:
    """
    Resolve Identity's active invocation context.

    Identity-owned callers may provide an explicit Identity context scope.
    Meta-generated handlers expose Meta handler context as the fallback.
    """

    identity_context = _CURRENT_IDENTITY_INVOCATION_CONTEXT.get()
    if identity_context is not None:
        return identity_context

    meta_context = _current_meta_invocation_context()
    if meta_context is not None:
        return meta_context

    raise RuntimeError(
        "No Identity invocation context set. Code must run under Meta handler "
        "context or scoped_identity_invocation_context()."
    )


def current_identity_id() -> UUID:
    """Identity is not part of canonical runtime context (resolve via identity lane)."""
    raise PermissionError(
        "Identity is not available in RuntimeContext; resolve identity_id via the identity lane (commit truth)."
    )


@contextmanager
def switch_identity_session(session: Any) -> Iterator[None]:
    """Scope Identity writes to the provided ORM branch session."""

    if current_session_context() is None:
        with set_session(
            session, branch_id=_optional_uuid(getattr(session, "branch_id", None))
        ):
            yield
        return

    with switch_session_context(session):
        yield


@contextmanager
def scoped_identity_invocation_context(
    context: IdentityInvocationContext,
) -> Iterator[IdentityInvocationContext]:
    """Set Identity invocation context for non-handler tests and transitional callers."""

    token = _CURRENT_IDENTITY_INVOCATION_CONTEXT.set(context)
    try:
        yield context
    finally:
        _CURRENT_IDENTITY_INVOCATION_CONTEXT.reset(token)


def _current_meta_invocation_context() -> IdentityInvocationContext | None:
    try:
        context = current_handler_context()
    except RuntimeError:
        return None
    actor_id = _required_uuid(getattr(context, "requester_id", None), "requester_id")
    return IdentityInvocationContext(
        actor_id=actor_id,
        environment_id=_optional_uuid(getattr(context, "environment_id", None)),
        process_id=_optional_uuid(getattr(context, "process_id", None)),
        thread_id=_optional_uuid(getattr(context, "thread_id", None)),
        branch_id=_optional_uuid(getattr(context, "branch_id", None)),
        object_instance_graph_branch_id=_optional_uuid(
            getattr(context, "domain_oigb_id", None),
        ),
    )


def _required_uuid(value: Any, label: str) -> UUID:
    result = _optional_uuid(value)
    if result is None:
        raise PermissionError(f"InvocationContext missing: {label} not set")
    return result


def _optional_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


__all__ = [
    "IdentityInvocationContext",
    "current_actor_id",
    "current_branch_id",
    "current_identity_id",
    "current_invocation_context",
    "scoped_identity_invocation_context",
    "switch_identity_session",
]
