from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphExecutionSessionDelta,
    MetaGraphHandlerExecutionRequest,
    MetaGraphPreState,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from uuid import UUID


class MetaGraphExecutionSessionDeltaError(RuntimeError):
    """Raised when Meta cannot safely build execution-session delta evidence."""


@dataclass(frozen=True, slots=True)
class MetaGraphExecutionSessionDeltaBuilder:
    """Build typed execution-session deltas from Meta-owned graph evidence."""

    def build_delta_from_changes(
        self,
        *,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        changes: Iterable[ObjectInstanceGraphChange],
        expected_graph_hash_post: str | None = None,
        root_object_id: UUID | None = None,
        root_class_instance_identity_id: UUID | None = None,
        constructed_class_instance_ids: Iterable[UUID] = (),
    ) -> MetaGraphExecutionSessionDelta:
        _validate_session_delta_inputs(request=request, pre_state=pre_state)
        change_tuple = tuple(changes)
        _validate_changes_target_pre_state_oig(
            pre_state=pre_state,
            changes=change_tuple,
        )
        post_oig = pre_state.before_oig.model_copy(deep=True)
        apply_object_instance_graph_changes(
            graph=post_oig,
            changes=change_tuple,
            attribute_configs_by_id=request.execution_plan.index.attribute_configs_by_id,
            class_configs_by_id=request.execution_plan.index.class_configs_by_id,
        )
        graph_hash_post = _compute_post_hash(
            post_oig=post_oig,
            expected_graph_hash_post=expected_graph_hash_post,
        )
        return MetaGraphExecutionSessionDelta(
            execution_plan=request.execution_plan,
            before_oig=pre_state.before_oig,
            changes=change_tuple,
            graph_hash_pre=pre_state.graph_hash_pre,
            graph_hash_post=graph_hash_post,
            root_object_id=root_object_id or pre_state.root_object_id,
            root_class_instance_identity_id=(
                root_class_instance_identity_id
                or pre_state.root_class_instance_identity_id
            ),
            target_class_instance_id=pre_state.target_object_id,
            constructed_class_instance_ids=tuple(constructed_class_instance_ids),
        )

    def build_delta_from_post_oig(
        self,
        *,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        post_oig: ObjectInstanceGraph,
        expected_graph_hash_post: str | None = None,
        root_object_id: UUID | None = None,
        root_class_instance_identity_id: UUID | None = None,
        constructed_class_instance_ids: Iterable[UUID] = (),
    ) -> MetaGraphExecutionSessionDelta:
        _validate_session_delta_inputs(request=request, pre_state=pre_state)
        if post_oig.id != pre_state.before_oig.id:
            raise MetaGraphExecutionSessionDeltaError(
                "Meta execution-session post-OIG evidence targets a different "
                "ObjectInstanceGraph."
            )
        graph_hash_post = _compute_post_hash(
            post_oig=post_oig,
            expected_graph_hash_post=expected_graph_hash_post,
        )
        changes = tuple(
            diff_object_instance_graph_changes(
                old=pre_state.before_oig,
                new=post_oig,
                object_instance_graph_identity_id=(
                    request.staged_call.lane_scope.object_instance_graph_identity_id
                ),
            )
        )
        return MetaGraphExecutionSessionDelta(
            execution_plan=request.execution_plan,
            before_oig=pre_state.before_oig,
            changes=changes,
            graph_hash_pre=pre_state.graph_hash_pre,
            graph_hash_post=graph_hash_post,
            root_object_id=root_object_id or pre_state.root_object_id,
            root_class_instance_identity_id=(
                root_class_instance_identity_id
                or pre_state.root_class_instance_identity_id
            ),
            target_class_instance_id=pre_state.target_object_id,
            constructed_class_instance_ids=tuple(constructed_class_instance_ids),
        )


def _validate_session_delta_inputs(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
) -> None:
    if pre_state.execution_plan is not request.execution_plan:
        raise MetaGraphExecutionSessionDeltaError(
            "Meta execution-session delta requires pre-state from the same "
            "execution plan."
        )


def _validate_changes_target_pre_state_oig(
    *,
    pre_state: MetaGraphPreState,
    changes: tuple[ObjectInstanceGraphChange, ...],
) -> None:
    before_oig_id = pre_state.before_oig.id
    for change in changes:
        if change.object_instance_graph_id != before_oig_id:
            raise MetaGraphExecutionSessionDeltaError(
                "Meta execution-session change targets a different "
                "ObjectInstanceGraph."
            )


def _compute_post_hash(
    *,
    post_oig: ObjectInstanceGraph,
    expected_graph_hash_post: str | None,
) -> str:
    graph_hash_post = compute_hash(post_oig, index=build_index(post_oig))
    if expected_graph_hash_post is not None and graph_hash_post != expected_graph_hash_post:
        raise MetaGraphExecutionSessionDeltaError(
            "Meta execution-session post hash mismatch: "
            f"have={graph_hash_post} expected={expected_graph_hash_post}"
        )
    return graph_hash_post


__all__ = [
    "MetaGraphExecutionSessionDeltaBuilder",
    "MetaGraphExecutionSessionDeltaError",
]
