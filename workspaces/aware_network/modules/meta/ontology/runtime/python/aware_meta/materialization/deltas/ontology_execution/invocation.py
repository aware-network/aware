from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from time import perf_counter
from typing import cast
from uuid import UUID

from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_meta.graph.instance.commit.perf_trace import (
    current_commit_perf_trace,
    commit_perf_span,
    summarize_commit_perf_events,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphInvokeFunctionInput,
)


ONTOLOGY_INVOCATION_EXECUTION_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-ontology-invocation-execution.v1"
)
ONTOLOGY_INVOCATION_COST_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-ontology-invocation-cost.v1"
)
ONTOLOGY_INVOCATION_AGGREGATE_RECEIPT_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-ontology-invocation-aggregate-receipt.v1"
)
ONTOLOGY_INVOCATION_AGGREGATE_COMMIT_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-ontology-invocation-aggregate-commit.v1"
)

_CORE_TRACE_PHASES = (
    "runtime.invoke_function.stage_function_call",
    "runtime.invoke_function.execute_staged_function_call",
    "runtime.invoke_function.handler_execute_function",
    "runtime.invoke_function.append_domain_commit",
    "runtime.invoke_function.append_invocation_domain_commit",
    "runtime.invoke_function.required_commit_reactions",
    "runtime.invoke_function.required_commit_reactions_batch",
    "runtime.invoke_function.required_commit_reactions.oigi_history.upsert_history",
    "runtime.invoke_function.required_commit_reactions.oigi_history.build_direct_projection_context",
    "runtime.invoke_function.required_commit_reactions.oigi_history.reuse_direct_projection_context",
    "runtime.invoke_function.required_commit_reactions.oigi_history.build_direct_pre_state_row_maps",
    "runtime.invoke_function.required_commit_reactions.oigi_history.reuse_direct_pre_state_row_maps",
    "runtime.invoke_function.required_commit_reactions.oigi_history.build_direct_source_state_rows",
    "runtime.invoke_function.build_commit_receipt",
)

_DURABLE_HEAD_WRITE_PHASES = (
    "oig_commit_store.append_record.durable_head_written",
    "oig_commit_store.append_records.durable_head_written",
)
_APPEND_GROUPED_DURABLE_WRITE_PHASES = (
    "oig_commit_store.append_record.grouped_durable_transaction_write",
    "oig_commit_store.append_records.grouped_durable_transaction_write",
)
_GROUPED_DURABLE_TRANSACTION_COMMIT_PHASES = (
    "oig_commit_store.append_record.grouped_durable_transaction_committed",
    "oig_commit_store.append_records.grouped_durable_transaction_committed",
    "runtime.invoke_function.aggregate.grouped_durable_transaction_committed",
)
_AGGREGATE_GROUPED_DURABLE_WRITE_PHASES = (
    "runtime.invoke_function.aggregate.grouped_durable_transaction_write",
)
_GROUPED_DURABLE_SYNCFS_PHASES = (
    "oig_commit_store.append_record.grouped_durable_transaction_syncfs",
    "oig_commit_store.append_records.grouped_durable_transaction_syncfs",
    "runtime.invoke_function.aggregate.grouped_durable_transaction_syncfs",
)
_GROUPED_DURABLE_FILE_FSYNC_PHASES = (
    "oig_commit_store.append_record.grouped_durable_transaction_file_fsync",
    "oig_commit_store.append_records.grouped_durable_transaction_file_fsync",
    "runtime.invoke_function.aggregate.grouped_durable_transaction_file_fsync",
)
_IMPL_DELEGATION_DIRECT_CHANGE_PHASE = (
    "handler_execution.impl_delegation.build_direct_change_evidence"
)
_IMPL_DELEGATION_DIRECT_CHANGE_FALLBACK_PHASE = (
    "handler_execution.impl_delegation.direct_change_evidence_fallback"
)
_IMPL_DELEGATION_SIMPLE_SCALAR_DIRECT_CHANGE_PHASE = (
    "handler_execution.impl_delegation.build_simple_scalar_direct_evidence"
)
_IMPL_DELEGATION_SIMPLE_SCALAR_DIRECT_CHANGE_SUCCESS_PHASE = (
    "handler_execution.impl_delegation.simple_scalar_direct_evidence_success"
)
_IMPL_DELEGATION_SIMPLE_SCALAR_DIRECT_CHANGE_FALLBACK_PHASE = (
    "handler_execution.impl_delegation.simple_scalar_direct_evidence_fallback"
)
_IMPL_DELEGATION_POST_OIG_FALLBACK_PHASE = (
    "handler_execution.impl_delegation.build_post_oig_fallback"
)
_SESSION_DELTA_DIRECT_CHANGE_APPLY_PHASE = (
    "handler_execution.session_delta.apply_direct_changes_for_hash"
)
_SESSION_DELTA_DIRECT_CHANGE_COPY_PHASE = (
    "handler_execution.session_delta.copy_direct_change_graph"
)
_SESSION_DELTA_DIRECT_CHANGE_HASH_PHASE = (
    "handler_execution.session_delta.hash_direct_changes"
)
_SESSION_DELTA_DIRECT_CHANGE_FINGERPRINT_PHASE = (
    "handler_execution.session_delta.fingerprint_direct_changes"
)
_SESSION_CANONICAL_APPLY_PREFIX = "handler_execution.session_delta.canonical_apply"
_SESSION_CANONICAL_APPLY_PHASES = {
    "build_class_instance_index": (
        f"{_SESSION_CANONICAL_APPLY_PREFIX}.build_class_instance_index"
    ),
    "class_instance_membership": (
        f"{_SESSION_CANONICAL_APPLY_PREFIX}.class_instance.membership"
    ),
    "class_instance_attributes": (
        f"{_SESSION_CANONICAL_APPLY_PREFIX}.class_instance.attributes"
    ),
    "class_instance_sort_attributes": (
        f"{_SESSION_CANONICAL_APPLY_PREFIX}.class_instance.sort_attributes"
    ),
    "attribute_apply": f"{_SESSION_CANONICAL_APPLY_PREFIX}.attribute.apply",
    "attribute_value_construct": (
        f"{_SESSION_CANONICAL_APPLY_PREFIX}.attribute_value.construct"
    ),
    "attribute_value_apply_scalar_changes": (
        f"{_SESSION_CANONICAL_APPLY_PREFIX}.attribute_value.apply_scalar_changes"
    ),
    "attribute_value_apply_child_changes": (
        f"{_SESSION_CANONICAL_APPLY_PREFIX}.attribute_value.apply_child_changes"
    ),
    "attribute_value_canonicalize": (
        f"{_SESSION_CANONICAL_APPLY_PREFIX}.attribute_value.canonicalize"
    ),
    "attribute_value_validate": (
        f"{_SESSION_CANONICAL_APPLY_PREFIX}.attribute_value.validate"
    ),
    "attribute_link": f"{_SESSION_CANONICAL_APPLY_PREFIX}.attribute.link",
    "relationship_apply": f"{_SESSION_CANONICAL_APPLY_PREFIX}.relationship.apply",
    "sort_graph_members": f"{_SESSION_CANONICAL_APPLY_PREFIX}.sort_graph_members",
}
_ORM_CHANGE_TRANSLATION_BUILD_OCG_INDEX_PHASE = (
    "handler_execution.orm_change_translation.build_ocg_index"
)
_ORM_CHANGE_TRANSLATION_OCG_INDEX_CACHE_BUILD_PHASE = (
    "handler_execution.orm_change_translation.build_ocg_index.cache_build"
)
_ORM_CHANGE_TRANSLATION_OCG_INDEX_CACHE_REUSE_PHASE = (
    "handler_execution.orm_change_translation.build_ocg_index.cache_reuse"
)
_ORM_CHANGE_TRANSLATION_BUILD_CLASS_INSTANCE_CHANGES_PHASE = (
    "handler_execution.orm_change_translation.build_class_instance_changes"
)
_ORM_CHANGE_TRANSLATION_BUILD_RELATIONSHIP_CHANGES_PHASE = (
    "handler_execution.orm_change_translation.build_relationship_changes"
)
_ORM_CHANGE_TRANSLATION_BUILD_DETACHED_CLASS_INSTANCE_CHANGES_PHASE = (
    "handler_execution.orm_change_translation." "build_detached_class_instance_changes"
)
_ORM_CHANGE_TRANSLATION_DETACHED_CLASS_INSTANCE_DELETE_PHASE = (
    "handler_execution.orm_change_translation.detached_class_instance_delete"
)
_ORM_CHANGE_TRANSLATION_DETACHED_RELATIONSHIP_DELETE_PHASE = (
    "handler_execution.orm_change_translation.detached_relationship_delete"
)
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_CLASSIFY_PHASE = (
    "handler_execution.orm_change_translation."
    "class_instance_changes.classify_candidates"
)
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_CONTEXT_PHASE = (
    "handler_execution.orm_change_translation."
    "class_instance_changes.build_relationship_context"
)
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_BUILD_PHASE = (
    "handler_execution.orm_change_translation."
    "class_instance_changes.build_class_instances"
)
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_EMIT_PHASE = (
    "handler_execution.orm_change_translation.class_instance_changes.emit_changes"
)
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_CANDIDATE_INPUT_PHASE = (
    "handler_execution.orm_change_translation.class_instance_changes.candidate_input"
)
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_CANDIDATE_SELECTED_PHASE = (
    "handler_execution.orm_change_translation."
    "class_instance_changes.candidate_selected"
)
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_CANDIDATE_PRUNED_PHASE = (
    "handler_execution.orm_change_translation."
    "class_instance_changes.candidate_pruned_relationship_only"
)
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_CANDIDATE_IGNORED_PHASE = (
    "handler_execution.orm_change_translation."
    "class_instance_changes.candidate_ignored_out_of_projection"
)
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_BUILD_PROFILE_PREFIX = (
    "handler_execution.orm_change_translation." "class_instance_changes.build_profile"
)
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_BUILD_PROFILE_PHASES = {
    name: f"{_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_BUILD_PROFILE_PREFIX}.{name}"
    for name in (
        "construct_shell",
        "plan_attributes",
        "materialize_attributes",
        "source_attribute_values",
        "build_attributes",
        "link_attributes",
    )
}
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_BUILD_PROFILE_COUNTS = {
    name: f"{_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_BUILD_PROFILE_PREFIX}.{name}"
    for name in (
        "attribute_link_input",
        "source_attribute_lookup",
        "attribute_built",
    )
}
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_EMISSION_PROFILE_PREFIX = (
    "handler_execution.orm_change_translation."
    "class_instance_changes.emission_profile"
)
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_EMISSION_PROFILE_PHASES = {
    name: f"{_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_EMISSION_PROFILE_PREFIX}.{name}"
    for name in (
        "index_inputs",
        "classify_candidates",
        "create_changes",
        "update_attribute_membership",
        "update_graph_diff",
        "delete_changes",
        "create_field_plan",
        "create_change_shell",
        "create_change_deltas",
        "create_change_delta_payload_value",
        "create_change_delta_json_wrapper",
        "create_change_delta_model",
        "orm_change_model_validation",
        "orm_change_model_validation_residual",
        "orm_change_relationship_pre_validator",
        "orm_change_relationship_pre_validator_residual",
        "orm_change_relationship_hook_guard",
        "orm_change_relationship_hook_guard_residual",
        "orm_change_uuid_default",
        "orm_change_relationship_processing",
        "orm_change_post_init_hook_guard",
        "orm_change_delta_model_validation",
        "orm_change_delta_model_validation_residual",
        "orm_change_delta_relationship_pre_validator",
        "orm_change_delta_relationship_pre_validator_residual",
        "orm_change_delta_relationship_hook_guard",
        "orm_change_delta_relationship_hook_guard_residual",
        "orm_change_delta_uuid_default",
        "orm_change_delta_relationship_processing",
        "orm_change_delta_post_init_hook_guard",
        "create_class_instance_wrapper",
        "create_attribute_index",
        "create_attribute_sort",
        "create_attribute_wrapper",
        "create_attribute_value_wrapper",
        "create_attribute_value_link_sort",
        "create_attribute_value_link_wrapper",
    )
}
_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_EMISSION_PROFILE_COUNTS = {
    name: f"{_ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_EMISSION_PROFILE_PREFIX}.{name}"
    for name in (
        "candidate_input",
        "create_candidate",
        "update_candidate",
        "delete_candidate",
        "update_attribute_membership_path",
        "update_graph_diff_path",
        "change_emitted",
        "create_change_object",
        "create_change_delta",
        "create_change_delta_payload_value",
        "create_change_delta_json_wrapper",
        "create_change_delta_model",
        "orm_change_model_validation_attempt",
        "orm_change_relationship_pre_validator_call",
        "orm_change_relationship_hook_guard_call",
        "orm_change_uuid_default_generated",
        "orm_change_relationship_processing_call",
        "orm_change_post_init_hook_guard_call",
        "orm_change_delta_model_validation_attempt",
        "orm_change_delta_relationship_pre_validator_call",
        "orm_change_delta_relationship_hook_guard_call",
        "orm_change_delta_uuid_default_generated",
        "orm_change_delta_relationship_processing_call",
        "orm_change_delta_post_init_hook_guard_call",
        "create_class_instance_wrapper_object",
        "create_attribute_input",
        "create_attribute_unique",
        "create_attribute_wrapper_object",
        "create_attribute_value_wrapper_object",
        "create_attribute_value_link_wrapper_object",
    )
}
_OIG_BUILDER_BUILD_INDEXES_PHASE = "handler_execution.oig_builder.build_indexes"
_OIG_BUILDER_STATIC_INDEX_CACHE_HIT_PHASE = (
    "handler_execution.oig_builder.static_index_cache_hit"
)
_OIG_BUILDER_STATIC_INDEX_CACHE_MISS_PHASE = (
    "handler_execution.oig_builder.static_index_cache_miss"
)
_OIG_BUILDER_BUILD_GRAPH_INDEX_PHASE = "handler_execution.oig_builder.build_graph_index"
_OIG_BUILDER_COMPUTE_GRAPH_HASH_PHASE = (
    "handler_execution.oig_builder.compute_graph_hash"
)
_SESSION_DELTA_DIFF_POST_OIG_PHASE = "handler_execution.session_delta.diff_post_oig"
_SESSION_DELTA_DIFF_POST_OIG_DIRTY_CLASS_INSTANCE_SET_PHASE = (
    "handler_execution.session_delta.diff_post_oig_dirty_class_instance_set"
)
_SESSION_DELTA_DIFF_POST_OIG_SPARSE_IDENTITY_SNAPSHOT_PHASE = (
    "handler_execution.session_delta.diff_post_oig_sparse_identity_snapshot"
)
_SESSION_DELTA_DIFF_POST_OIG_FULL_FALLBACK_PHASE = (
    "handler_execution.session_delta.diff_post_oig_full_fallback"
)


def ontology_invocation_runtime_preflight(
    *,
    request: object,
) -> dict[str, object]:
    runtime = _request_value(request=request, key="runtime")
    graph_runtime_context = _request_value(
        request=request,
        key="aware_meta.graph_runtime_context",
    )
    return {
        "preflight_kind": "meta_ocg_provider_delta_ontology_invocation_runtime_preflight",
        "contract_version": (
            "aware.meta.ocg.provider-delta-ontology-invocation-runtime-preflight.v1"
        ),
        "runtime_available": runtime is not None,
        "runtime_backend": type(runtime).__name__ if runtime is not None else None,
        "runtime_invoke_function_available": callable(
            getattr(runtime, "invoke_function", None)
        ),
        "runtime_invoke_instance_available": callable(
            getattr(runtime, "invoke_instance", None)
        ),
        "graph_runtime_context_available": graph_runtime_context is not None,
        "graph_runtime_context_backend": (
            type(graph_runtime_context).__name__
            if graph_runtime_context is not None
            else None
        ),
    }


async def execute_ontology_invocation_intents(
    *,
    runtime: object,
    graph_runtime_context: object,
    actor_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    domain_object_instance_graph_id: UUID | None = None,
    domain_object_instance_graph_identity_id: UUID | None = None,
    invocation_intents: Sequence[Mapping[str, object]],
    initial_expected_head_commit_id: UUID | None = None,
) -> dict[str, object]:
    invoke_function = _invoke_function_callable(runtime=runtime)
    index = getattr(graph_runtime_context, "index", None)
    with commit_perf_span(
        phase="ontology_invocation.sort_intents",
        category="meta.provider_delta",
        metadata={"invocation_intent_count": len(invocation_intents)},
    ):
        sorted_intents = _sorted_invocation_intents(invocation_intents)
    blockers = []
    if invoke_function is None:
        blockers.append("runtime_invoke_function_unavailable")
    if index is None:
        blockers.append("graph_runtime_context_index_unavailable")
    if not sorted_intents:
        blockers.append("ontology_invocation_intents_empty")
    if blockers:
        return _execution_payload(
            status="ontology_function_call_execution_blocked",
            reason="meta_ocg_ontology_function_call_execution_blocked",
            runtime=runtime,
            graph_runtime_context=graph_runtime_context,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            blockers=tuple(blockers),
            invocation_intents=tuple(sorted_intents),
        )
    assert invoke_function is not None
    assert index is not None

    aggregate_execution = await _try_execute_aggregate_invocation(
        runtime=runtime,
        graph_runtime_context=graph_runtime_context,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        domain_object_instance_graph_id=domain_object_instance_graph_id,
        domain_object_instance_graph_identity_id=(
            domain_object_instance_graph_identity_id
        ),
        invocation_intents=tuple(sorted_intents),
        initial_expected_head_commit_id=initial_expected_head_commit_id,
    )
    if aggregate_execution is not None:
        return aggregate_execution

    receipts: list[dict[str, object]] = []
    expected_head_commit_ids_by_projection_hash: dict[str, UUID | None] = {
        projection_hash: initial_expected_head_commit_id,
    }
    expected_graph_hash_pre_by_projection_hash: dict[str, str | None] = {}
    projection_hash_by_object_id: dict[UUID, str] = {}
    for invocation_index, intent in enumerate(sorted_intents):
        trace_metadata = _trace_metadata_for_intent(
            intent=intent,
            invocation_index=invocation_index,
        )
        with commit_perf_span(
            phase="ontology_invocation.input_for_intent",
            category="meta.provider_delta",
            metadata=trace_metadata,
        ):
            input_or_blocked = _invoke_function_input_for_intent(
                index=cast(MetaGraphRuntimeIndex, index),
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                domain_object_instance_graph_id=domain_object_instance_graph_id,
                domain_object_instance_graph_identity_id=(
                    domain_object_instance_graph_identity_id
                ),
                intent=intent,
                expected_head_commit_ids_by_projection_hash=(
                    expected_head_commit_ids_by_projection_hash
                ),
                expected_graph_hash_pre_by_projection_hash=(
                    expected_graph_hash_pre_by_projection_hash
                ),
                projection_hash_by_object_id=projection_hash_by_object_id,
            )
        input_blockers = _tuple_text(input_or_blocked.get("blockers"))
        if input_blockers:
            return _execution_payload(
                status="ontology_function_call_execution_blocked",
                reason="meta_ocg_ontology_function_call_input_blocked",
                runtime=runtime,
                graph_runtime_context=graph_runtime_context,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                blockers=input_blockers,
                invocation_intents=tuple(sorted_intents),
                invocation_receipts=tuple(receipts),
            )
        invoke_input = cast(
            MetaGraphInvokeFunctionInput,
            input_or_blocked.get("input"),
        )
        try:
            trace_event_offset = _active_trace_event_count()
            invoke_started_at = perf_counter()
            with commit_perf_span(
                phase="ontology_invocation.invoke_function",
                category="meta.provider_delta",
                metadata=trace_metadata,
            ):
                commit_receipt = await invoke_function(invoke_input)
            invoke_duration_ms = _elapsed_ms(invoke_started_at)
            invoke_trace_summary = _active_trace_summary_since(trace_event_offset)
        except Exception as exc:
            return _execution_payload(
                status="ontology_function_call_execution_failed",
                reason="meta_ocg_ontology_function_call_invoke_failed",
                runtime=runtime,
                graph_runtime_context=graph_runtime_context,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                blockers=(),
                invocation_intents=tuple(sorted_intents),
                invocation_receipts=tuple(receipts),
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
        with commit_perf_span(
            phase="ontology_invocation.receipt_payload",
            category="meta.provider_delta",
            metadata=trace_metadata,
        ):
            receipt_payload = _commit_receipt_payload(
                intent=intent,
                commit_receipt=commit_receipt,
            )
            receipt_payload.update(
                _invoke_function_cost_payload(
                    invoke_input=invoke_input,
                    duration_ms=invoke_duration_ms,
                    trace_summary=invoke_trace_summary,
                )
            )
        receipts.append(receipt_payload)
        if _optional_text(receipt_payload.get("status")) != "succeeded":
            return _execution_payload(
                status="ontology_function_call_execution_failed",
                reason="meta_ocg_ontology_function_call_commit_failed",
                runtime=runtime,
                graph_runtime_context=graph_runtime_context,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                blockers=(),
                invocation_intents=tuple(sorted_intents),
                invocation_receipts=tuple(receipts),
                error_message=_optional_text(receipt_payload.get("error")),
            )
        if _commit_required_missing(receipt_payload=receipt_payload):
            return _execution_payload(
                status="ontology_function_call_execution_failed",
                reason="meta_ocg_ontology_function_call_required_commit_missing",
                runtime=runtime,
                graph_runtime_context=graph_runtime_context,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                blockers=(),
                invocation_intents=tuple(sorted_intents),
                invocation_receipts=tuple(receipts),
                error_message=(
                    "Ontology FunctionCall succeeded without a commit for a "
                    "commit-required intent."
                ),
            )
        with commit_perf_span(
            phase="ontology_invocation.head_tracking",
            category="meta.provider_delta",
            metadata=trace_metadata,
        ):
            receipt_projection_hash = _optional_text(
                receipt_payload.get("projection_hash")
            )
            if receipt_projection_hash is not None:
                expected_head_commit_ids_by_projection_hash[receipt_projection_hash] = (
                    _uuid_value(receipt_payload.get("commit_id"))
                )
                expected_graph_hash_pre_by_projection_hash[receipt_projection_hash] = (
                    _optional_text(receipt_payload.get("graph_hash_post"))
                )
                for object_id in _receipt_object_ids_for_projection_binding(
                    intent=intent,
                    receipt_payload=receipt_payload,
                ):
                    projection_hash_by_object_id[object_id] = receipt_projection_hash

    return _execution_payload(
        status="ontology_function_call_execution_applied",
        reason="meta_ocg_ontology_function_call_execution_applied",
        runtime=runtime,
        graph_runtime_context=graph_runtime_context,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        blockers=(),
        invocation_intents=tuple(sorted_intents),
        invocation_receipts=tuple(receipts),
    )


async def _try_execute_aggregate_invocation(
    *,
    runtime: object,
    graph_runtime_context: object,
    actor_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    domain_object_instance_graph_id: UUID | None,
    domain_object_instance_graph_identity_id: UUID | None,
    invocation_intents: tuple[Mapping[str, object], ...],
    initial_expected_head_commit_id: UUID | None,
) -> dict[str, object] | None:
    aggregate_executor = _invoke_function_aggregate_callable(runtime=runtime)
    if aggregate_executor is None or len(invocation_intents) < 2:
        return None
    index = getattr(graph_runtime_context, "index", None)
    if index is None:
        return None

    input_payload = _aggregate_invocation_inputs_for_intents(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        domain_object_instance_graph_id=domain_object_instance_graph_id,
        domain_object_instance_graph_identity_id=(
            domain_object_instance_graph_identity_id
        ),
        invocation_intents=invocation_intents,
        initial_expected_head_commit_id=initial_expected_head_commit_id,
    )
    input_blockers = _tuple_text(input_payload.get("blockers"))
    if input_blockers:
        return None
    invoke_inputs = cast(
        tuple[MetaGraphInvokeFunctionInput, ...],
        input_payload.get("inputs") or (),
    )
    if len(invoke_inputs) != len(invocation_intents):
        return None

    trace_event_offset = _active_trace_event_count()
    aggregate_started_at = perf_counter()
    try:
        with commit_perf_span(
            phase="ontology_invocation.invoke_function.aggregate",
            category="meta.provider_delta",
            metadata={
                "invocation_intent_count": len(invocation_intents),
                "executor": "invoke_function_aggregate",
            },
        ):
            aggregate_result = await aggregate_executor(invoke_inputs)
    except Exception as exc:
        return _execution_payload(
            status="ontology_function_call_execution_failed",
            reason="meta_ocg_ontology_function_call_aggregate_invoke_failed",
            runtime=runtime,
            graph_runtime_context=graph_runtime_context,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            blockers=(),
            invocation_intents=invocation_intents,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    aggregate_duration_ms = _elapsed_ms(aggregate_started_at)
    aggregate_trace_summary = _active_trace_summary_since(trace_event_offset)
    commit_receipts = _aggregate_commit_receipts_from_result(aggregate_result)
    if len(commit_receipts) != len(invocation_intents):
        return _execution_payload(
            status="ontology_function_call_execution_failed",
            reason="meta_ocg_ontology_function_call_aggregate_receipt_count_mismatch",
            runtime=runtime,
            graph_runtime_context=graph_runtime_context,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            blockers=(),
            invocation_intents=invocation_intents,
            error_message=(
                "Aggregate FunctionCall executor returned "
                f"{len(commit_receipts)} receipts for {len(invocation_intents)} intents."
            ),
        )

    receipts: list[dict[str, object]] = []
    for index_position, (intent, invoke_input, commit_receipt) in enumerate(
        zip(invocation_intents, invoke_inputs, commit_receipts, strict=True)
    ):
        receipt_payload = _commit_receipt_payload(
            intent=intent,
            commit_receipt=commit_receipt,
        )
        receipt_payload.update(
            _invoke_function_cost_payload(
                invoke_input=invoke_input,
                duration_ms=aggregate_duration_ms if index_position == 0 else 0.0,
                trace_summary=aggregate_trace_summary if index_position == 0 else {},
            )
        )
        receipt_payload["aggregate_commit_execution_index"] = index_position
        receipts.append(receipt_payload)
        if _optional_text(receipt_payload.get("status")) != "succeeded":
            return _execution_payload(
                status="ontology_function_call_execution_failed",
                reason="meta_ocg_ontology_function_call_aggregate_commit_failed",
                runtime=runtime,
                graph_runtime_context=graph_runtime_context,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                blockers=(),
                invocation_intents=invocation_intents,
                invocation_receipts=tuple(receipts),
                error_message=_optional_text(receipt_payload.get("error")),
            )
        if _commit_required_missing(receipt_payload=receipt_payload):
            return _execution_payload(
                status="ontology_function_call_execution_failed",
                reason=(
                    "meta_ocg_ontology_function_call_aggregate_required_commit_missing"
                ),
                runtime=runtime,
                graph_runtime_context=graph_runtime_context,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                blockers=(),
                invocation_intents=invocation_intents,
                invocation_receipts=tuple(receipts),
                error_message=(
                    "Aggregate FunctionCall executor returned a succeeded "
                    "commit-required receipt without a commit."
                ),
            )

    aggregate_commit_execution = _aggregate_commit_execution_payload_from_result(
        result=aggregate_result,
        duration_ms=aggregate_duration_ms,
        receipt_count=len(receipts),
    )
    return _execution_payload(
        status="ontology_function_call_execution_applied",
        reason="meta_ocg_ontology_function_call_aggregate_execution_applied",
        runtime=runtime,
        graph_runtime_context=graph_runtime_context,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        blockers=(),
        invocation_intents=invocation_intents,
        invocation_receipts=tuple(receipts),
        aggregate_commit_execution=aggregate_commit_execution,
    )


def _aggregate_invocation_inputs_for_intents(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    domain_object_instance_graph_id: UUID | None,
    domain_object_instance_graph_identity_id: UUID | None,
    invocation_intents: tuple[Mapping[str, object], ...],
    initial_expected_head_commit_id: UUID | None,
) -> dict[str, object]:
    expected_head_commit_ids_by_projection_hash: dict[str, UUID | None] = {
        projection_hash: initial_expected_head_commit_id,
    }
    expected_graph_hash_pre_by_projection_hash: dict[str, str | None] = {}
    projection_hash_by_object_id: dict[UUID, str] = {}
    invoke_inputs: list[MetaGraphInvokeFunctionInput] = []
    blockers: list[str] = []
    for intent in invocation_intents:
        input_or_blocked = _invoke_function_input_for_intent(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            domain_object_instance_graph_id=domain_object_instance_graph_id,
            domain_object_instance_graph_identity_id=(
                domain_object_instance_graph_identity_id
            ),
            intent=intent,
            expected_head_commit_ids_by_projection_hash=(
                expected_head_commit_ids_by_projection_hash
            ),
            expected_graph_hash_pre_by_projection_hash=(
                expected_graph_hash_pre_by_projection_hash
            ),
            projection_hash_by_object_id=projection_hash_by_object_id,
        )
        intent_blockers = _tuple_text(input_or_blocked.get("blockers"))
        if intent_blockers:
            blockers.extend(intent_blockers)
            continue
        invoke_input = input_or_blocked.get("input")
        if isinstance(invoke_input, MetaGraphInvokeFunctionInput):
            invoke_inputs.append(invoke_input)
        else:
            blockers.append("aggregate_invoke_input_missing")
    return {
        "blockers": tuple(dict.fromkeys(blockers)),
        "inputs": tuple(invoke_inputs),
    }


def _aggregate_commit_receipts_from_result(result: object) -> tuple[object, ...]:
    if isinstance(result, Mapping):
        for key in ("invocation_receipts", "receipts", "commit_receipts"):
            value = result.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                return tuple(value)
        return ()
    receipts = getattr(result, "invocation_receipts", None)
    if isinstance(receipts, Sequence) and not isinstance(receipts, (str, bytes)):
        return tuple(receipts)
    if isinstance(result, Sequence) and not isinstance(result, (str, bytes)):
        return tuple(result)
    return ()


def _aggregate_commit_execution_payload_from_result(
    *,
    result: object,
    duration_ms: float,
    receipt_count: int,
) -> dict[str, object]:
    payload: dict[str, object] = {}
    if isinstance(result, Mapping):
        execution = result.get("aggregate_commit_execution")
        if isinstance(execution, Mapping):
            payload.update(dict(execution))
    status = _optional_text(payload.get("status")) or "succeeded"
    executor = _optional_text(payload.get("executor")) or "invoke_function_aggregate"
    return {
        **payload,
        "status": status,
        "executor": executor,
        "duration_ms": round(duration_ms, 3),
        "receipt_count": receipt_count,
    }


def _trace_metadata_for_intent(
    *,
    intent: Mapping[str, object],
    invocation_index: int,
) -> dict[str, object]:
    return {
        "invocation_index": invocation_index,
        "intent_key": _optional_text(intent.get("intent_key")),
        "operation_key": _optional_text(intent.get("operation_key")),
        "semantic_key": _optional_text(intent.get("semantic_key")),
        "owner_class_name": _optional_text(intent.get("owner_class_name")),
        "function_name": _optional_text(intent.get("function_name")),
        "invocation_mode": _optional_text(intent.get("invocation_mode")),
    }


def _invoke_function_input_for_intent(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    domain_object_instance_graph_id: UUID | None,
    domain_object_instance_graph_identity_id: UUID | None,
    intent: Mapping[str, object],
    expected_head_commit_ids_by_projection_hash: Mapping[str, UUID | None],
    expected_graph_hash_pre_by_projection_hash: Mapping[str, str | None],
    projection_hash_by_object_id: Mapping[UUID, str],
) -> dict[str, object]:
    owner_class_name = _optional_text(intent.get("owner_class_name"))
    function_name = _optional_text(intent.get("function_name"))
    invocation_mode = _optional_text(intent.get("invocation_mode"))
    blockers: list[str] = []
    if owner_class_name is None:
        blockers.append("owner_class_name_missing")
    if function_name is None:
        blockers.append("function_name_missing")
    if invocation_mode is None:
        blockers.append("invocation_mode_missing")
    if blockers:
        return {"blockers": tuple(blockers)}

    resolution = _resolve_function_for_intent(
        index=index,
        owner_class_name=owner_class_name or "",
        function_name=function_name or "",
    )
    function_id = _uuid_value(resolution.get("function_id"))
    if function_id is None:
        return {
            "blockers": (
                "ontology_function_unresolved:"
                f"{owner_class_name or 'unknown'}.{function_name or 'unknown'}",
            )
        }

    call_target = _call_target_for_mode(invocation_mode or "")
    if call_target is None:
        return {"blockers": (f"unsupported_invocation_mode:{invocation_mode}",)}

    target_object_id = None
    object_projection_graph_id = None
    invocation_projection_hash = projection_hash
    if call_target is MetaGraphCallTarget.instance:
        target_object_id = _uuid_value(intent.get("target_object_id"))
        if target_object_id is None:
            return {"blockers": ("target_object_id_missing_or_invalid",)}
        invocation_projection_hash = _invocation_projection_hash_for_instance_intent(
            index=index,
            intent=intent,
            target_object_id=target_object_id,
            default_projection_hash=projection_hash,
            projection_hash_by_object_id=projection_hash_by_object_id,
        )
    else:
        constructor_opg = _constructor_opg_for_intent(
            index=index,
            intent=intent,
            function_link_id=_uuid_value(resolution.get("function_link_id")),
            function_id=function_id,
        )
        if constructor_opg is None:
            return {
                "blockers": (
                    "ontology_constructor_opg_unresolved:"
                    f"{owner_class_name or 'unknown'}.{function_name or 'unknown'}",
                )
            }
        object_projection_graph_id = _uuid_value(getattr(constructor_opg, "id", None))
        invocation_projection_hash = (
            _optional_text(getattr(constructor_opg, "projection_hash", None))
            or projection_hash
        )

    expected_head_commit_id = expected_head_commit_ids_by_projection_hash.get(
        invocation_projection_hash,
    )
    expected_graph_hash_pre = expected_graph_hash_pre_by_projection_hash.get(
        invocation_projection_hash,
    )

    return {
        "blockers": (),
        "input": MetaGraphInvokeFunctionInput(
            index=index,
            actor_id=actor_id,
            function_id=function_id,
            domain_branch_id=branch_id,
            domain_projection_hash=invocation_projection_hash,
            domain_object_instance_graph_id=domain_object_instance_graph_id,
            domain_object_instance_graph_identity_id=(
                domain_object_instance_graph_identity_id
            ),
            call_target=call_target,
            target_object_id=target_object_id,
            object_projection_graph_id=object_projection_graph_id,
            args=JsonArray([]),
            kwargs=JsonObject(
                cast(dict[str, JsonValue], _mapping_text_keys(intent.get("kwargs")))
            ),
            expected_graph_hash_pre=expected_graph_hash_pre,
            expected_head_commit_id=expected_head_commit_id,
            commit=True,
            publish=False,
        ),
    }


def _resolve_function_for_intent(
    *,
    index: MetaGraphRuntimeIndex,
    owner_class_name: str,
    function_name: str,
) -> dict[str, object]:
    for class_config in _index_class_configs(index=index):
        if not _class_config_matches_owner(
            class_config=class_config,
            owner_class_name=owner_class_name,
        ):
            continue
        for function_link in (
            getattr(
                class_config,
                "class_config_function_configs",
                (),
            )
            or ()
        ):
            function_config = getattr(function_link, "function_config", None)
            if _optional_text(getattr(function_config, "name", None)) != function_name:
                continue
            function_id = getattr(function_config, "id", None) or getattr(
                function_link, "function_config_id", None
            )
            return {
                "class_config_id": getattr(class_config, "id", None),
                "function_link_id": getattr(function_link, "id", None),
                "function_id": function_id,
            }
    return {}


def _invocation_projection_hash_for_instance_intent(
    *,
    index: MetaGraphRuntimeIndex,
    intent: Mapping[str, object],
    target_object_id: UUID,
    default_projection_hash: str,
    projection_hash_by_object_id: Mapping[UUID, str],
) -> str:
    explicit_projection_hash = _optional_text(intent.get("target_projection_hash"))
    if explicit_projection_hash is not None:
        return explicit_projection_hash
    planned_projection_hash = projection_hash_by_object_id.get(target_object_id)
    if planned_projection_hash is not None:
        return planned_projection_hash
    target_projection_name = _optional_text(intent.get("target_projection_name"))
    if target_projection_name is not None:
        resolved = _projection_hash_for_name(
            index=index,
            projection_name=target_projection_name,
        )
        if resolved is not None:
            return resolved
    return default_projection_hash


def _constructor_opg_for_intent(
    *,
    index: MetaGraphRuntimeIndex,
    intent: Mapping[str, object],
    function_link_id: UUID | None,
    function_id: UUID,
) -> object | None:
    explicit_projection_hash = _optional_text(intent.get("result_projection_hash"))
    if explicit_projection_hash is not None:
        opg = _opg_for_projection_hash(
            index=index,
            projection_hash=explicit_projection_hash,
        )
        if opg is not None:
            return opg
    result_projection_name = _optional_text(intent.get("result_projection_name"))
    if result_projection_name is not None:
        opg = _opg_for_projection_name(
            index=index,
            projection_name=result_projection_name,
        )
        if opg is not None:
            return opg
    return _constructor_opg_for_function(
        index=index,
        function_link_id=function_link_id,
        function_id=function_id,
    )


def _projection_hash_for_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> str | None:
    opg = _opg_for_projection_name(
        index=index,
        projection_name=projection_name,
    )
    if opg is not None:
        return _optional_text(getattr(opg, "projection_hash", None))
    return None


def _opg_for_projection_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> object | None:
    for opg in _index_opgs(index=index):
        if _optional_text(getattr(opg, "name", None)) == projection_name:
            return opg
    return None


def _opg_for_projection_hash(
    *,
    index: MetaGraphRuntimeIndex,
    projection_hash: str,
) -> object | None:
    for opg in _index_opgs(index=index):
        if _optional_text(getattr(opg, "projection_hash", None)) == projection_hash:
            return opg
    return None


def _index_class_configs(*, index: MetaGraphRuntimeIndex) -> tuple[object, ...]:
    class_configs = getattr(index, "class_configs_by_id", None)
    if isinstance(class_configs, Mapping):
        return tuple(class_configs.values())
    if isinstance(class_configs, Sequence) and not isinstance(
        class_configs,
        (str, bytes),
    ):
        return tuple(class_configs)
    return ()


def _class_config_matches_owner(
    *,
    class_config: object,
    owner_class_name: str,
) -> bool:
    candidates = _tuple_text(
        (
            getattr(class_config, "name", None),
            getattr(class_config, "class_fqn", None),
        )
    )
    for candidate in candidates:
        if owner_class_name == candidate:
            return True
        if owner_class_name.endswith(f".{candidate}"):
            return True
        if candidate.endswith(f".{owner_class_name}"):
            return True
    return False


def _constructor_opg_for_function(
    *,
    index: MetaGraphRuntimeIndex,
    function_link_id: UUID | None,
    function_id: UUID,
) -> object | None:
    ids = {item for item in (function_link_id, function_id) if item is not None}
    for opg in _index_opgs(index=index):
        for constructor in (
            getattr(
                opg,
                "object_projection_graph_constructors",
                (),
            )
            or ()
        ):
            constructor_function_id = _uuid_value(
                getattr(constructor, "function_constructor_id", None)
            )
            if constructor_function_id in ids:
                return opg
    return None


def _index_opgs(*, index: MetaGraphRuntimeIndex) -> tuple[object, ...]:
    seen: set[str] = set()
    opgs: list[object] = []
    for source in (
        getattr(index, "opg_by_id", None),
        getattr(index, "opg_by_hash", None),
    ):
        for opg in _mapping_or_sequence_values(source):
            opg_id = _optional_text(getattr(opg, "id", None))
            dedupe_key = opg_id or str(id(opg))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            opgs.append(opg)
    return tuple(opgs)


def _mapping_or_sequence_values(value: object) -> Iterable[object]:
    if isinstance(value, Mapping):
        return tuple(value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


def _call_target_for_mode(value: str) -> MetaGraphCallTarget | None:
    if value == MetaGraphCallTarget.instance.value:
        return MetaGraphCallTarget.instance
    if value in {
        "constructor",
        MetaGraphCallTarget.opg_constructor.value,
    }:
        return MetaGraphCallTarget.opg_constructor
    return None


def _sorted_invocation_intents(
    invocation_intents: Sequence[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    return tuple(
        sorted(
            (intent for intent in invocation_intents if isinstance(intent, Mapping)),
            key=lambda intent: (
                _int_value(intent.get("invocation_order")),
                _optional_text(intent.get("intent_key")) or "",
            ),
        )
    )


def _execution_payload(
    *,
    status: str,
    reason: str,
    runtime: object,
    graph_runtime_context: object,
    actor_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    blockers: tuple[str, ...],
    invocation_intents: tuple[Mapping[str, object], ...],
    invocation_receipts: tuple[Mapping[str, object], ...] = (),
    aggregate_commit_execution: Mapping[str, object] | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
) -> dict[str, object]:
    applied = status == "ontology_function_call_execution_applied"
    first_receipt = invocation_receipts[0] if invocation_receipts else {}
    last_receipt = invocation_receipts[-1] if invocation_receipts else {}
    cost_summary = _ontology_invocation_cost_summary(invocation_receipts)
    aggregate_invocation_receipt = _aggregate_invocation_receipt_payload(
        runtime=runtime,
        invocation_receipts=invocation_receipts,
        cost_summary=cost_summary,
        aggregate_commit_execution=aggregate_commit_execution,
    )
    return {
        "execution_kind": "meta_ocg_provider_delta_ontology_invocation_execution",
        "contract_version": ONTOLOGY_INVOCATION_EXECUTION_CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "available": applied,
        "blocked": status == "ontology_function_call_execution_blocked",
        "blockers": tuple(dict.fromkeys(blockers)),
        "blocker_count": len(tuple(dict.fromkeys(blockers))),
        "runtime_backend": type(runtime).__name__,
        "graph_runtime_context_backend": type(graph_runtime_context).__name__,
        "actor_id": str(actor_id),
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "invocation_intent_count": len(invocation_intents),
        "invocation_intents": tuple(dict(intent) for intent in invocation_intents),
        "applied_invocation_count": len(invocation_receipts),
        "invocation_receipts": tuple(dict(receipt) for receipt in invocation_receipts),
        "commit_id": _optional_text(last_receipt.get("commit_id")),
        "domain_commit_id": _optional_text(last_receipt.get("commit_id")),
        "object_instance_graph_commit_id": _optional_text(
            last_receipt.get("object_instance_graph_commit_id")
        ),
        "root_object_id": _optional_text(last_receipt.get("root_object_id")),
        "graph_hash_pre": _optional_text(first_receipt.get("graph_hash_pre")),
        "graph_hash_post": _optional_text(last_receipt.get("graph_hash_post")),
        "error_type": error_type,
        "error_message": error_message,
        "would_execute": bool(invocation_intents),
        "did_execute": applied,
        "would_persist": bool(invocation_intents),
        "did_persist": applied,
        "execution_wired": applied,
        "production_execution_wired": applied,
        "aggregate_invocation_receipt": aggregate_invocation_receipt,
        "aggregate_invocation_receipt_status": (aggregate_invocation_receipt["status"]),
        "aggregate_invocation_receipt_available": (
            aggregate_invocation_receipt["available"]
        ),
        "aggregate_invocation_receipt_contract_version": (
            aggregate_invocation_receipt["contract_version"]
        ),
        "aggregate_commit_execution": (
            dict(aggregate_commit_execution)
            if isinstance(aggregate_commit_execution, Mapping)
            else None
        ),
        **cost_summary,
    }


def _commit_receipt_payload(
    *,
    intent: Mapping[str, object],
    commit_receipt: object,
) -> dict[str, object]:
    payload = _model_payload(commit_receipt)
    return {
        "receipt_kind": "meta_ocg_provider_delta_ontology_invocation_receipt",
        "intent_key": _optional_text(intent.get("intent_key")),
        "operation_key": _optional_text(intent.get("operation_key")),
        "semantic_key": _optional_text(intent.get("semantic_key")),
        "invocation_order": _int_value(intent.get("invocation_order")),
        "invocation_mode": _optional_text(intent.get("invocation_mode")),
        "owner_class_name": _optional_text(intent.get("owner_class_name")),
        "function_name": _optional_text(intent.get("function_name")),
        "status": _optional_text(
            getattr(commit_receipt, "status", None) or payload.get("status")
        ),
        "actor_id": _optional_text(
            getattr(commit_receipt, "actor_id", None) or payload.get("actor_id")
        ),
        "branch_id": _optional_text(
            getattr(commit_receipt, "domain_branch_id", None)
            or payload.get("domain_branch_id")
        ),
        "projection_hash": _optional_text(
            getattr(commit_receipt, "domain_projection_hash", None)
            or payload.get("domain_projection_hash")
        ),
        "expected_result_object_id": _optional_text(
            intent.get("expected_result_object_id")
        ),
        "target_projection_name": _optional_text(intent.get("target_projection_name")),
        "target_projection_hash": _optional_text(intent.get("target_projection_hash")),
        "result_projection_name": _optional_text(intent.get("result_projection_name")),
        "result_projection_hash": _optional_text(intent.get("result_projection_hash")),
        "lane_state_role": _optional_text(intent.get("lane_state_role")),
        "commit_required": _bool_value(intent.get("commit_required")),
        "commit_id": _optional_text(
            getattr(commit_receipt, "commit_id", None) or payload.get("commit_id")
        ),
        "object_instance_graph_commit_id": _optional_text(
            getattr(commit_receipt, "object_instance_graph_commit_id", None)
            or payload.get("object_instance_graph_commit_id")
        ),
        "root_object_id": _optional_text(
            getattr(commit_receipt, "root_object_id", None)
            or payload.get("root_object_id")
        ),
        "graph_hash_pre": _optional_text(
            getattr(commit_receipt, "graph_hash_pre", None)
            or payload.get("graph_hash_pre")
        ),
        "graph_hash_post": _optional_text(
            getattr(commit_receipt, "graph_hash_post", None)
            or payload.get("graph_hash_post")
        ),
        "function_call_id": _optional_text(
            getattr(commit_receipt, "function_call_id", None)
            or payload.get("function_call_id")
        ),
        "function_call_response_id": _optional_text(
            getattr(commit_receipt, "function_call_response_id", None)
            or payload.get("function_call_response_id")
        ),
        "perf_trace_duration_ms": _optional_float(
            getattr(commit_receipt, "perf_trace_duration_ms", None)
            or payload.get("perf_trace_duration_ms")
        ),
        "perf_trace_summary": _perf_trace_summary(
            getattr(commit_receipt, "perf_trace_summary", None)
            or payload.get("perf_trace_summary")
        ),
        "commit_group": _commit_group_payload(
            getattr(commit_receipt, "commit_group", None) or payload.get("commit_group")
        ),
        "error": _optional_text(
            getattr(commit_receipt, "error", None) or payload.get("error")
        ),
    }


def _invoke_function_cost_payload(
    *,
    invoke_input: MetaGraphInvokeFunctionInput,
    duration_ms: float,
    trace_summary: Mapping[str, Mapping[str, float | int]],
) -> dict[str, object]:
    return {
        "invoke_function_duration_ms": round(duration_ms, 3),
        "invoke_function_trace_summary": _perf_trace_summary(trace_summary),
        "invoke_function_core_phase_ms": _compact_core_phase_ms(trace_summary),
        "invoke_call_target": invoke_input.call_target.value,
        "invoke_function_id": str(invoke_input.function_id),
        "invoke_projection_hash": invoke_input.domain_projection_hash,
        "invoke_expected_head_commit_id": _optional_text(
            invoke_input.expected_head_commit_id
        ),
        "invoke_expected_graph_hash_pre": _optional_text(
            invoke_input.expected_graph_hash_pre
        ),
        "invoke_commit_requested": invoke_input.commit,
    }


def _ontology_invocation_cost_summary(
    invocation_receipts: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    function_call_count = len(invocation_receipts)
    core_total_ms = _receipt_metric_total(
        invocation_receipts,
        "invoke_function_duration_ms",
    )
    handler_execute_ms = _receipt_core_phase_total(
        invocation_receipts,
        "runtime.invoke_function.handler_execute_function",
    )
    append_domain_commit_ms = _receipt_core_phase_total(
        invocation_receipts,
        "runtime.invoke_function.append_domain_commit",
    )
    append_invocation_domain_commit_ms = _receipt_core_phase_total(
        invocation_receipts,
        "runtime.invoke_function.append_invocation_domain_commit",
    )
    required_commit_reactions_independent_ms = _receipt_core_phase_total(
        invocation_receipts,
        "runtime.invoke_function.required_commit_reactions",
    )
    required_commit_reactions_batch_ms = _receipt_core_phase_total(
        invocation_receipts,
        "runtime.invoke_function.required_commit_reactions_batch",
    )
    required_commit_reactions_ms = round(
        required_commit_reactions_independent_ms + required_commit_reactions_batch_ms,
        3,
    )
    append_domain_excluding_required_reactions_ms = round(
        max(append_domain_commit_ms - required_commit_reactions_ms, 0.0),
        3,
    )
    oigi_history_upsert_ms = _receipt_core_phase_total(
        invocation_receipts,
        "runtime.invoke_function.required_commit_reactions.oigi_history.upsert_history",
    )
    oigi_history_direct_projection_context_build_ms = _receipt_core_phase_total(
        invocation_receipts,
        "runtime.invoke_function.required_commit_reactions.oigi_history.build_direct_projection_context",
    )
    oigi_history_direct_projection_context_reuse_ms = _receipt_core_phase_total(
        invocation_receipts,
        "runtime.invoke_function.required_commit_reactions.oigi_history.reuse_direct_projection_context",
    )
    oigi_history_pre_state_row_maps_build_ms = _receipt_core_phase_total(
        invocation_receipts,
        "runtime.invoke_function.required_commit_reactions.oigi_history.build_direct_pre_state_row_maps",
    )
    oigi_history_pre_state_row_maps_reuse_ms = _receipt_core_phase_total(
        invocation_receipts,
        "runtime.invoke_function.required_commit_reactions.oigi_history.reuse_direct_pre_state_row_maps",
    )
    oigi_history_source_state_rows_ms = _receipt_core_phase_total(
        invocation_receipts,
        "runtime.invoke_function.required_commit_reactions.oigi_history.build_direct_source_state_rows",
    )
    oigi_history_direct_projection_context_build_count = _receipt_trace_phase_count_total(
        invocation_receipts,
        "runtime.invoke_function.required_commit_reactions.oigi_history.build_direct_projection_context",
    )
    oigi_history_direct_projection_context_reuse_count = _receipt_trace_phase_count_total(
        invocation_receipts,
        "runtime.invoke_function.required_commit_reactions.oigi_history.reuse_direct_projection_context",
    )
    oigi_history_pre_state_row_maps_build_count = _receipt_trace_phase_count_total(
        invocation_receipts,
        "runtime.invoke_function.required_commit_reactions.oigi_history.build_direct_pre_state_row_maps",
    )
    oigi_history_pre_state_row_maps_reuse_count = _receipt_trace_phase_count_total(
        invocation_receipts,
        "runtime.invoke_function.required_commit_reactions.oigi_history.reuse_direct_pre_state_row_maps",
    )
    write_counts = _ontology_invocation_write_count_summary(invocation_receipts)
    direct_change_metrics = _ontology_invocation_direct_change_summary(
        invocation_receipts
    )
    batch_payload = _single_commit_candidate_payload(
        invocation_receipts=invocation_receipts,
        append_domain_commit_ms=append_domain_commit_ms,
    )
    return {
        "ontology_invocation_cost_contract_version": (
            ONTOLOGY_INVOCATION_COST_CONTRACT_VERSION
        ),
        "function_call_count": function_call_count,
        "function_call_commit_core_ms": core_total_ms,
        "handler_execute_ms": handler_execute_ms,
        "append_domain_commit_ms": append_domain_commit_ms,
        "append_domain_excluding_required_reactions_ms": (
            append_domain_excluding_required_reactions_ms
        ),
        "append_invocation_domain_commit_ms": append_invocation_domain_commit_ms,
        "required_commit_reactions_ms": required_commit_reactions_ms,
        "required_commit_reactions_batch_ms": required_commit_reactions_batch_ms,
        "oigi_history_upsert_ms": oigi_history_upsert_ms,
        "oigi_history_direct_projection_context_build_ms": (
            oigi_history_direct_projection_context_build_ms
        ),
        "oigi_history_direct_projection_context_build_count": (
            oigi_history_direct_projection_context_build_count
        ),
        "oigi_history_direct_projection_context_reuse_ms": (
            oigi_history_direct_projection_context_reuse_ms
        ),
        "oigi_history_direct_projection_context_reuse_count": (
            oigi_history_direct_projection_context_reuse_count
        ),
        "oigi_history_pre_state_row_maps_build_ms": (
            oigi_history_pre_state_row_maps_build_ms
        ),
        "oigi_history_pre_state_row_maps_build_count": (
            oigi_history_pre_state_row_maps_build_count
        ),
        "oigi_history_pre_state_row_maps_reuse_ms": (
            oigi_history_pre_state_row_maps_reuse_ms
        ),
        "oigi_history_pre_state_row_maps_reuse_count": (
            oigi_history_pre_state_row_maps_reuse_count
        ),
        "oigi_history_source_state_rows_ms": oigi_history_source_state_rows_ms,
        **write_counts,
        **direct_change_metrics,
        "single_commit_candidate": batch_payload["single_commit_candidate"],
        "batch_blocker_reasons": batch_payload["batch_blocker_reasons"],
        "estimated_batch_savings_ms": batch_payload["estimated_batch_savings_ms"],
        "batch_candidate_projection_hash": batch_payload[
            "batch_candidate_projection_hash"
        ],
    }


def _ontology_invocation_write_count_summary(
    invocation_receipts: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    durable_body_write_count = _receipt_trace_phase_count_total(
        invocation_receipts,
        "oig_commit_store.put_commit_record.durable_body_written",
    )
    durable_body_validate_count = _receipt_trace_phase_count_total(
        invocation_receipts,
        "oig_commit_store.put_commit_record.durable_body_validated",
    )
    durable_envelope_write_count = _receipt_trace_phase_count_total(
        invocation_receipts,
        "oig_commit_store.put_commit_record.durable_envelope_written",
    )
    durable_envelope_validate_count = _receipt_trace_phase_count_total(
        invocation_receipts,
        "oig_commit_store.put_commit_record.durable_envelope_validated",
    )
    durable_head_write_count = sum(
        _receipt_trace_phase_count_total(invocation_receipts, phase)
        for phase in _DURABLE_HEAD_WRITE_PHASES
    )
    durable_meta_write_count = _receipt_trace_phase_count_total(
        invocation_receipts,
        "oig_commit_store.put_commit_record.durable_meta_written",
    )
    durable_meta_validate_count = _receipt_trace_phase_count_total(
        invocation_receipts,
        "oig_commit_store.put_commit_record.durable_meta_validated",
    )
    rebuildable_meta_write_count = _receipt_trace_phase_count_total(
        invocation_receipts,
        "oig_commit_store.put_commit_record.commit_action_meta_written_rebuildable",
    )
    rebuildable_meta_validate_count = _receipt_trace_phase_count_total(
        invocation_receipts,
        "oig_commit_store.put_commit_record.commit_action_meta_validated",
    )
    append_durable_write_count = (
        durable_body_write_count
        + durable_envelope_write_count
        + durable_head_write_count
        + durable_meta_write_count
    )
    append_grouped_durable_write_count = sum(
        _receipt_trace_phase_count_total(invocation_receipts, phase)
        for phase in _APPEND_GROUPED_DURABLE_WRITE_PHASES
    )
    grouped_durable_transaction_count = sum(
        _receipt_trace_phase_count_total(invocation_receipts, phase)
        for phase in _GROUPED_DURABLE_TRANSACTION_COMMIT_PHASES
    )
    aggregate_grouped_durable_transaction_write_count = sum(
        _receipt_trace_phase_count_total(invocation_receipts, phase)
        for phase in _AGGREGATE_GROUPED_DURABLE_WRITE_PHASES
    )
    grouped_durable_transaction_syncfs_count = sum(
        _receipt_trace_phase_count_total(invocation_receipts, phase)
        for phase in _GROUPED_DURABLE_SYNCFS_PHASES
    )
    grouped_durable_transaction_file_fsync_count = sum(
        _receipt_trace_phase_count_total(invocation_receipts, phase)
        for phase in _GROUPED_DURABLE_FILE_FSYNC_PHASES
    )
    append_rebuildable_write_count = rebuildable_meta_write_count
    return {
        "durable_body_write_count": durable_body_write_count,
        "durable_body_validate_count": durable_body_validate_count,
        "durable_envelope_write_count": durable_envelope_write_count,
        "durable_envelope_validate_count": durable_envelope_validate_count,
        "durable_head_write_count": durable_head_write_count,
        "durable_meta_write_count": durable_meta_write_count,
        "durable_meta_validate_count": durable_meta_validate_count,
        "rebuildable_meta_write_count": rebuildable_meta_write_count,
        "rebuildable_meta_validate_count": rebuildable_meta_validate_count,
        "append_durable_write_count": append_durable_write_count,
        "append_grouped_durable_write_count": append_grouped_durable_write_count,
        "append_independent_durable_write_count": max(
            append_durable_write_count - append_grouped_durable_write_count,
            0,
        ),
        "grouped_durable_transaction_count": grouped_durable_transaction_count,
        "aggregate_grouped_durable_transaction_write_count": (
            aggregate_grouped_durable_transaction_write_count
        ),
        "grouped_durable_transaction_syncfs_count": (
            grouped_durable_transaction_syncfs_count
        ),
        "grouped_durable_transaction_file_fsync_count": (
            grouped_durable_transaction_file_fsync_count
        ),
        "append_rebuildable_write_count": append_rebuildable_write_count,
        "commit_action_meta_write_policy": "rebuildable_sidecar",
    }


def _ontology_invocation_direct_change_summary(
    invocation_receipts: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return {
        "impl_delegation_direct_change_evidence_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _IMPL_DELEGATION_DIRECT_CHANGE_PHASE,
            )
        ),
        "impl_delegation_direct_change_evidence_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _IMPL_DELEGATION_DIRECT_CHANGE_PHASE,
            )
        ),
        "impl_delegation_direct_change_evidence_fallback_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _IMPL_DELEGATION_DIRECT_CHANGE_FALLBACK_PHASE,
            )
        ),
        "impl_delegation_direct_change_evidence_fallback_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _IMPL_DELEGATION_DIRECT_CHANGE_FALLBACK_PHASE,
            )
        ),
        "impl_delegation_simple_scalar_direct_evidence_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _IMPL_DELEGATION_SIMPLE_SCALAR_DIRECT_CHANGE_PHASE,
            )
        ),
        "impl_delegation_simple_scalar_direct_evidence_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _IMPL_DELEGATION_SIMPLE_SCALAR_DIRECT_CHANGE_PHASE,
            )
        ),
        "impl_delegation_simple_scalar_direct_evidence_success_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _IMPL_DELEGATION_SIMPLE_SCALAR_DIRECT_CHANGE_SUCCESS_PHASE,
            )
        ),
        "impl_delegation_simple_scalar_direct_evidence_success_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _IMPL_DELEGATION_SIMPLE_SCALAR_DIRECT_CHANGE_SUCCESS_PHASE,
            )
        ),
        "impl_delegation_simple_scalar_direct_evidence_fallback_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _IMPL_DELEGATION_SIMPLE_SCALAR_DIRECT_CHANGE_FALLBACK_PHASE,
            )
        ),
        "impl_delegation_simple_scalar_direct_evidence_fallback_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _IMPL_DELEGATION_SIMPLE_SCALAR_DIRECT_CHANGE_FALLBACK_PHASE,
            )
        ),
        "impl_delegation_post_oig_fallback_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _IMPL_DELEGATION_POST_OIG_FALLBACK_PHASE,
            )
        ),
        "impl_delegation_post_oig_fallback_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _IMPL_DELEGATION_POST_OIG_FALLBACK_PHASE,
            )
        ),
        "session_delta_direct_change_apply_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _SESSION_DELTA_DIRECT_CHANGE_APPLY_PHASE,
            )
        ),
        "session_delta_direct_change_copy_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _SESSION_DELTA_DIRECT_CHANGE_COPY_PHASE,
            )
        ),
        "session_delta_direct_change_hash_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _SESSION_DELTA_DIRECT_CHANGE_HASH_PHASE,
            )
        ),
        "session_delta_direct_change_fingerprint_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _SESSION_DELTA_DIRECT_CHANGE_FINGERPRINT_PHASE,
            )
        ),
        **_ontology_invocation_canonical_apply_summary(invocation_receipts),
        "orm_change_translation_build_ocg_index_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_BUILD_OCG_INDEX_PHASE,
            )
        ),
        "orm_change_translation_ocg_index_cache_build_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_OCG_INDEX_CACHE_BUILD_PHASE,
            )
        ),
        "orm_change_translation_ocg_index_cache_build_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_OCG_INDEX_CACHE_BUILD_PHASE,
            )
        ),
        "orm_change_translation_ocg_index_cache_reuse_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_OCG_INDEX_CACHE_REUSE_PHASE,
            )
        ),
        "orm_change_translation_ocg_index_cache_reuse_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_OCG_INDEX_CACHE_REUSE_PHASE,
            )
        ),
        "orm_change_translation_build_class_instance_changes_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_BUILD_CLASS_INSTANCE_CHANGES_PHASE,
            )
        ),
        "orm_change_translation_build_relationship_changes_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_BUILD_RELATIONSHIP_CHANGES_PHASE,
            )
        ),
        "orm_change_translation_build_detached_class_instance_changes_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_BUILD_DETACHED_CLASS_INSTANCE_CHANGES_PHASE,
            )
        ),
        "orm_change_translation_detached_class_instance_delete_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_DETACHED_CLASS_INSTANCE_DELETE_PHASE,
            )
        ),
        "orm_change_translation_detached_relationship_delete_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_DETACHED_RELATIONSHIP_DELETE_PHASE,
            )
        ),
        "orm_change_translation_class_instance_classify_candidates_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_CLASSIFY_PHASE,
            )
        ),
        "orm_change_translation_class_instance_build_relationship_context_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_CONTEXT_PHASE,
            )
        ),
        "orm_change_translation_class_instance_build_class_instances_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_BUILD_PHASE,
            )
        ),
        "orm_change_translation_class_instance_emit_changes_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_EMIT_PHASE,
            )
        ),
        "orm_change_translation_class_instance_candidate_input_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_CANDIDATE_INPUT_PHASE,
            )
        ),
        "orm_change_translation_class_instance_candidate_selected_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_CANDIDATE_SELECTED_PHASE,
            )
        ),
        "orm_change_translation_class_instance_candidate_pruned_relationship_only_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_CANDIDATE_PRUNED_PHASE,
            )
        ),
        "orm_change_translation_class_instance_candidate_ignored_out_of_projection_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_CANDIDATE_IGNORED_PHASE,
            )
        ),
        **_ontology_invocation_class_instance_profile_summary(invocation_receipts),
        "oig_builder_build_indexes_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _OIG_BUILDER_BUILD_INDEXES_PHASE,
            )
        ),
        "oig_builder_static_index_cache_hit_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _OIG_BUILDER_STATIC_INDEX_CACHE_HIT_PHASE,
            )
        ),
        "oig_builder_static_index_cache_miss_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _OIG_BUILDER_STATIC_INDEX_CACHE_MISS_PHASE,
            )
        ),
        "oig_builder_build_graph_index_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _OIG_BUILDER_BUILD_GRAPH_INDEX_PHASE,
            )
        ),
        "oig_builder_compute_graph_hash_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _OIG_BUILDER_COMPUTE_GRAPH_HASH_PHASE,
            )
        ),
        "session_delta_diff_post_oig_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _SESSION_DELTA_DIFF_POST_OIG_PHASE,
            )
        ),
        "session_delta_diff_post_oig_dirty_class_instance_set_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _SESSION_DELTA_DIFF_POST_OIG_DIRTY_CLASS_INSTANCE_SET_PHASE,
            )
        ),
        "session_delta_diff_post_oig_dirty_class_instance_set_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _SESSION_DELTA_DIFF_POST_OIG_DIRTY_CLASS_INSTANCE_SET_PHASE,
            )
        ),
        "session_delta_diff_post_oig_sparse_identity_snapshot_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _SESSION_DELTA_DIFF_POST_OIG_SPARSE_IDENTITY_SNAPSHOT_PHASE,
            )
        ),
        "session_delta_diff_post_oig_sparse_identity_snapshot_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _SESSION_DELTA_DIFF_POST_OIG_SPARSE_IDENTITY_SNAPSHOT_PHASE,
            )
        ),
        "session_delta_diff_post_oig_full_fallback_count": (
            _receipt_trace_phase_count_total(
                invocation_receipts,
                _SESSION_DELTA_DIFF_POST_OIG_FULL_FALLBACK_PHASE,
            )
        ),
        "session_delta_diff_post_oig_full_fallback_ms": (
            _receipt_trace_phase_total_ms(
                invocation_receipts,
                _SESSION_DELTA_DIFF_POST_OIG_FULL_FALLBACK_PHASE,
            )
        ),
    }


def _ontology_invocation_canonical_apply_summary(
    invocation_receipts: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    metrics: dict[str, object] = {}
    for metric_name, phase in _SESSION_CANONICAL_APPLY_PHASES.items():
        metrics[f"session_canonical_apply_{metric_name}_count"] = (
            _receipt_trace_phase_count_total(invocation_receipts, phase)
        )
        metrics[f"session_canonical_apply_{metric_name}_ms"] = (
            _receipt_trace_phase_total_ms(invocation_receipts, phase)
        )
    return metrics


def _ontology_invocation_class_instance_profile_summary(
    invocation_receipts: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    metrics: dict[str, object] = {}
    for (
        name,
        phase,
    ) in _ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_BUILD_PROFILE_PHASES.items():
        metrics[f"orm_change_translation_class_instance_build_{name}_ms"] = (
            _receipt_trace_phase_total_ms(invocation_receipts, phase)
        )
    for (
        name,
        phase,
    ) in _ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_BUILD_PROFILE_COUNTS.items():
        metrics[f"orm_change_translation_class_instance_build_{name}_count"] = (
            _receipt_trace_phase_count_total(invocation_receipts, phase)
        )
    for (
        name,
        phase,
    ) in _ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_EMISSION_PROFILE_PHASES.items():
        metrics[f"orm_change_translation_class_instance_emission_{name}_ms"] = (
            _receipt_trace_phase_total_ms(invocation_receipts, phase)
        )
    for (
        name,
        phase,
    ) in _ORM_CHANGE_TRANSLATION_CLASS_INSTANCE_EMISSION_PROFILE_COUNTS.items():
        metrics[f"orm_change_translation_class_instance_emission_{name}_count"] = (
            _receipt_trace_phase_count_total(invocation_receipts, phase)
        )
    return metrics


def _single_commit_candidate_payload(
    *,
    invocation_receipts: tuple[Mapping[str, object], ...],
    append_domain_commit_ms: float,
) -> dict[str, object]:
    blockers: list[str] = []
    if len(invocation_receipts) < 2:
        blockers.append("function_call_count_lt_2")

    statuses = {
        status
        for receipt in invocation_receipts
        if (status := _optional_text(receipt.get("status"))) is not None
    }
    if statuses and statuses != {"succeeded"}:
        blockers.append("non_succeeded_function_call")
    if len(statuses) != 1 and invocation_receipts:
        blockers.append("status_missing")

    if any(
        not _bool_value(receipt.get("commit_required"))
        for receipt in invocation_receipts
    ):
        blockers.append("non_commit_required_intent")
    if any(
        _optional_text(receipt.get("commit_id")) is None
        for receipt in invocation_receipts
    ):
        blockers.append("commit_id_missing")

    projection_hashes = _receipt_text_values(invocation_receipts, "projection_hash")
    if not projection_hashes and invocation_receipts:
        blockers.append("projection_hash_missing")
    elif len(projection_hashes) > 1:
        blockers.append("multiple_projection_hashes")

    branch_ids = _receipt_text_values(invocation_receipts, "branch_id")
    if not branch_ids and invocation_receipts:
        blockers.append("branch_id_missing")
    elif len(branch_ids) > 1:
        blockers.append("multiple_branch_ids")

    if not _has_linear_graph_hash_chain(invocation_receipts):
        blockers.append("non_linear_graph_hash_chain")

    unique_blockers = tuple(dict.fromkeys(blockers))
    candidate = not unique_blockers
    per_call_commit_cycle = tuple(
        _receipt_core_phase_value(
            receipt,
            "runtime.invoke_function.append_domain_commit",
        )
        for receipt in invocation_receipts
    )
    estimated_batch_savings_ms = 0.0
    if len(invocation_receipts) > 1 and per_call_commit_cycle:
        estimated_batch_savings_ms = max(
            append_domain_commit_ms - max(per_call_commit_cycle),
            0.0,
        )
    return {
        "single_commit_candidate": candidate,
        "batch_blocker_reasons": unique_blockers,
        "estimated_batch_savings_ms": round(estimated_batch_savings_ms, 3),
        "batch_candidate_projection_hash": (
            projection_hashes[0] if candidate and projection_hashes else None
        ),
    }


def _aggregate_invocation_receipt_payload(
    *,
    runtime: object,
    invocation_receipts: tuple[Mapping[str, object], ...],
    cost_summary: Mapping[str, object],
    aggregate_commit_execution: Mapping[str, object] | None,
) -> dict[str, object]:
    function_call_count = len(invocation_receipts)
    commit_groups = _receipt_commit_groups(invocation_receipts)
    commit_group_summary = _commit_group_summary_payload(commit_groups)
    blockers: list[str] = []
    if function_call_count < 2:
        blockers.append("function_call_count_lt_2")
    if function_call_count >= 2 and not commit_groups:
        blockers.append("commit_group_evidence_missing")
    if any(
        _optional_text(receipt.get("commit_id")) is None
        for receipt in invocation_receipts
    ):
        blockers.append("commit_id_missing")
    unique_blockers = tuple(dict.fromkeys(blockers))
    ready = function_call_count >= 2 and not unique_blockers
    aggregate_commit_backend_available = (
        _invoke_function_aggregate_callable(runtime=runtime) is not None
    )
    aggregate_commit_execution_status = _optional_text(
        aggregate_commit_execution.get("status")
        if isinstance(aggregate_commit_execution, Mapping)
        else None
    )
    aggregate_commit_executed = aggregate_commit_execution_status == "succeeded"
    aggregate_commit_backend_invoked = _aggregate_commit_backend_invoked(
        aggregate_commit_execution=aggregate_commit_execution,
    )
    aggregate_commit_required_mode = _aggregate_commit_required_mode(
        ready=ready,
        cost_summary=cost_summary,
    )
    aggregate_commit_blockers = _aggregate_commit_blockers(
        ready=ready,
        receipt_blockers=unique_blockers,
        required_mode=aggregate_commit_required_mode,
        backend_available=aggregate_commit_backend_available,
        backend_invoked=aggregate_commit_backend_invoked,
        executed=aggregate_commit_executed,
        aggregate_commit_execution=aggregate_commit_execution,
    )
    return {
        "receipt_kind": "meta_ocg_provider_delta_ontology_aggregate_invocation_receipt",
        "contract_version": ONTOLOGY_INVOCATION_AGGREGATE_RECEIPT_CONTRACT_VERSION,
        "status": (
            "aggregate_invocation_receipt_ready"
            if ready
            else "aggregate_invocation_receipt_blocked"
        ),
        "reason": (
            "same_projection_multi_intent_receipt_aggregated"
            if ready
            else "same_projection_multi_intent_receipt_not_aggregated"
        ),
        "available": ready,
        "blocked": not ready,
        "blockers": unique_blockers,
        "blocker_count": len(unique_blockers),
        "function_call_count": function_call_count,
        "invocation_receipt_count": len(invocation_receipts),
        "commit_count": len(_receipt_text_sequence(invocation_receipts, "commit_id")),
        "object_instance_graph_commit_count": len(
            _receipt_text_sequence(
                invocation_receipts,
                "object_instance_graph_commit_id",
            )
        ),
        "commit_ids": _receipt_text_sequence(invocation_receipts, "commit_id"),
        "object_instance_graph_commit_ids": _receipt_text_sequence(
            invocation_receipts,
            "object_instance_graph_commit_id",
        ),
        "branch_ids": _receipt_text_values(invocation_receipts, "branch_id"),
        "projection_hashes": _receipt_text_values(
            invocation_receipts,
            "projection_hash",
        ),
        "graph_hash_pre": (
            _optional_text(invocation_receipts[0].get("graph_hash_pre"))
            if invocation_receipts
            else None
        ),
        "graph_hash_post": (
            _optional_text(invocation_receipts[-1].get("graph_hash_post"))
            if invocation_receipts
            else None
        ),
        "linear_graph_hash_chain": _has_linear_graph_hash_chain(invocation_receipts),
        "single_commit_candidate": bool(cost_summary.get("single_commit_candidate")),
        "estimated_batch_savings_ms": _optional_float(
            cost_summary.get("estimated_batch_savings_ms")
        )
        or 0.0,
        "commit_group_summary": commit_group_summary,
        "current_durability_policy": tuple(
            policy
            for policy in _tuple_text(commit_group_summary.get("durability_policies"))
        ),
        "aggregate_receipt_implemented": True,
        "aggregate_commit_contract_version": (
            ONTOLOGY_INVOCATION_AGGREGATE_COMMIT_CONTRACT_VERSION
        ),
        "aggregate_commit_implemented": aggregate_commit_executed,
        "aggregate_commit_status": (
            "succeeded" if aggregate_commit_executed else "not_implemented"
        ),
        "aggregate_commit_execution_status": aggregate_commit_execution_status,
        "aggregate_commit_backend_invoked": aggregate_commit_backend_invoked,
        "aggregate_commit_durable_transaction_status": _optional_text(
            aggregate_commit_execution.get("durable_transaction_status")
            if isinstance(aggregate_commit_execution, Mapping)
            else None
        ),
        "aggregate_commit_durable_transaction_write_count": _optional_int(
            aggregate_commit_execution.get("durable_transaction_write_count")
            if isinstance(aggregate_commit_execution, Mapping)
            else None
        ),
        "aggregate_commit_durable_transaction_syncfs_count": _optional_int(
            aggregate_commit_execution.get("durable_transaction_syncfs_count")
            if isinstance(aggregate_commit_execution, Mapping)
            else None
        ),
        "aggregate_commit_durable_transaction_file_fsync_count": _optional_int(
            aggregate_commit_execution.get("durable_transaction_file_fsync_count")
            if isinstance(aggregate_commit_execution, Mapping)
            else None
        ),
        "aggregate_commit_durable_transaction_directory_fsync_count": _optional_int(
            aggregate_commit_execution.get("durable_transaction_directory_fsync_count")
            if isinstance(aggregate_commit_execution, Mapping)
            else None
        ),
        "aggregate_commit_durable_transaction_storage_status": _optional_text(
            aggregate_commit_execution.get("durable_transaction_storage_status")
            if isinstance(aggregate_commit_execution, Mapping)
            else None
        ),
        "aggregate_commit_durability_policy": _optional_text(
            aggregate_commit_execution.get("durability_policy")
            if isinstance(aggregate_commit_execution, Mapping)
            else None
        ),
        "aggregate_commit_required_mode": aggregate_commit_required_mode,
        "aggregate_commit_backend_available": aggregate_commit_backend_available,
        "aggregate_commit_blockers": aggregate_commit_blockers,
        "aggregate_commit_execution": (
            dict(aggregate_commit_execution)
            if isinstance(aggregate_commit_execution, Mapping)
            else None
        ),
        "did_execute": ready,
        "did_persist": aggregate_commit_executed,
        "would_persist": ready,
    }


def _aggregate_commit_required_mode(
    *,
    ready: bool,
    cost_summary: Mapping[str, object],
) -> str:
    if not ready:
        return "not_applicable"
    if bool(cost_summary.get("single_commit_candidate")):
        return "single_domain_commit"
    return "grouped_commit_transaction"


def _aggregate_commit_blockers(
    *,
    ready: bool,
    receipt_blockers: tuple[str, ...],
    required_mode: str,
    backend_available: bool,
    backend_invoked: bool,
    executed: bool,
    aggregate_commit_execution: Mapping[str, object] | None,
) -> tuple[str, ...]:
    if not ready:
        return receipt_blockers
    if executed:
        return ()
    execution_blockers = _tuple_text(
        aggregate_commit_execution.get("blockers")
        if isinstance(aggregate_commit_execution, Mapping)
        else None
    )
    if execution_blockers:
        return tuple(
            dict.fromkeys(("aggregate_commit_not_implemented", *execution_blockers))
        )
    if backend_available and backend_invoked:
        return (
            "aggregate_commit_not_implemented",
            "aggregate_commit_backend_invoked_without_grouped_transaction",
        )
    blockers = ["aggregate_commit_not_implemented"]
    if backend_available:
        blockers.append("aggregate_commit_executor_available_not_invoked")
    elif required_mode == "single_domain_commit":
        blockers.append("aggregate_commit_single_domain_backend_unavailable")
    elif required_mode == "grouped_commit_transaction":
        blockers.append("aggregate_commit_grouped_transaction_backend_unavailable")
    else:
        blockers.append("aggregate_commit_backend_unavailable")
    return tuple(dict.fromkeys(blockers))


def _aggregate_commit_backend_invoked(
    *,
    aggregate_commit_execution: Mapping[str, object] | None,
) -> bool:
    if not isinstance(aggregate_commit_execution, Mapping):
        return False
    if _bool_value(aggregate_commit_execution.get("backend_invoked")):
        return True
    return _optional_text(aggregate_commit_execution.get("status")) is not None


def _receipt_commit_groups(
    invocation_receipts: tuple[Mapping[str, object], ...],
) -> tuple[Mapping[str, object], ...]:
    return tuple(
        commit_group
        for receipt in invocation_receipts
        if isinstance((commit_group := receipt.get("commit_group")), Mapping)
    )


def _commit_group_summary_payload(
    commit_groups: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    role_counts: dict[str, int] = {}
    durability_policies: set[str] = set()
    contract_versions: set[str] = set()
    entry_lanes: set[tuple[str, str]] = set()
    domain_lanes: set[tuple[str, str]] = set()
    entry_count = 0
    for group in commit_groups:
        entry_count += _int_value(group.get("entry_count"))
        for role, count in _mapping_items(group.get("role_counts")):
            role_counts[role] = role_counts.get(role, 0) + _int_value(count)
        for entry in _commit_group_entries(group):
            branch_id = _optional_text(entry.get("branch_id"))
            projection_hash = _optional_text(entry.get("projection_hash"))
            if branch_id is not None and projection_hash is not None:
                lane_key = (branch_id, projection_hash)
                entry_lanes.add(lane_key)
                if _optional_text(entry.get("role")) == "domain_commit":
                    domain_lanes.add(lane_key)
        if policy := _optional_text(group.get("durability_policy")):
            durability_policies.add(policy)
        if contract_version := _optional_text(group.get("contract_version")):
            contract_versions.add(contract_version)
    return {
        "group_count": len(commit_groups),
        "entry_count": entry_count,
        "role_counts": dict(sorted(role_counts.items())),
        "durability_policies": tuple(sorted(durability_policies)),
        "contract_versions": tuple(sorted(contract_versions)),
        "entry_lane_count": len(entry_lanes),
        "domain_lane_count": len(domain_lanes),
    }


def _commit_group_entries(
    group: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    entries = group.get("entries")
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        return ()
    return tuple(entry for entry in entries if isinstance(entry, Mapping))


def _mapping_items(value: object) -> tuple[tuple[str, object], ...]:
    if not isinstance(value, Mapping):
        return ()
    return tuple((str(key), item) for key, item in value.items())


def _receipt_text_sequence(
    receipts: tuple[Mapping[str, object], ...],
    key: str,
) -> tuple[str, ...]:
    return tuple(
        value
        for receipt in receipts
        if (value := _optional_text(receipt.get(key))) is not None
    )


def _active_trace_event_count() -> int:
    recorder = current_commit_perf_trace()
    if recorder is None:
        return 0
    return len(recorder.snapshot())


def _active_trace_summary_since(
    offset: int,
) -> dict[str, dict[str, float | int]]:
    recorder = current_commit_perf_trace()
    if recorder is None:
        return {}
    return summarize_commit_perf_events(recorder.snapshot()[offset:])


def _elapsed_ms(started_at: float) -> float:
    return max((perf_counter() - started_at) * 1000.0, 0.0)


def _compact_core_phase_ms(
    trace_summary: Mapping[str, Mapping[str, float | int]],
) -> dict[str, float]:
    return {
        phase: _summary_total_ms(trace_summary.get(phase))
        for phase in _CORE_TRACE_PHASES
        if phase in trace_summary
    }


def _receipt_core_phase_total(
    receipts: tuple[Mapping[str, object], ...],
    phase: str,
) -> float:
    return round(
        sum(_receipt_core_phase_value(receipt, phase) for receipt in receipts),
        3,
    )


def _receipt_core_phase_value(
    receipt: Mapping[str, object],
    phase: str,
) -> float:
    core_phase_ms = receipt.get("invoke_function_core_phase_ms")
    if not isinstance(core_phase_ms, Mapping):
        return 0.0
    return _optional_float(core_phase_ms.get(phase)) or 0.0


def _receipt_metric_total(
    receipts: tuple[Mapping[str, object], ...],
    key: str,
) -> float:
    return round(
        sum(_optional_float(receipt.get(key)) or 0.0 for receipt in receipts),
        3,
    )


def _receipt_trace_phase_count_total(
    receipts: tuple[Mapping[str, object], ...],
    phase: str,
) -> int:
    total = 0
    for receipt in receipts:
        summary = receipt.get("invoke_function_trace_summary")
        if not isinstance(summary, Mapping):
            continue
        stats = summary.get(phase)
        if not isinstance(stats, Mapping):
            continue
        total += _summary_count(cast(Mapping[str, object], stats))
    return total


def _receipt_trace_phase_total_ms(
    receipts: tuple[Mapping[str, object], ...],
    phase: str,
) -> float:
    total = 0.0
    for receipt in receipts:
        summary = receipt.get("invoke_function_trace_summary")
        if not isinstance(summary, Mapping):
            continue
        stats = summary.get(phase)
        if not isinstance(stats, Mapping):
            continue
        total += _summary_total_ms(cast(Mapping[str, object], stats))
    return round(total, 3)


def _summary_total_ms(
    stats: Mapping[str, object] | None,
) -> float:
    if not isinstance(stats, Mapping):
        return 0.0
    value = _optional_float(stats.get("total_ms"))
    if value is None:
        value = _optional_float(stats.get("mean_ms"))
    return round(value or 0.0, 3)


def _summary_count(stats: Mapping[str, object] | None) -> int:
    if not isinstance(stats, Mapping):
        return 0
    return _int_value(stats.get("count"))


def _receipt_text_values(
    receipts: tuple[Mapping[str, object], ...],
    key: str,
) -> tuple[str, ...]:
    values = tuple(
        value
        for receipt in receipts
        if (value := _optional_text(receipt.get(key))) is not None
    )
    return tuple(dict.fromkeys(values))


def _has_linear_graph_hash_chain(
    receipts: tuple[Mapping[str, object], ...],
) -> bool:
    for previous, current in zip(receipts, receipts[1:], strict=False):
        previous_post = _optional_text(previous.get("graph_hash_post"))
        current_pre = _optional_text(current.get("graph_hash_pre"))
        if previous_post is None or current_pre is None:
            return False
        if previous_post != current_pre:
            return False
    return True


def _commit_required_missing(
    *,
    receipt_payload: Mapping[str, object],
) -> bool:
    return (
        _bool_value(receipt_payload.get("commit_required"))
        and _optional_text(receipt_payload.get("commit_id")) is None
    )


def _receipt_object_ids_for_projection_binding(
    *,
    intent: Mapping[str, object],
    receipt_payload: Mapping[str, object],
) -> tuple[UUID, ...]:
    object_ids = tuple(
        object_id
        for object_id in (
            _uuid_value(intent.get("target_object_id")),
            _uuid_value(intent.get("expected_result_object_id")),
            _uuid_value(receipt_payload.get("root_object_id")),
        )
        if object_id is not None
    )
    return tuple(dict.fromkeys(object_ids))


def _request_value(*, request: object, key: str) -> object | None:
    context = getattr(request, "context", None)
    if isinstance(context, Mapping) and key in context:
        return context[key]
    return getattr(request, key, None)


def _invoke_function_callable(
    *,
    runtime: object,
) -> Callable[[MetaGraphInvokeFunctionInput], Awaitable[object]] | None:
    invoke_function = getattr(runtime, "invoke_function", None)
    if not callable(invoke_function):
        return None
    return cast(
        Callable[[MetaGraphInvokeFunctionInput], Awaitable[object]],
        invoke_function,
    )


def _invoke_function_aggregate_callable(
    *,
    runtime: object,
) -> Callable[[tuple[MetaGraphInvokeFunctionInput, ...]], Awaitable[object]] | None:
    invoke_function_aggregate = getattr(runtime, "invoke_function_aggregate", None)
    if not callable(invoke_function_aggregate):
        return None
    return cast(
        Callable[[tuple[MetaGraphInvokeFunctionInput, ...]], Awaitable[object]],
        invoke_function_aggregate,
    )


def _mapping_text_keys(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _model_payload(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="python")
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    return {}


def _commit_group_payload(value: object) -> dict[str, object] | None:
    evidence_payload = getattr(value, "evidence_payload", None)
    if callable(evidence_payload):
        payload = evidence_payload()
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _tuple_text(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        text = str(value)
        return (text,) if text else ()
    if isinstance(value, Iterable):
        return tuple(
            text for item in value if (text := _optional_text(item)) is not None
        )
    text = _optional_text(value)
    return (text,) if text is not None else ()


def _uuid_value(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    text = _optional_text(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _int_value(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    text = _optional_text(value)
    if text is None:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def _optional_int(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    text = _optional_text(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _optional_float(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = _optional_text(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _perf_trace_summary(value: object) -> dict[str, dict[str, float | int]]:
    if not isinstance(value, Mapping):
        return {}
    summary: dict[str, dict[str, float | int]] = {}
    for raw_phase, raw_stats in value.items():
        if not isinstance(raw_stats, Mapping):
            continue
        stats: dict[str, float | int] = {}
        count = _int_value(raw_stats.get("count"))
        if count:
            stats["count"] = count
        for key in ("total_ms", "mean_ms", "max_ms"):
            metric = _optional_float(raw_stats.get(key))
            if metric is not None:
                stats[key] = metric
        if stats:
            summary[str(raw_phase)] = stats
    return summary


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = _optional_text(value)
    if text is None:
        return False
    return text.casefold() in {"1", "true", "yes", "y", "on"}


__all__ = [
    "ONTOLOGY_INVOCATION_AGGREGATE_COMMIT_CONTRACT_VERSION",
    "ONTOLOGY_INVOCATION_EXECUTION_CONTRACT_VERSION",
    "execute_ontology_invocation_intents",
    "ontology_invocation_runtime_preflight",
]
