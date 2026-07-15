from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import cast

from aware_meta.graph.instance.apply import (
    apply_object_instance_graph_body_draft,
    apply_object_instance_graph_changes,
)
from aware_meta.graph.instance.commit.body_codec import (
    oig_body_draft_change_set_sha256,
    oig_change_set_sha256,
)
from aware_meta.graph.instance.commit.perf_trace import commit_perf_span
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.graph.instance.replay import copy_object_instance_graph_for_changes
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphAppendReadyChanges,
    MetaGraphHandlerExecutionRequest,
    MetaGraphMaterializationCachePrimeSnapshot,
    MetaGraphMutationBoundaryStatus,
    MetaGraphMutationBoundaryValidation,
    MetaGraphMutationSet,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)


class MetaGraphAppendReadyAssemblyError(RuntimeError):
    """Raised when append-ready OIG changes cannot be assembled safely."""


@dataclass(frozen=True, slots=True)
class MetaGraphAppendReadyChangeAssemblerPhase:
    """Assemble append-ready OIG changes after boundary validation."""

    async def assemble_append_ready_changes(
        self,
        request: MetaGraphHandlerExecutionRequest,
        mutation_set: MetaGraphMutationSet,
        boundary_validation: MetaGraphMutationBoundaryValidation,
    ) -> MetaGraphAppendReadyChanges:
        return build_meta_graph_append_ready_changes(
            request=request,
            mutation_set=mutation_set,
            boundary_validation=boundary_validation,
        )


def build_meta_graph_append_ready_changes(
    *,
    request: MetaGraphHandlerExecutionRequest,
    mutation_set: MetaGraphMutationSet,
    boundary_validation: MetaGraphMutationBoundaryValidation,
) -> MetaGraphAppendReadyChanges:
    metadata = _append_ready_trace_metadata(
        mutation_set=mutation_set,
    )
    with commit_perf_span(
        phase="handler_execution.append_ready.validate_inputs",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        _validate_append_ready_inputs(
            request=request,
            mutation_set=mutation_set,
            boundary_validation=boundary_validation,
        )
    if boundary_validation.status is not MetaGraphMutationBoundaryStatus.accepted:
        raise MetaGraphAppendReadyAssemblyError(
            "Cannot assemble append-ready changes for rejected mutations. "
            f"violation_message={boundary_validation.violation_message}"
        )
    if not mutation_set.graph_hash_pre:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready changes require graph_hash_pre from mutation set."
        )
    if not mutation_set.graph_hash_post:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready changes require graph_hash_post from mutation set."
        )
    with commit_perf_span(
        phase="handler_execution.append_ready.validate_cache_prime_snapshot",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        _validate_materialization_cache_prime_snapshot(mutation_set=mutation_set)
    with commit_perf_span(
        phase="handler_execution.append_ready.validate_replay",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        cache_prime_snapshot = _validate_append_ready_replay(
            mutation_set=mutation_set,
            metadata=metadata,
        )
    with commit_perf_span(
        phase="handler_execution.append_ready.assemble_result",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        return MetaGraphAppendReadyChanges(
            execution_plan=request.execution_plan,
            before_oig=mutation_set.before_oig,
            changes=mutation_set.changes,
            body_draft=mutation_set.body_draft,
            graph_hash_pre=mutation_set.graph_hash_pre,
            graph_hash_post=mutation_set.graph_hash_post,
            root_object_id=mutation_set.root_object_id,
            root_class_instance_identity_id=(
                mutation_set.root_class_instance_identity_id
            ),
            materialization_cache_prime_snapshot=cache_prime_snapshot,
        )


def _validate_append_ready_inputs(
    *,
    request: MetaGraphHandlerExecutionRequest,
    mutation_set: MetaGraphMutationSet,
    boundary_validation: MetaGraphMutationBoundaryValidation,
) -> None:
    execution_plan = request.execution_plan
    if mutation_set.execution_plan is not execution_plan:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready assembly requires mutations from the same execution plan."
        )
    if boundary_validation.execution_plan is not execution_plan:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready assembly requires boundary validation from the same "
            "execution plan."
        )
    if boundary_validation.mutation_set is not mutation_set:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready assembly requires boundary validation for the same "
            "mutation set."
        )
    if mutation_set.changes and mutation_set.body_draft is not None:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready assembly cannot mix changes and body-draft evidence."
        )


def _validate_append_ready_replay(
    *,
    mutation_set: MetaGraphMutationSet,
    metadata: dict[str, object],
) -> MetaGraphMaterializationCachePrimeSnapshot:
    artifact_fallback_reason = _validated_replay_artifact_fallback_reason(
        mutation_set=mutation_set,
        metadata=metadata,
    )
    if artifact_fallback_reason is None:
        artifact = mutation_set.validated_replay_artifact
        if artifact is None:
            raise AssertionError("validated replay artifact unexpectedly absent")
        with commit_perf_span(
            phase="handler_execution.append_ready.replay_artifact.reuse",
            category="meta.runtime.handler_execution",
            metadata=metadata,
        ):
            return MetaGraphMaterializationCachePrimeSnapshot(
                execution_plan=mutation_set.execution_plan,
                post_oig=artifact.post_oig,
                graph_hash_post=artifact.graph_hash_post,
            )

    fallback_metadata = {
        **metadata,
        "artifact_fallback_reason": artifact_fallback_reason,
    }
    with commit_perf_span(
        phase="handler_execution.append_ready.replay_artifact.fallback",
        category="meta.runtime.handler_execution",
        metadata=fallback_metadata,
    ):
        pass
    try:
        copy_metadata = dict(metadata)
        with commit_perf_span(
            phase="handler_execution.append_ready.replay.copy_graph",
            category="meta.runtime.handler_execution",
            metadata=copy_metadata,
        ):
            replay_copy = copy_object_instance_graph_for_changes(
                before_oig=mutation_set.before_oig,
                changes=cast(
                    Iterable[ObjectInstanceGraphChange],
                    (
                        mutation_set.body_draft.roots
                        if mutation_set.body_draft is not None
                        else mutation_set.changes
                    ),
                ),
            )
            copy_metadata.update(
                {
                    "class_instance_copy_count": (
                        replay_copy.class_instance_copy_count
                    ),
                    "attribute_copy_count": replay_copy.attribute_copy_count,
                    "value_node_copy_count": replay_copy.value_node_copy_count,
                }
            )
        replay_graph = replay_copy.graph
        with commit_perf_span(
            phase="handler_execution.append_ready.replay.apply_changes",
            category="meta.runtime.handler_execution",
            metadata=metadata,
        ):
            attribute_configs_by_id = (
                mutation_set.execution_plan.index.attribute_configs_by_id
            )
            class_configs_by_id = mutation_set.execution_plan.index.class_configs_by_id
            if mutation_set.body_draft is not None:
                apply_object_instance_graph_body_draft(
                    graph=replay_graph,
                    body_draft=mutation_set.body_draft,
                    attribute_configs_by_id=attribute_configs_by_id,
                    class_configs_by_id=class_configs_by_id,
                )
            else:
                apply_object_instance_graph_changes(
                    graph=replay_graph,
                    changes=mutation_set.changes,
                    attribute_configs_by_id=attribute_configs_by_id,
                    class_configs_by_id=class_configs_by_id,
                )
        with commit_perf_span(
            phase="handler_execution.append_ready.replay.build_index",
            category="meta.runtime.handler_execution",
            metadata=metadata,
        ):
            replay_index = build_index(replay_graph)
        with commit_perf_span(
            phase="handler_execution.append_ready.replay.compute_hash",
            category="meta.runtime.handler_execution",
            metadata=metadata,
        ):
            replay_hash_post = compute_hash(replay_graph, replay_index)
    except Exception as exc:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready changes are not replayable from graph_hash_pre. "
            f"error={type(exc).__name__}: {exc}"
        ) from exc

    if replay_hash_post != mutation_set.graph_hash_post:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready changes are not replayable from graph_hash_pre. "
            f"have={replay_hash_post} expected={mutation_set.graph_hash_post} "
            f"change_count={len(mutation_set.changes)}"
        )
    existing_snapshot = mutation_set.materialization_cache_prime_snapshot
    if existing_snapshot is not None:
        try:
            existing_snapshot_hash = compute_hash(
                existing_snapshot.post_oig,
                build_index(existing_snapshot.post_oig),
            )
        except Exception:
            existing_snapshot_hash = None
        if existing_snapshot_hash == replay_hash_post:
            return existing_snapshot
    return MetaGraphMaterializationCachePrimeSnapshot(
        execution_plan=mutation_set.execution_plan,
        post_oig=replay_graph,
        graph_hash_post=replay_hash_post,
    )


def _validated_replay_artifact_fallback_reason(
    *,
    mutation_set: MetaGraphMutationSet,
    metadata: dict[str, object],
) -> str | None:
    artifact = mutation_set.validated_replay_artifact
    if artifact is None:
        return "missing"
    if artifact.execution_plan is not mutation_set.execution_plan:
        return "execution_plan_identity_mismatch"
    if artifact.before_oig is not mutation_set.before_oig:
        return "before_oig_identity_mismatch"
    if mutation_set.body_draft is not None:
        if artifact.body_draft is not mutation_set.body_draft:
            return "body_draft_identity_mismatch"
        if artifact.changes:
            return "artifact_mixed_evidence"
    elif artifact.changes is not mutation_set.changes:
        return "changes_identity_mismatch"
    if artifact.graph_hash_pre != mutation_set.graph_hash_pre:
        return "graph_hash_pre_mismatch"
    if artifact.graph_hash_post != mutation_set.graph_hash_post:
        return "graph_hash_post_mismatch"
    if artifact.post_oig.id != mutation_set.before_oig.id:
        return "post_oig_id_mismatch"

    try:
        with commit_perf_span(
            phase=(
                "handler_execution.append_ready." "replay_artifact.fingerprint_changes"
            ),
            category="meta.runtime.handler_execution",
            metadata=metadata,
        ):
            change_set_sha256 = (
                oig_body_draft_change_set_sha256(mutation_set.body_draft)
                if mutation_set.body_draft is not None
                else oig_change_set_sha256(mutation_set.changes)
            )
    except Exception as exc:
        return f"change_set_fingerprint_error:{type(exc).__name__}"
    if change_set_sha256 != artifact.change_set_sha256:
        return "change_set_sha256_mismatch"

    try:
        with commit_perf_span(
            phase="handler_execution.append_ready.replay_artifact.hash_pre_state",
            category="meta.runtime.handler_execution",
            metadata=metadata,
        ):
            graph_hash_pre = compute_hash(
                mutation_set.before_oig,
                build_index(mutation_set.before_oig),
            )
    except Exception as exc:
        return f"pre_state_hash_error:{type(exc).__name__}"
    if graph_hash_pre != artifact.graph_hash_pre:
        return "pre_state_hash_mismatch"

    try:
        with commit_perf_span(
            phase="handler_execution.append_ready.replay_artifact.hash_post_state",
            category="meta.runtime.handler_execution",
            metadata=metadata,
        ):
            graph_hash_post = compute_hash(
                artifact.post_oig,
                build_index(artifact.post_oig),
            )
    except Exception as exc:
        return f"post_state_hash_error:{type(exc).__name__}"
    if graph_hash_post != artifact.graph_hash_post:
        return "post_state_hash_mismatch"
    return None


def _append_ready_trace_metadata(
    *,
    mutation_set: MetaGraphMutationSet,
) -> dict[str, object]:
    return {
        "change_count": len(mutation_set.changes),
        "body_draft_root_count": (
            len(mutation_set.body_draft.roots)
            if mutation_set.body_draft is not None
            else 0
        ),
        "class_instance_count": len(mutation_set.before_oig.class_instances),
    }


def _validate_materialization_cache_prime_snapshot(
    *,
    mutation_set: MetaGraphMutationSet,
) -> None:
    snapshot = mutation_set.materialization_cache_prime_snapshot
    if snapshot is None:
        return
    if snapshot.execution_plan is not mutation_set.execution_plan:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready materialization cache snapshot belongs to a different "
            "execution plan."
        )
    if snapshot.post_oig.id != mutation_set.before_oig.id:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready materialization cache snapshot targets a different "
            "ObjectInstanceGraph."
        )
    if snapshot.graph_hash_post != mutation_set.graph_hash_post:
        raise MetaGraphAppendReadyAssemblyError(
            "Append-ready materialization cache snapshot graph_hash_post mismatch."
        )


__all__ = [
    "build_meta_graph_append_ready_changes",
    "MetaGraphAppendReadyAssemblyError",
    "MetaGraphAppendReadyChangeAssemblerPhase",
]
