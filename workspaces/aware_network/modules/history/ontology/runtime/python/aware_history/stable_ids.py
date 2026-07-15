from __future__ import annotations

"""History stable-id helpers on the compiler-owned rail.

Compatibility policy:
- History owns identity primitives (`stable_branch_id(key)`, `stable_lane_id`, ...).
- Higher-level branch families are module-owned (for example environment/meta).
- This module keeps compatibility wrappers while delegating branch-family formulas.
"""

from importlib import import_module
from typing import Protocol, cast
from uuid import UUID

from aware_history_ontology.stable_ids import (
    NS_HISTORY,
    stable_commit_parent_id as _stable_commit_parent_id,
    stable_lane_id,
)


class _EnvironmentBranchingModule(Protocol):
    def stable_environment_thread_branch_id(
        self, *, environment_id: UUID, thread_id: UUID, tail: str | None = None
    ) -> UUID: ...


class _MetaProjectionBranchingModule(Protocol):
    def stable_portal_target_branch_id(
        self,
        *,
        object_instance_graph_id: UUID,
        object_projection_graph_identity_id: UUID,
        target_object_id: UUID,
    ) -> UUID: ...


def stable_branch_id(*, environment_id: UUID, thread_id: UUID, key: str | None = None) -> UUID:
    """Compatibility adapter for module-owned environment/thread branch family."""
    module = cast(
        _EnvironmentBranchingModule,
        cast(object, import_module("aware_environment.branching")),
    )

    return module.stable_environment_thread_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
        tail=key,
    )


def stable_portal_branch_id(
    *,
    object_instance_graph_id: UUID,
    object_projection_graph_identity_id: UUID,
    target_object_id: UUID,
) -> UUID:
    """Compatibility adapter for module-owned portal branch family."""
    module = cast(
        _MetaProjectionBranchingModule,
        cast(object, import_module("aware_meta.graph.projection.branching")),
    )

    return module.stable_portal_target_branch_id(
        object_instance_graph_id=object_instance_graph_id,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        target_object_id=target_object_id,
    )


def stable_commit_parent_id(
    *,
    commit_id: UUID | None = None,
    parent_commit_id: UUID | None = None,
    parent_id: UUID | None = None,
    child_id: UUID | None = None,
) -> UUID:
    """Compatibility adapter for renamed identity parameters."""
    resolved_commit_id = commit_id or child_id
    if resolved_commit_id is None:
        raise ValueError("stable_commit_parent_id requires commit_id (or legacy child_id)")
    resolved_parent_commit_id = parent_commit_id or parent_id
    if resolved_parent_commit_id is None:
        raise ValueError("stable_commit_parent_id requires parent_commit_id (or legacy parent_id)")
    try:
        return _stable_commit_parent_id(
            commit_id=resolved_commit_id,
            parent_commit_id=resolved_parent_commit_id,
        )
    except TypeError:
        return _stable_commit_parent_id(
            commit_id=resolved_commit_id,
            parent_id=resolved_parent_commit_id,
        )


__all__ = [
    "NS_HISTORY",
    "stable_branch_id",
    "stable_lane_id",
    "stable_portal_branch_id",
    "stable_commit_parent_id",
]
