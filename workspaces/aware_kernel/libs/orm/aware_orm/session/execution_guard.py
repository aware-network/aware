"""Execution guardrails for domain/runtime boundaries.

The canonical runtime contract is:
- Domain handlers only mutate in-memory state.
- The runtime owns persistence staging and transaction commits.

This module provides a lightweight ContextVar-based mechanism so runtimes can
enforce "handlers never push" without depending on stack inspection.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Iterator
from uuid import UUID


@dataclass(frozen=True)
class ConstructorCreateScope:
    """Typed authority for recording one constructor-created root instance."""

    target_class_config_id: UUID
    expected_instance_id: UUID
    target_function_config_id: UUID | None = None
    parent_relationship_config_id: UUID | None = None


_push_allowed: ContextVar[bool] = ContextVar("aware_orm_push_allowed", default=True)
_domain_create_allowed: ContextVar[bool] = ContextVar("aware_orm_domain_create_allowed", default=False)
_constructor_create_scope: ContextVar[ConstructorCreateScope | None] = ContextVar(
    "aware_orm_constructor_create_scope",
    default=None,
)
_mutation_owner_id: ContextVar[UUID | None] = ContextVar("aware_orm_mutation_owner_id", default=None)
_execution_mode: ContextVar[str | None] = ContextVar("aware_orm_execution_mode", default=None)
# Relationship propagation guard (used by runtime persistence staging).
_propagation_allowed: ContextVar[bool] = ContextVar("aware_orm_relationship_propagation_allowed", default=True)
# Per-invocation read-only barrier.
#
# `scoped_execution_mode("read")` must enforce read-only semantics even when
# nested inside a write execution scope (write dominates for DB-read policies).
_read_only_depth: ContextVar[int] = ContextVar("aware_orm_read_only_depth", default=0)


def is_push_allowed() -> bool:
    return bool(_push_allowed.get())


def set_push_allowed(value: bool) -> Token[bool]:
    return _push_allowed.set(bool(value))


def reset_push_allowed(token: Token[bool]) -> None:
    _push_allowed.reset(token)


def is_domain_create_allowed() -> bool:
    return bool(_domain_create_allowed.get())


def current_constructor_create_scope() -> ConstructorCreateScope | None:
    return _constructor_create_scope.get()


def set_domain_create_allowed(value: bool) -> Token[bool]:
    return _domain_create_allowed.set(bool(value))


def reset_domain_create_allowed(token: Token[bool]) -> None:
    _domain_create_allowed.reset(token)


def set_constructor_create_scope(
    value: ConstructorCreateScope | None,
) -> Token[ConstructorCreateScope | None]:
    return _constructor_create_scope.set(value)


def reset_constructor_create_scope(token: Token[ConstructorCreateScope | None]) -> None:
    _constructor_create_scope.reset(token)


def current_mutation_owner() -> UUID | None:
    return _mutation_owner_id.get()


def set_mutation_owner(owner_id: UUID | None) -> Token[UUID | None]:
    return _mutation_owner_id.set(owner_id)


def reset_mutation_owner(token: Token[UUID | None]) -> None:
    _mutation_owner_id.reset(token)


def is_relationship_propagation_allowed() -> bool:
    return bool(_propagation_allowed.get())


def set_relationship_propagation_allowed(value: bool) -> Token[bool]:
    return _propagation_allowed.set(bool(value))


def reset_relationship_propagation_allowed(token: Token[bool]) -> None:
    _propagation_allowed.reset(token)


def current_execution_mode() -> str | None:
    """Return the current runtime execution mode (\"read\" | \"write\"), if any."""
    value = _execution_mode.get()
    if value is None:
        return None
    if value not in {"read", "write"}:
        raise ValueError(f"Invalid execution mode value: {value!r}")
    return value


def is_read_only_scope() -> bool:
    """Return True when executing within a read-only function invocation scope."""
    return int(_read_only_depth.get() or 0) > 0


def _enter_read_only_scope() -> Token[int]:
    depth = int(_read_only_depth.get() or 0)
    return _read_only_depth.set(depth + 1)


def _exit_read_only_scope(token: Token[int]) -> None:
    _read_only_depth.reset(token)


def _set_execution_mode(mode: str) -> Token[str | None]:
    if mode not in {"read", "write"}:
        raise ValueError(f"Invalid execution mode: {mode!r}")
    return _execution_mode.set(mode)


def _reset_execution_mode(token: Token[str | None]) -> None:
    _execution_mode.reset(token)


@contextmanager
def scoped_execution_mode(mode: str) -> Iterator[None]:
    """Scope runtime execution semantics across nested function calls.

    Rules (canonical, v0):
    - Top-level calls set the mode based on the invoked FunctionConfig.verb.
    - Nested calls may not escalate from \"read\" → \"write\".
    - Nested calls may not relax from \"write\" → \"read\" (\"write\" dominates).
    """
    current = _execution_mode.get()
    if current is None:
        token = _set_execution_mode(mode)
        read_token: Token[int] | None = None
        if mode == "read":
            read_token = _enter_read_only_scope()
        try:
            yield
        finally:
            if read_token is not None:
                _exit_read_only_scope(read_token)
            _reset_execution_mode(token)
        return

    if current not in {"read", "write"}:
        raise ValueError(f"Invalid execution mode value: {current!r}")
    if mode not in {"read", "write"}:
        raise ValueError(f"Invalid execution mode: {mode!r}")

    # A read-only invocation is always a barrier for nested write calls, even when
    # nested inside a write scope (write dominates the global execution mode).
    if mode == "write" and is_read_only_scope():
        raise PermissionError("Write function invocation is not allowed inside a read-only function invocation scope.")

    if current == "read" and mode == "write":
        raise PermissionError("Write function invocation is not allowed inside a read-only execution scope.")

    # Keep the existing mode (\"write\" dominates) for nested scopes, but track
    # read-only barriers for nested read invocations.
    read_token = None
    if mode == "read":
        read_token = _enter_read_only_scope()
    try:
        yield
    finally:
        if read_token is not None:
            _exit_read_only_scope(read_token)


@contextmanager
def disallow_push() -> Iterator[None]:
    """Disallow `ORMModel.push()` for the duration of the context."""
    token = set_push_allowed(False)
    try:
        yield
    finally:
        reset_push_allowed(token)


@contextmanager
def allow_push() -> Iterator[None]:
    """Allow `ORMModel.push()` for the duration of the context."""
    token = set_push_allowed(True)
    try:
        yield
    finally:
        reset_push_allowed(token)


@contextmanager
def suppress_relationship_propagation() -> Iterator[None]:
    """Disable RelationshipMixin.propagate_ids() during persistence staging."""
    token = set_relationship_propagation_allowed(False)
    try:
        yield
    finally:
        reset_relationship_propagation_allowed(token)


@contextmanager
def allow_domain_create() -> Iterator[None]:
    """Allow domain ORM models to be created inside a runtime execution scope."""
    token = set_domain_create_allowed(True)
    try:
        yield
    finally:
        reset_domain_create_allowed(token)


@contextmanager
def allow_constructor_create(
    *,
    target_class_config_id: UUID,
    expected_instance_id: UUID,
    target_function_config_id: UUID | None = None,
    parent_relationship_config_id: UUID | None = None,
) -> Iterator[None]:
    """Allow exactly the invoked constructor's resolved root instance to be recorded."""
    scope = ConstructorCreateScope(
        target_class_config_id=target_class_config_id,
        expected_instance_id=expected_instance_id,
        target_function_config_id=target_function_config_id,
        parent_relationship_config_id=parent_relationship_config_id,
    )
    scope_token = set_constructor_create_scope(scope)
    create_token = set_domain_create_allowed(True)
    try:
        yield
    finally:
        reset_domain_create_allowed(create_token)
        reset_constructor_create_scope(scope_token)


@contextmanager
def disallow_domain_create() -> Iterator[None]:
    """Disallow domain ORM model creation inside a runtime execution scope."""
    token = set_domain_create_allowed(False)
    try:
        yield
    finally:
        reset_domain_create_allowed(token)


__all__ = [
    "ConstructorCreateScope",
    "allow_constructor_create",
    "allow_domain_create",
    "allow_push",
    "current_constructor_create_scope",
    "current_execution_mode",
    "current_mutation_owner",
    "disallow_domain_create",
    "disallow_push",
    "is_read_only_scope",
    "is_relationship_propagation_allowed",
    "is_domain_create_allowed",
    "is_push_allowed",
    "reset_mutation_owner",
    "reset_constructor_create_scope",
    "reset_domain_create_allowed",
    "reset_push_allowed",
    "suppress_relationship_propagation",
    "scoped_execution_mode",
    "set_constructor_create_scope",
    "set_mutation_owner",
    "set_domain_create_allowed",
    "set_push_allowed",
]
