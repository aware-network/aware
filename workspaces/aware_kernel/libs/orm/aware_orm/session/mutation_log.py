from __future__ import annotations

from contextvars import ContextVar
from typing import Dict, Optional, Set, Tuple
from uuid import UUID

# Session-scoped set of (class_config_id, instance_id) pairs mutated during the operation
_mutation_pairs_ctx: ContextVar[Set[Tuple[UUID, UUID]]] = ContextVar("aware_orm_mutation_pairs", default=set())

# Scoped context: (thread_id, branch_id) -> set of (class_config_id, instance_id)
_current_scope_ctx: ContextVar[Optional[Tuple[UUID, UUID]]] = ContextVar("aware_orm_mutation_scope", default=None)
_scoped_pairs_ctx: ContextVar[Dict[Tuple[UUID, UUID], Set[Tuple[UUID, UUID]]]] = ContextVar(
    "aware_orm_mutation_pairs_scoped", default={}
)


def set_scope(thread_id: Optional[UUID], branch_id: Optional[UUID]) -> None:
    """Set current (thread, branch) scope for mutation tracking. Pass None to clear."""
    if thread_id and branch_id:
        _current_scope_ctx.set((thread_id, branch_id))
    else:
        _current_scope_ctx.set(None)


def get_scope() -> Optional[Tuple[UUID, UUID]]:
    return _current_scope_ctx.get()


def clear_scope() -> None:
    """Clear current scope binding (does not clear stored pairs)."""
    _current_scope_ctx.set(None)


# Back-compat API (unscoped)


def add_pair(class_config_id: UUID, instance_id: UUID) -> None:
    pairs = set(_mutation_pairs_ctx.get() or set())
    pairs.add((class_config_id, instance_id))
    _mutation_pairs_ctx.set(pairs)

    # Also record under current scope, if any
    scope = _current_scope_ctx.get()
    if scope is not None:
        scoped = dict(_scoped_pairs_ctx.get() or {})
        s = set(scoped.get(scope, set()))
        s.add((class_config_id, instance_id))
        scoped[scope] = s
        _scoped_pairs_ctx.set(scoped)


def get_pairs() -> Set[Tuple[UUID, UUID]]:
    return set(_mutation_pairs_ctx.get() or set())


def get_pairs_for_scope(thread_id: UUID, branch_id: UUID) -> Set[Tuple[UUID, UUID]]:
    scoped = _scoped_pairs_ctx.get() or {}
    return set(scoped.get((thread_id, branch_id), set()))


def get_scoped_pairs() -> Dict[Tuple[UUID, UUID], Set[Tuple[UUID, UUID]]]:
    scoped = _scoped_pairs_ctx.get() or {}
    # Return shallow copy to avoid external mutation
    return {k: set(v) for k, v in scoped.items()}


def clear() -> None:
    _mutation_pairs_ctx.set(set())


def clear_for_scope(thread_id: UUID, branch_id: UUID) -> None:
    scoped = dict(_scoped_pairs_ctx.get() or {})
    scoped.pop((thread_id, branch_id), None)
    _scoped_pairs_ctx.set(scoped)
