from __future__ import annotations

from importlib import import_module
from typing import Protocol, cast
from uuid import UUID

from aware_history.stable_ids import stable_branch_id, stable_portal_branch_id


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


def test_history_wrapper_stable_branch_id_delegates_to_environment_family() -> None:
    environment = cast(
        _EnvironmentBranchingModule,
        cast(object, import_module("aware_environment.branching")),
    )
    environment_id = UUID("00000000-0000-0000-0000-000000000101")
    thread_id = UUID("00000000-0000-0000-0000-000000000202")
    assert stable_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
        key="Provider",
    ) == environment.stable_environment_thread_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
        tail="Provider",
    )


def test_history_wrapper_stable_portal_branch_id_delegates_to_meta_family() -> None:
    meta = cast(
        _MetaProjectionBranchingModule,
        cast(object, import_module("aware_meta.graph.projection.branching")),
    )
    oig_id = UUID("00000000-0000-0000-0000-000000000303")
    opgi_id = UUID("00000000-0000-0000-0000-000000000404")
    target_object_id = UUID("00000000-0000-0000-0000-000000000505")
    assert stable_portal_branch_id(
        object_instance_graph_id=oig_id,
        object_projection_graph_identity_id=opgi_id,
        target_object_id=target_object_id,
    ) == meta.stable_portal_target_branch_id(
        object_instance_graph_id=oig_id,
        object_projection_graph_identity_id=opgi_id,
        target_object_id=target_object_id,
    )
