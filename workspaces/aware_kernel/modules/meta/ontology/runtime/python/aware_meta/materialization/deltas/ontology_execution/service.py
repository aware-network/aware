from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from aware_meta.materialization.deltas.ontology_execution.contracts import (
    ONTOLOGY_EXECUTION_PLAN_CONTRACT_VERSION,
    OntologyExecutionPlanningContext,
    OntologyOperationHandlerResult,
    OntologyTypedOperation,
)
from aware_meta.materialization.deltas.ontology_execution.invocation import (
    ontology_invocation_runtime_preflight,
)
from aware_meta.materialization.deltas.ontology_execution.receiver_resolution import (
    optional_text,
    semantic_object_anchors_from_plan,
    typed_operations_from_plan,
)
from aware_meta.materialization.deltas.ontology_execution.registry import (
    plan_operation,
)
from aware_meta.enum.config.deltas.operation_normalization import (
    coalesced_enum_aggregate_delete_typed_operations,
)
from aware_meta.class_.config.deltas.operation_normalization import (
    coalesced_class_aggregate_delete_typed_operations,
    coalesced_class_create_update_typed_operations,
)


def build_provider_delta_ontology_execution_plan(
    *,
    request: object,
    provider_delta_typed_operation_plan: Mapping[str, object],
) -> dict[str, object]:
    typed_status = optional_text(provider_delta_typed_operation_plan.get("status"))
    if typed_status != "typed_operation_plan_ready":
        return _plan_payload(
            status="ontology_execution_plan_blocked",
            reason="meta_ocg_ontology_execution_requires_ready_typed_operations",
            typed_operation_plan_status=typed_status,
            operation_results=(),
            blockers=(f"typed_operation_plan_not_ready:{typed_status or 'unknown'}",),
            invocation_runtime_preflight=ontology_invocation_runtime_preflight(
                request=request,
            ),
        )

    operations = _coalesced_typed_operations(
        typed_operations_from_plan(
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        )
    )
    context = _planning_context_from_typed_operation_plan(
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        operations=operations,
    )
    if not operations:
        return _plan_payload(
            status="ontology_execution_plan_empty",
            reason="meta_ocg_ontology_execution_no_typed_operations",
            typed_operation_plan_status=typed_status,
            operation_results=(),
            blockers=(),
            invocation_runtime_preflight=ontology_invocation_runtime_preflight(
                request=request,
            ),
        )
    operation_results = tuple(
        plan_operation(operation, context=context) for operation in operations
    )
    blockers = tuple(
        blocker
        for result in operation_results
        for blocker in result.blockers
    )
    status = (
        "ontology_execution_plan_ready"
        if (
            operation_results
            and not blockers
            and all(result.ready for result in operation_results)
        )
        else "ontology_execution_plan_blocked"
    )
    return _plan_payload(
        status=status,
        reason=(
            "meta_ocg_ontology_execution_plan_ready"
            if status == "ontology_execution_plan_ready"
            else "meta_ocg_ontology_execution_plan_blocked"
        ),
        typed_operation_plan_status=typed_status,
        operation_results=operation_results,
        blockers=blockers,
        invocation_runtime_preflight=ontology_invocation_runtime_preflight(
            request=request,
        ),
    )


def _coalesced_typed_operations(
    operations: tuple[OntologyTypedOperation, ...],
) -> tuple[OntologyTypedOperation, ...]:
    coalesced = coalesced_class_aggregate_delete_typed_operations(
        operations=cast(
            Any,
            coalesced_class_create_update_typed_operations(
                operations=cast(
                    Any,
                    coalesced_enum_aggregate_delete_typed_operations(
                        operations=cast(Any, operations),
                    ),
                ),
            ),
        ),
    )
    return cast(tuple[OntologyTypedOperation, ...], coalesced)


def _plan_payload(
    *,
    status: str,
    reason: str,
    typed_operation_plan_status: str | None,
    operation_results: tuple[OntologyOperationHandlerResult, ...],
    blockers: tuple[str, ...],
    invocation_runtime_preflight: Mapping[str, object],
) -> dict[str, object]:
    result_payloads = tuple(
        result.evidence_payload()
        for result in operation_results
    )
    invocation_intents = tuple(
        intent
        for result in result_payloads
        for intent in _tuple_dicts(result.get("invocation_intents"))
    )
    ready = status == "ontology_execution_plan_ready"
    return {
        "plan_kind": "meta_ocg_provider_delta_ontology_execution_plan",
        "contract_version": ONTOLOGY_EXECUTION_PLAN_CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "source": "aware_meta.provider_delta.typed_operations",
        "typed_operation_plan_status": typed_operation_plan_status,
        "operation_handler_result_count": len(result_payloads),
        "operation_handler_results": result_payloads,
        "invocation_intent_count": len(invocation_intents),
        "invocation_intents": invocation_intents,
        "blocker_count": len(blockers),
        "blockers": tuple(dict.fromkeys(blockers)),
        "handler_status_counts": _count_by_field(result_payloads, "status"),
        "handler_reason_counts": _count_by_field(result_payloads, "reason"),
        "invocation_runtime_preflight": dict(invocation_runtime_preflight),
        "available": ready,
        "blocked": status == "ontology_execution_plan_blocked",
        "execution_wired": False,
        "apply_wired": ready,
        "would_execute": ready,
        "did_execute": False,
        "would_persist": ready,
        "did_persist": False,
        "production_execution_wired": False,
    }


def _tuple_dicts(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        {str(key): item for key, item in entry.items()}
        for entry in value
        if isinstance(entry, Mapping)
    )


def _count_by_field(
    entries: tuple[Mapping[str, object], ...],
    field_name: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        value = optional_text(entry.get(field_name)) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _planning_context_from_typed_operation_plan(
    *,
    provider_delta_typed_operation_plan: Mapping[str, object],
    operations: tuple[OntologyTypedOperation, ...],
) -> OntologyExecutionPlanningContext:
    anchors = semantic_object_anchors_from_plan(
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
    )
    by_semantic_key: dict[str, OntologyTypedOperation] = {
        operation.semantic_key: operation
        for operation in (*anchors, *operations)
        if operation.semantic_key
    }
    return OntologyExecutionPlanningContext(
        operation_by_semantic_key=by_semantic_key,
    )


__all__ = ["build_provider_delta_ontology_execution_plan"]
