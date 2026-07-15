from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.commit.perf_trace import commit_perf_span
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphExecutionSessionDelta,
    MetaGraphHandlerExecutionRequest,
    MetaGraphMaterializationCachePrimeSnapshot,
    MetaGraphPreState,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_history_ontology.change.change_enums import ChangeType
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
            materialization_cache_prime_snapshot=_materialization_cache_prime_snapshot(
                request=request,
                post_oig=post_oig,
                graph_hash_post=graph_hash_post,
            ),
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
        metadata = _session_delta_trace_metadata(request)
        with commit_perf_span(
            phase="handler_execution.session_delta.diff_post_oig",
            category="meta.runtime.handler_execution",
            metadata=metadata,
        ):
            changes = tuple(
                diff_object_instance_graph_changes(
                    old=pre_state.before_oig,
                    new=post_oig,
                    object_instance_graph_identity_id=(
                        request.staged_call.lane_scope.object_instance_graph_identity_id
                    ),
                )
            )
        if _can_hash_constructor_post_oig_directly(request=request):
            with commit_perf_span(
                phase="handler_execution.session_delta.constructor_post_oig_hash",
                category="meta.runtime.handler_execution",
                metadata=metadata,
            ):
                graph_hash_post = _compute_post_hash(
                    post_oig=post_oig,
                    expected_graph_hash_post=expected_graph_hash_post,
                )
            cache_prime_post_oig = post_oig
        else:
            with commit_perf_span(
                phase="handler_execution.session_delta.scope_post_oig_changes",
                category="meta.runtime.handler_execution",
                metadata=metadata,
            ):
                scoped_changes = _scope_instance_call_changes(
                    request=request,
                    pre_state=pre_state,
                    changes=changes,
                    constructed_class_instance_ids=tuple(constructed_class_instance_ids),
                )
                changes = scoped_changes.changes
            if scoped_changes.filtered:
                with commit_perf_span(
                    phase=(
                        "handler_execution.session_delta."
                        "apply_scoped_changes_for_hash"
                    ),
                    category="meta.runtime.handler_execution",
                    metadata=metadata,
                ):
                    scoped_post_oig = pre_state.before_oig.model_copy(deep=True)
                    apply_object_instance_graph_changes(
                        graph=scoped_post_oig,
                        changes=changes,
                        attribute_configs_by_id=(
                            request.execution_plan.index.attribute_configs_by_id
                        ),
                        class_configs_by_id=(
                            request.execution_plan.index.class_configs_by_id
                        ),
                    )
                with commit_perf_span(
                    phase="handler_execution.session_delta.hash_scoped_post_oig",
                    category="meta.runtime.handler_execution",
                    metadata=metadata,
                ):
                    graph_hash_post = _compute_post_hash(
                        post_oig=scoped_post_oig,
                        expected_graph_hash_post=expected_graph_hash_post,
                    )
                cache_prime_post_oig = scoped_post_oig
            else:
                with commit_perf_span(
                    phase=(
                        "handler_execution.session_delta."
                        "scoped_post_oig_hash_direct"
                    ),
                    category="meta.runtime.handler_execution",
                    metadata=metadata,
                ):
                    graph_hash_post = _compute_post_hash(
                        post_oig=post_oig,
                        expected_graph_hash_post=expected_graph_hash_post,
                    )
                cache_prime_post_oig = post_oig
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
            materialization_cache_prime_snapshot=_materialization_cache_prime_snapshot(
                request=request,
                post_oig=cache_prime_post_oig,
                graph_hash_post=graph_hash_post,
            ),
        )


@dataclass(frozen=True, slots=True)
class _ScopedInstanceCallChanges:
    changes: tuple[ObjectInstanceGraphChange, ...]
    filtered: bool


def _scope_instance_call_changes(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    changes: tuple[ObjectInstanceGraphChange, ...],
    constructed_class_instance_ids: tuple[UUID, ...],
) -> _ScopedInstanceCallChanges:
    if request.execution_plan.implementation.is_constructor:
        return _ScopedInstanceCallChanges(changes=changes, filtered=False)
    target_class_instance_id = pre_state.target_object_id
    if target_class_instance_id is None:
        return _ScopedInstanceCallChanges(changes=changes, filtered=False)
    allowed_ids = {
        target_class_instance_id,
        *constructed_class_instance_ids,
        *_descendant_class_instance_ids(
            before_oig=pre_state.before_oig,
            changes=changes,
            target_class_instance_id=target_class_instance_id,
        ),
    }
    if not allowed_ids:
        return _ScopedInstanceCallChanges(changes=changes, filtered=False)

    scoped_changes: list[ObjectInstanceGraphChange] = []
    filtered = False
    for change in changes:
        class_instance_changes = [
            item
            for item in change.class_instance_changes
            if item.class_instance_id in allowed_ids
        ]
        relationship_changes = [
            item
            for item in change.class_instance_relationship_changes
            if item.source_class_instance_id in allowed_ids
            or item.target_class_instance_id in allowed_ids
        ]
        class_instances_filtered = len(class_instance_changes) != len(
            change.class_instance_changes,
        )
        relationships_filtered = len(relationship_changes) != len(
            change.class_instance_relationship_changes,
        )
        if class_instances_filtered or relationships_filtered:
            filtered = True
        if not class_instance_changes and not relationship_changes:
            continue
        if class_instances_filtered or relationships_filtered:
            scoped_changes.append(
                change.model_copy(
                    update={
                        "class_instance_changes": class_instance_changes,
                        "class_instance_relationship_changes": relationship_changes,
                    },
                )
            )
        else:
            scoped_changes.append(change)
    if not filtered:
        return _ScopedInstanceCallChanges(changes=changes, filtered=False)
    return _ScopedInstanceCallChanges(changes=tuple(scoped_changes), filtered=True)


def _can_hash_constructor_post_oig_directly(
    *,
    request: MetaGraphHandlerExecutionRequest,
) -> bool:
    return request.execution_plan.implementation.is_constructor


def _materialization_cache_prime_snapshot(
    *,
    request: MetaGraphHandlerExecutionRequest,
    post_oig: ObjectInstanceGraph,
    graph_hash_post: str,
) -> MetaGraphMaterializationCachePrimeSnapshot:
    return MetaGraphMaterializationCachePrimeSnapshot(
        execution_plan=request.execution_plan,
        post_oig=post_oig,
        graph_hash_post=graph_hash_post,
    )


def _descendant_class_instance_ids(
    *,
    before_oig: ObjectInstanceGraph,
    changes: tuple[ObjectInstanceGraphChange, ...],
    target_class_instance_id: UUID,
) -> set[UUID]:
    relationships_by_source: dict[UUID, list[UUID]] = {}
    for relationship in before_oig.class_instance_relationships:
        relationships_by_source.setdefault(
            relationship.source_class_instance_id,
            [],
        ).append(relationship.target_class_instance_id)
    for root in changes:
        for relationship_change in root.class_instance_relationship_changes:
            if relationship_change.change.type is ChangeType.delete:
                continue
            relationships_by_source.setdefault(
                relationship_change.source_class_instance_id,
                [],
            ).append(relationship_change.target_class_instance_id)

    descendants: set[UUID] = set()
    stack = list(relationships_by_source.get(target_class_instance_id, ()))
    while stack:
        class_instance_id = stack.pop()
        if class_instance_id in descendants:
            continue
        descendants.add(class_instance_id)
        stack.extend(relationships_by_source.get(class_instance_id, ()))
    return descendants


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
    if (
        expected_graph_hash_post is not None
        and graph_hash_post != expected_graph_hash_post
    ):
        raise MetaGraphExecutionSessionDeltaError(
            "Meta execution-session post hash mismatch: "
            f"have={graph_hash_post} expected={expected_graph_hash_post}"
        )
    return graph_hash_post


def _session_delta_trace_metadata(
    request: MetaGraphHandlerExecutionRequest,
) -> dict[str, object]:
    implementation = request.execution_plan.implementation
    return {
        "call_target": request.request.call_target.value,
        "domain_projection_hash": request.request.domain_projection_hash,
        "function_call_id": request.staged_call.function_call.id,
        "function_id": implementation.function_config.id,
        "function_name": implementation.function_config.name,
        "is_constructor": implementation.is_constructor,
        "operation_label": request.staged_call.resolved_target.operation_label,
    }


__all__ = [
    "MetaGraphExecutionSessionDeltaBuilder",
    "MetaGraphExecutionSessionDeltaError",
]
