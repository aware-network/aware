from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from uuid import UUID

from aware_code.semantic_capability import SemanticCapabilityFunctionCallPlan
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_EXECUTION_CONTEXT_KEY,
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
)
from aware_meta.materialization.deltas.baseline import (
    _baseline_hydration_preflight,
    _baseline_ref_payload,
    _int_payload_value,
    _mapping_value,
    _model_payload,
    _optional_text,
    _request_baseline_oig_hydrator,
    _request_value,
    _tuple_text,
    _uuid_value,
)
from aware_meta.materialization.deltas.ontology_execution.invocation import (
    execute_ontology_invocation_intents,
)
from aware_meta.graph.instance.commit.fs_store import FSCommitStore


_EXECUTE_FLAG_PREFLIGHT_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-execute-flag-preflight.v1"
)
_EXECUTION_CONTEXT_PREFLIGHT_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-execution-context-preflight.v1"
)
_EXECUTE_FLAG_COMMIT_RECEIPT_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-execute-flag-commit-receipt.v1"
)
_HEAD_MOVE_APPLIED_RECEIPT_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-head-move-applied-receipt.v1"
)
_ACTIVE_EXECUTION_RAIL_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-active-execution-rail.v1"
)
_META_GRAPH_RUNTIME_CONTEXT_KEY = "aware_meta.graph_runtime_context"
_DELTA_OPERATION_EXECUTION_FLAG = "execute_provider_delta_materialization"
_OBJECT_CONFIG_GRAPH_PROJECTION_NAME = "ObjectConfigGraph"


def _provider_delta_execute_flag_preflight(
    *,
    request: object,
    baseline_dirty_preflight: Mapping[str, object],
    semantic_dirty_diff: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    provider_delta_mutation_plan: Mapping[str, object],
    provider_delta_ontology_execution_plan: Mapping[str, object] | None = None,
    provider_delta_functioncall_capability_matrix: Mapping[str, object] | None = None,
) -> dict[str, object]:
    flag_requested = _operation_execution_requested(request=request)
    hydration = _mapping_value(
        baseline_dirty_preflight.get("baseline_hydration_preflight")
    )
    ontology_execution_plan = dict(provider_delta_ontology_execution_plan or {})
    ontology_runtime_preflight = _mapping_value(
        ontology_execution_plan.get("invocation_runtime_preflight")
    )
    functioncall_capability_matrix = dict(
        provider_delta_functioncall_capability_matrix or {}
    )
    noop_apply_ready = _provider_delta_noop_apply_ready(
        semantic_dirty_diff=semantic_dirty_diff,
        provider_delta_head_move_plan=provider_delta_head_move_plan,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
    )
    active_execution_rail = _provider_delta_active_execution_rail(
        noop_apply_ready=noop_apply_ready,
        provider_delta_ontology_execution_plan=ontology_execution_plan,
        provider_delta_functioncall_capability_matrix=(functioncall_capability_matrix),
    )
    blockers = (
        _execute_flag_preflight_blockers(
            baseline_dirty_preflight=baseline_dirty_preflight,
            request=request,
            hydration=hydration,
            semantic_dirty_diff=semantic_dirty_diff,
            provider_delta_head_move_plan=provider_delta_head_move_plan,
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            provider_delta_mutation_plan=provider_delta_mutation_plan,
            noop_apply_ready=noop_apply_ready,
            provider_delta_ontology_execution_plan=ontology_execution_plan,
            ontology_runtime_preflight=ontology_runtime_preflight,
            provider_delta_functioncall_capability_matrix=(
                functioncall_capability_matrix
            ),
        )
        if flag_requested
        else ()
    )
    status = _execute_flag_preflight_status(
        flag_requested=flag_requested,
        blockers=blockers,
    )
    return {
        "preflight_kind": "meta_ocg_provider_delta_execute_flag_preflight",
        "contract_version": _EXECUTE_FLAG_PREFLIGHT_CONTRACT_VERSION,
        "required_flag": _DELTA_OPERATION_EXECUTION_FLAG,
        "flag_requested": flag_requested,
        "status": status,
        "reason": _execute_flag_preflight_reason(
            flag_requested=flag_requested,
            blockers=blockers,
        ),
        "available": status == "execute_flag_preflight_ready",
        "blocked": status == "execute_flag_preflight_blocked",
        "blockers": blockers,
        "blocker_count": len(blockers),
        "baseline_dirty_preflight_status": _optional_text(
            baseline_dirty_preflight.get("status")
        ),
        "commit_backed_baseline_available": (
            baseline_dirty_preflight.get("commit_backed_baseline_available") is True
        ),
        "baseline_ref_available": (
            baseline_dirty_preflight.get("baseline_ref_available") is True
        ),
        "baseline_ref_hydrator_ready": (
            baseline_dirty_preflight.get("baseline_ref_hydrator_ready") is True
        ),
        "baseline_ref_missing_required_fields": _tuple_text(
            baseline_dirty_preflight.get("baseline_ref_missing_required_fields")
        ),
        "baseline_commit_ref_missing_required_fields": _tuple_text(
            baseline_dirty_preflight.get("missing_required_fields")
        ),
        "baseline_hydration_status": _optional_text(hydration.get("status")),
        "semantic_dirty_diff_status": _optional_text(semantic_dirty_diff.get("status")),
        "semantic_dirty_entry_count": _int_payload_value(
            semantic_dirty_diff,
            "dirty_entry_count",
        ),
        "provider_delta_head_move_status": _optional_text(
            provider_delta_head_move_plan.get("status")
        ),
        "provider_delta_typed_operation_status": _optional_text(
            provider_delta_typed_operation_plan.get("status")
        ),
        "noop_apply": noop_apply_ready,
        "noop_apply_status": (
            "noop_apply_ready" if noop_apply_ready else "noop_apply_not_ready"
        ),
        "provider_delta_mutation_plan_status": _optional_text(
            provider_delta_mutation_plan.get("status")
        ),
        "active_execution_rail": _optional_text(
            active_execution_rail.get("active_execution_rail")
        ),
        "active_execution_status": _optional_text(active_execution_rail.get("status")),
        "active_execution_reason": _optional_text(active_execution_rail.get("reason")),
        "provider_delta_active_execution_rail": active_execution_rail,
        "provider_delta_ontology_execution_status": _optional_text(
            ontology_execution_plan.get("status")
        ),
        "provider_delta_ontology_execution_reason": _optional_text(
            ontology_execution_plan.get("reason")
        ),
        "provider_delta_ontology_execution_invocation_intent_count": (
            _int_payload_value(ontology_execution_plan, "invocation_intent_count")
        ),
        "provider_delta_ontology_execution_blocker_count": _int_payload_value(
            ontology_execution_plan,
            "blocker_count",
        ),
        "provider_delta_ontology_execution_plan": ontology_execution_plan,
        "provider_delta_ontology_invocation_runtime_preflight": (
            ontology_runtime_preflight
        ),
        "provider_delta_functioncall_capability_status": _optional_text(
            functioncall_capability_matrix.get("coverage_status")
        ),
        "provider_delta_functioncall_capability_execution_allowed": (
            functioncall_capability_matrix.get("execution_allowed") is True
        ),
        "provider_delta_functioncall_capability_non_executable_count": (
            _int_payload_value(
                functioncall_capability_matrix,
                "non_executable_operation_count",
            )
        ),
        "provider_delta_functioncall_capability_matrix": (
            functioncall_capability_matrix
        ),
        "execution_wired": active_execution_rail.get("execution_wired") is True,
        "apply_wired": (
            functioncall_capability_matrix.get("execution_allowed") is True
            or noop_apply_ready
        ),
        "would_execute": status == "execute_flag_preflight_ready",
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
        "production_execution_wired": False,
    }


def _provider_delta_active_execution_rail(
    *,
    noop_apply_ready: bool = False,
    provider_delta_ontology_execution_plan: Mapping[str, object],
    provider_delta_functioncall_capability_matrix: Mapping[str, object],
) -> dict[str, object]:
    ontology_status = _optional_text(
        provider_delta_ontology_execution_plan.get("status")
    )
    invocation_intent_count = _int_payload_value(
        provider_delta_ontology_execution_plan,
        "invocation_intent_count",
    )
    functioncall_execution_allowed = (
        provider_delta_functioncall_capability_matrix.get("execution_allowed") is True
    )
    if noop_apply_ready:
        return {
            "rail_kind": "meta_ocg_provider_delta_active_execution_rail",
            "contract_version": _ACTIVE_EXECUTION_RAIL_CONTRACT_VERSION,
            "active_execution_rail": "semantic_noop",
            "status": "active_execution_rail_noop",
            "reason": "meta_ocg_provider_delta_no_semantic_operations",
            "execution_allowed": True,
            "execution_wired": True,
            "production_execution_wired": True,
            "ontology_function_call_execution_allowed": False,
            "ontology_execution_status": ontology_status,
            "ontology_invocation_intent_count": invocation_intent_count,
            "functioncall_capability_status": _optional_text(
                provider_delta_functioncall_capability_matrix.get("coverage_status")
            ),
            "noop_apply": True,
            "blockers": (),
            "blocker_count": 0,
        }
    if (
        functioncall_execution_allowed
        and ontology_status == "ontology_execution_plan_ready"
        and invocation_intent_count > 0
    ):
        return {
            "rail_kind": "meta_ocg_provider_delta_active_execution_rail",
            "contract_version": _ACTIVE_EXECUTION_RAIL_CONTRACT_VERSION,
            "active_execution_rail": "ontology_function_call",
            "status": "active_execution_rail_ready",
            "reason": (
                "meta_ocg_provider_delta_ontology_function_call_active_execution_rail"
            ),
            "execution_allowed": True,
            "execution_wired": True,
            "production_execution_wired": True,
            "ontology_function_call_execution_allowed": True,
            "ontology_execution_status": ontology_status,
            "ontology_invocation_intent_count": invocation_intent_count,
            "functioncall_capability_status": _optional_text(
                provider_delta_functioncall_capability_matrix.get("coverage_status")
            ),
            "blockers": (),
            "blocker_count": 0,
        }

    blockers: list[str] = []
    if ontology_status != "ontology_execution_plan_ready":
        blockers.append(
            f"ontology_execution_plan_not_ready:{ontology_status or 'unknown'}"
        )
    if invocation_intent_count <= 0:
        blockers.append("ontology_execution_plan_has_no_invocation_intents")
    if not functioncall_execution_allowed:
        coverage_status = (
            _optional_text(
                provider_delta_functioncall_capability_matrix.get("coverage_status")
            )
            or "unknown"
        )
        blockers.append(
            "functioncall_capability_matrix_not_executable:" f"{coverage_status}"
        )
    return {
        "rail_kind": "meta_ocg_provider_delta_active_execution_rail",
        "contract_version": _ACTIVE_EXECUTION_RAIL_CONTRACT_VERSION,
        "active_execution_rail": "none",
        "status": "active_execution_rail_blocked",
        "reason": "meta_ocg_provider_delta_no_active_execution_rail",
        "execution_allowed": False,
        "execution_wired": False,
        "production_execution_wired": False,
        "ontology_function_call_execution_allowed": False,
        "ontology_execution_status": ontology_status,
        "ontology_invocation_intent_count": invocation_intent_count,
        "functioncall_capability_status": _optional_text(
            provider_delta_functioncall_capability_matrix.get("coverage_status")
        ),
        "blockers": tuple(dict.fromkeys(blockers)),
        "blocker_count": len(tuple(dict.fromkeys(blockers))),
    }


def _execute_flag_preflight_blockers(
    *,
    baseline_dirty_preflight: Mapping[str, object],
    request: object,
    hydration: Mapping[str, object],
    semantic_dirty_diff: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    provider_delta_mutation_plan: Mapping[str, object],
    noop_apply_ready: bool,
    provider_delta_ontology_execution_plan: Mapping[str, object],
    ontology_runtime_preflight: Mapping[str, object],
    provider_delta_functioncall_capability_matrix: Mapping[str, object],
) -> tuple[str, ...]:
    blockers: list[str] = []
    empty_lane_genesis_apply_ready = _provider_delta_empty_lane_genesis_apply_ready(
        request=request,
        semantic_dirty_diff=semantic_dirty_diff,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        provider_delta_ontology_execution_plan=provider_delta_ontology_execution_plan,
        provider_delta_functioncall_capability_matrix=(
            provider_delta_functioncall_capability_matrix
        ),
    )
    missing_commit_fields = _tuple_text(
        baseline_dirty_preflight.get("missing_required_fields")
    )
    if (
        baseline_dirty_preflight.get("commit_backed_baseline_available") is not True
        and not empty_lane_genesis_apply_ready
    ):
        if missing_commit_fields:
            blockers.extend(
                f"baseline_commit_ref_missing:{field_name}"
                for field_name in missing_commit_fields
            )
        else:
            blockers.append("baseline_commit_refs_unavailable")
    if (
        baseline_dirty_preflight.get("baseline_ref_available") is not True
        and not empty_lane_genesis_apply_ready
    ):
        blockers.append("baseline_ref_missing")
    elif (
        baseline_dirty_preflight.get("baseline_ref_hydrator_ready") is not True
        and not empty_lane_genesis_apply_ready
    ):
        missing_ref_fields = _tuple_text(
            baseline_dirty_preflight.get("baseline_ref_missing_required_fields")
        )
        if missing_ref_fields:
            blockers.extend(
                f"baseline_ref_missing:{field_name}"
                for field_name in missing_ref_fields
            )
        else:
            blockers.append("baseline_ref_incomplete")
    hydration_status = _optional_text(hydration.get("status"))
    if hydration_status != "baseline_hydrated" and not empty_lane_genesis_apply_ready:
        blockers.append(f"baseline_hydration_not_ready:{hydration_status or 'unknown'}")
    dirty_diff_status = _optional_text(semantic_dirty_diff.get("status"))
    if dirty_diff_status != "semantic_dirty_diff_ready":
        blockers.append(
            f"semantic_dirty_diff_not_ready:{dirty_diff_status or 'unknown'}"
        )
    head_move_status = _optional_text(provider_delta_head_move_plan.get("status"))
    if head_move_status != "head_move_plan_ready":
        blockers.append(
            f"provider_delta_head_move_not_ready:{head_move_status or 'unknown'}"
        )
    typed_status = _optional_text(provider_delta_typed_operation_plan.get("status"))
    if typed_status != "typed_operation_plan_ready":
        blockers.append(
            f"provider_delta_typed_operations_not_ready:{typed_status or 'unknown'}"
        )
    if noop_apply_ready:
        return tuple(blockers)
    functioncall_execution_allowed = (
        provider_delta_functioncall_capability_matrix.get("execution_allowed") is True
    )
    mutation_status = _optional_text(provider_delta_mutation_plan.get("status"))
    if mutation_status != "mutation_plan_ready" and not functioncall_execution_allowed:
        blockers.append(
            f"provider_delta_mutation_plan_not_ready:{mutation_status or 'unknown'}"
        )
    ontology_status = _optional_text(
        provider_delta_ontology_execution_plan.get("status")
    )
    if ontology_status != "ontology_execution_plan_ready":
        blockers.append(
            f"ontology_execution_plan_not_ready:{ontology_status or 'unknown'}"
        )
    ontology_blockers = _tuple_text(
        provider_delta_ontology_execution_plan.get("blockers")
    )
    blockers.extend(f"ontology_execution:{blocker}" for blocker in ontology_blockers)
    if (
        _int_payload_value(
            provider_delta_ontology_execution_plan,
            "invocation_intent_count",
        )
        <= 0
    ):
        blockers.append("ontology_execution_plan_has_no_invocation_intents")
    if (
        provider_delta_functioncall_capability_matrix.get("execution_allowed")
        is not True
    ):
        coverage_status = (
            _optional_text(
                provider_delta_functioncall_capability_matrix.get("coverage_status")
            )
            or "unknown"
        )
        blockers.append(
            "functioncall_capability_matrix_not_executable:" f"{coverage_status}"
        )
        blockers.extend(
            f"functioncall_capability:{blocker}"
            for blocker in _tuple_text(
                provider_delta_functioncall_capability_matrix.get("blockers")
            )
        )
    if (
        ontology_runtime_preflight.get("runtime_invoke_function_available") is not True
        and ontology_runtime_preflight.get("runtime_invoke_instance_available")
        is not True
        and not empty_lane_genesis_apply_ready
    ):
        blockers.append("ontology_function_call_runtime_unavailable")
    return tuple(blockers)


def _provider_delta_noop_apply_ready(
    *,
    semantic_dirty_diff: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
) -> bool:
    if _optional_text(semantic_dirty_diff.get("status")) != "semantic_dirty_diff_ready":
        return False
    if semantic_dirty_diff.get("blocked") is True:
        return False
    if _optional_text(provider_delta_head_move_plan.get("status")) != (
        "head_move_plan_ready"
    ):
        return False
    if provider_delta_head_move_plan.get("blocked") is True:
        return False
    if "planned_operation_count" not in provider_delta_head_move_plan:
        return False
    if (
        _int_payload_value(provider_delta_head_move_plan, "planned_operation_count")
        != 0
    ):
        return False
    if _optional_text(provider_delta_typed_operation_plan.get("status")) != (
        "typed_operation_plan_ready"
    ):
        return False
    if provider_delta_typed_operation_plan.get("blocked") is True:
        return False
    if "typed_operation_count" not in provider_delta_typed_operation_plan:
        return False
    if "blocked_operation_count" not in provider_delta_typed_operation_plan:
        return False
    return (
        _int_payload_value(provider_delta_typed_operation_plan, "typed_operation_count")
        == 0
        and _int_payload_value(
            provider_delta_typed_operation_plan,
            "blocked_operation_count",
        )
        == 0
    )


def _provider_delta_empty_lane_genesis_apply_ready(
    *,
    request: object,
    semantic_dirty_diff: Mapping[str, object] | None = None,
    provider_delta_typed_operation_plan: Mapping[str, object] | None = None,
    provider_delta_ontology_execution_plan: Mapping[str, object] | None = None,
    provider_delta_functioncall_capability_matrix: Mapping[str, object] | None = None,
) -> bool:
    lane_state = _model_payload(getattr(request, "provider_delta_lane_state", None))
    if _optional_text(lane_state.get("status")) != "empty_lane":
        return False
    if semantic_dirty_diff is not None and (
        semantic_dirty_diff.get("diff_kind")
        != "meta_ocg_package_genesis_semantic_dirty_diff"
        or semantic_dirty_diff.get("status") != "semantic_dirty_diff_ready"
        or semantic_dirty_diff.get("baseline_identity_source")
        != "workspace.provider_delta_lane_state"
    ):
        return False
    if provider_delta_typed_operation_plan is not None and (
        provider_delta_typed_operation_plan.get("plan_kind")
        != "meta_ocg_package_genesis_typed_operation_plan"
        or provider_delta_typed_operation_plan.get("status")
        != "typed_operation_plan_ready"
        or provider_delta_typed_operation_plan.get("builder_fallback_used") is not False
        or provider_delta_typed_operation_plan.get("would_use_builder") is not False
    ):
        return False
    if provider_delta_ontology_execution_plan is not None and (
        provider_delta_ontology_execution_plan.get("status")
        != "ontology_execution_plan_ready"
        or not _provider_delta_ontology_plan_has_empty_lane_genesis_intents(
            provider_delta_ontology_execution_plan=(
                provider_delta_ontology_execution_plan
            ),
        )
    ):
        return False
    if (
        provider_delta_functioncall_capability_matrix is not None
        and provider_delta_functioncall_capability_matrix.get("execution_allowed")
        is not True
    ):
        return False
    return True


def _provider_delta_ontology_plan_has_empty_lane_genesis_intents(
    *,
    provider_delta_ontology_execution_plan: Mapping[str, object],
) -> bool:
    intents = _tuple_mappings(
        provider_delta_ontology_execution_plan.get("invocation_intents")
    )
    intent_keys = {
        (
            _optional_text(intent.get("owner_class_name")),
            _optional_text(intent.get("function_name")),
        )
        for intent in intents
    }
    return {
        ("ObjectConfigGraphPackage", "build"),
        ("ObjectConfigGraph", "build"),
        ("ObjectProjectionGraph", "build_via_object_config_graph"),
        ("ObjectProjectionGraph", "create_node"),
    }.issubset(intent_keys)


def _provider_delta_execution_context_preflight(
    *,
    request: object,
) -> dict[str, object]:
    graph_context = _request_value(
        request=request,
        key=_META_GRAPH_RUNTIME_CONTEXT_KEY,
    )
    materialization_context = _mapping_value(
        _request_value(
            request=request,
            key=SEMANTIC_MATERIALIZATION_EXECUTION_CONTEXT_KEY,
        )
    )
    projection_hash_by_name = getattr(graph_context, "projection_hash_by_name", None)
    runtime_graph_ids = _tuple_text(getattr(graph_context, "runtime_graph_ids", ()))
    source_graph_ids = _tuple_text(getattr(graph_context, "source_graph_ids", ()))
    graph_context_available = graph_context is not None
    status = (
        "execution_context_available"
        if graph_context_available
        else "execution_context_unavailable"
    )
    reason = (
        "meta_ocg_provider_delta_execution_context_available"
        if graph_context_available
        else "meta_ocg_provider_delta_execution_context_unavailable"
    )
    return {
        "preflight_kind": "meta_ocg_provider_delta_execution_context_preflight",
        "contract_version": _EXECUTION_CONTEXT_PREFLIGHT_CONTRACT_VERSION,
        "context_key": _META_GRAPH_RUNTIME_CONTEXT_KEY,
        "available": graph_context_available,
        "status": status,
        "reason": reason,
        "materialization_execution_context_available": bool(materialization_context),
        "materialization_execution_context_keys": _tuple_text(
            materialization_context.get("context_keys")
        ),
        "provider_materialization_execution_context_keys": _mapping_tuple_text(
            materialization_context.get("provider_context_keys")
        ),
        "runtime_graph_ids": runtime_graph_ids,
        "runtime_graph_count": len(runtime_graph_ids),
        "source_graph_ids": source_graph_ids,
        "source_graph_count": len(source_graph_ids),
        "projection_names": (
            tuple(sorted(str(key) for key in projection_hash_by_name))
            if isinstance(projection_hash_by_name, Mapping)
            else ()
        ),
        "projection_count": (
            len(projection_hash_by_name)
            if isinstance(projection_hash_by_name, Mapping)
            else 0
        ),
    }


def _execute_flag_preflight_status(
    *,
    flag_requested: bool,
    blockers: tuple[str, ...],
) -> str:
    if not flag_requested:
        return "execute_flag_preflight_not_requested"
    if blockers:
        return "execute_flag_preflight_blocked"
    return "execute_flag_preflight_ready"


def _execute_flag_preflight_reason(
    *,
    flag_requested: bool,
    blockers: tuple[str, ...],
) -> str:
    if not flag_requested:
        return "meta_ocg_provider_delta_execute_flag_not_requested"
    if blockers:
        return "meta_ocg_provider_delta_execute_flag_preflight_blocked"
    return "meta_ocg_provider_delta_execute_flag_preflight_ready"


def _provider_delta_head_move_applied_receipt(
    *,
    request: object,
    baseline_dirty_preflight: Mapping[str, object],
    provider_delta_oig_commit_receipt: Mapping[str, object],
) -> dict[str, object]:
    commit_status = _optional_text(provider_delta_oig_commit_receipt.get("status"))
    if commit_status == "execute_flag_commit_noop":
        head_refs = _provider_delta_stayed_head_refs_payload(
            request=request,
            baseline_dirty_preflight=baseline_dirty_preflight,
        )
        blockers = _provider_delta_head_ref_blockers(head_refs=head_refs)
        if blockers:
            head_refs = {
                **head_refs,
                "head_ref_status": "head_refs_partial",
            }
            return _provider_delta_head_move_applied_receipt_payload(
                status="head_move_applied_receipt_blocked",
                reason="meta_ocg_provider_delta_head_refs_incomplete",
                provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
                head_refs=head_refs,
                dirty_status_after_head_move="unknown",
                blockers=blockers,
                blocked=True,
                did_execute=False,
                did_persist=False,
            )
        head_refs = {
            **head_refs,
            "head_ref_status": "head_refs_available",
        }
        return _provider_delta_head_move_applied_receipt_payload(
            status="head_move_applied_receipt_ready",
            reason="meta_ocg_provider_delta_head_stayed_noop",
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
            head_refs=head_refs,
            dirty_status_after_head_move="clean",
            blockers=(),
            blocked=False,
            did_execute=False,
            did_persist=False,
        )
    if commit_status != "execute_flag_commit_applied":
        blocked = commit_status in {
            "execute_flag_commit_blocked",
            "execute_flag_commit_failed",
        }
        blockers = (
            (f"oig_commit_not_applied:{commit_status}",)
            if blocked and commit_status is not None
            else ()
        )
        return _provider_delta_head_move_applied_receipt_payload(
            status="head_move_applied_receipt_unavailable",
            reason="meta_ocg_provider_delta_head_move_requires_applied_oig_commit",
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
            head_refs=_provider_delta_unavailable_head_refs_payload(),
            dirty_status_after_head_move="unknown",
            blockers=blockers,
            blocked=blocked,
        )

    head_refs = _provider_delta_head_refs_payload(
        request=request,
        baseline_dirty_preflight=baseline_dirty_preflight,
        provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
    )
    blockers = _provider_delta_head_ref_blockers(head_refs=head_refs)
    if blockers:
        head_refs = {
            **head_refs,
            "head_ref_status": "head_refs_partial",
        }
        return _provider_delta_head_move_applied_receipt_payload(
            status="head_move_applied_receipt_blocked",
            reason="meta_ocg_provider_delta_head_refs_incomplete",
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
            head_refs=head_refs,
            dirty_status_after_head_move="unknown",
            blockers=blockers,
            blocked=True,
        )

    head_refs = {
        **head_refs,
        "head_ref_status": "head_refs_available",
    }
    return _provider_delta_head_move_applied_receipt_payload(
        status="head_move_applied_receipt_ready",
        reason="meta_ocg_provider_delta_head_move_applied",
        provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
        head_refs=head_refs,
        dirty_status_after_head_move="clean",
        blockers=(),
        blocked=False,
    )


def _provider_delta_head_refs_payload(
    *,
    request: object,
    baseline_dirty_preflight: Mapping[str, object],
    provider_delta_oig_commit_receipt: Mapping[str, object],
) -> dict[str, object]:
    hydration = _mapping_value(
        baseline_dirty_preflight.get("baseline_hydration_preflight")
    )
    baseline_ref = _baseline_ref_payload(request=request) or {}
    lane_state = _model_payload(getattr(request, "provider_delta_lane_state", None))
    lane_package = _mapping_value(lane_state.get("package"))
    final_invocation_receipt = _provider_delta_final_invocation_receipt(
        provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
    )
    domain_commit_id = _optional_text(
        provider_delta_oig_commit_receipt.get("domain_commit_id")
    ) or _optional_text(provider_delta_oig_commit_receipt.get("commit_id"))
    object_instance_graph_commit_id = (
        _optional_text(
            provider_delta_oig_commit_receipt.get("object_instance_graph_commit_id")
        )
        or domain_commit_id
    )
    source_commit_id = (
        _optional_text(hydration.get("source_object_instance_graph_commit_id"))
        or _optional_text(baseline_ref.get("source_object_instance_graph_commit_id"))
        or _optional_text(lane_state.get("source_object_instance_graph_commit_id"))
        or _optional_text(
            getattr(request, "baseline_source_object_instance_graph_commit_id", None)
        )
    )
    semantic_branch_id = (
        _optional_text(provider_delta_oig_commit_receipt.get("branch_id"))
        or _optional_text(hydration.get("semantic_branch_id"))
        or _optional_text(baseline_ref.get("semantic_branch_id"))
        or _optional_text(lane_state.get("semantic_branch_id"))
        or _optional_text(getattr(request, "semantic_branch_id", None))
    )
    semantic_projection_name = (
        _optional_text(hydration.get("semantic_projection_name"))
        or _optional_text(baseline_ref.get("semantic_projection_name"))
        or _optional_text(lane_state.get("semantic_projection_name"))
        or _optional_text(final_invocation_receipt.get("target_projection_name"))
        or _optional_text(final_invocation_receipt.get("result_projection_name"))
    )
    semantic_projection_hash = (
        _optional_text(provider_delta_oig_commit_receipt.get("projection_hash"))
        or _optional_text(hydration.get("semantic_projection_hash"))
        or _optional_text(baseline_ref.get("semantic_projection_hash"))
        or _optional_text(baseline_ref.get("projection_hash"))
    )
    semantic_package_id = (
        _optional_text(hydration.get("semantic_package_id"))
        or _optional_text(baseline_ref.get("semantic_package_id"))
        or _optional_text(lane_state.get("semantic_package_id"))
        or _optional_text(lane_package.get("semantic_package_id"))
    )
    semantic_root_id = (
        _optional_text(hydration.get("semantic_root_id"))
        or _optional_text(baseline_ref.get("semantic_root_id"))
        or _optional_text(lane_state.get("semantic_root_id"))
        or _optional_text(provider_delta_oig_commit_receipt.get("root_object_id"))
        or _optional_text(final_invocation_receipt.get("root_object_id"))
    )
    baseline_semantic_package_commit_id = _optional_text(
        hydration.get("semantic_package_commit_id")
    ) or _optional_text(baseline_ref.get("semantic_package_commit_id"))
    baseline_semantic_oig_commit_id = (
        _optional_text(hydration.get("semantic_object_instance_graph_commit_id"))
        or _optional_text(baseline_ref.get("semantic_object_instance_graph_commit_id"))
        or _optional_text(
            getattr(
                request,
                "baseline_semantic_object_instance_graph_commit_id",
                None,
            )
        )
    )
    baseline_semantic_root_oig_commit_id = (
        _optional_text(hydration.get("semantic_root_object_instance_graph_commit_id"))
        or _optional_text(
            baseline_ref.get("semantic_root_object_instance_graph_commit_id")
        )
        or _optional_text(
            getattr(
                request,
                "baseline_semantic_root_object_instance_graph_commit_id",
                None,
            )
        )
    )
    return {
        "head_ref_status": "head_refs_unavailable",
        "source_object_instance_graph_commit_id": source_commit_id,
        "semantic_branch_id": semantic_branch_id,
        "semantic_projection_name": semantic_projection_name,
        "semantic_projection_hash": semantic_projection_hash,
        "semantic_package_id": semantic_package_id,
        "semantic_root_id": semantic_root_id,
        "semantic_package_commit_id": domain_commit_id,
        "semantic_object_instance_graph_commit_id": (object_instance_graph_commit_id),
        "semantic_root_object_instance_graph_commit_id": (
            object_instance_graph_commit_id
        ),
        "details": {
            "head_ref_source": "meta.provider_delta_oig_commit_receipt",
            "source_object_instance_graph_commit_id_source": ("workspace.baseline_ref"),
            "semantic_package_commit_id_source": (
                "provider_delta_oig_commit_receipt.domain_commit_id"
            ),
            "semantic_object_instance_graph_commit_id_source": (
                "provider_delta_oig_commit_receipt.object_instance_graph_commit_id"
            ),
            "semantic_root_object_instance_graph_commit_id_source": (
                "provider_delta_oig_commit_receipt.object_instance_graph_commit_id"
            ),
            "baseline_semantic_package_commit_id": (
                baseline_semantic_package_commit_id
            ),
            "baseline_semantic_object_instance_graph_commit_id": (
                baseline_semantic_oig_commit_id
            ),
            "baseline_semantic_root_object_instance_graph_commit_id": (
                baseline_semantic_root_oig_commit_id
            ),
            "object_instance_graph_id": _optional_text(
                provider_delta_oig_commit_receipt.get("object_instance_graph_id")
            ),
            "object_instance_graph_identity_id": _optional_text(
                provider_delta_oig_commit_receipt.get(
                    "object_instance_graph_identity_id"
                )
            ),
            "projection_hash": semantic_projection_hash,
            "graph_hash_pre": _optional_text(
                provider_delta_oig_commit_receipt.get("graph_hash_pre")
            ),
            "graph_hash_post": _optional_text(
                provider_delta_oig_commit_receipt.get("graph_hash_post")
            ),
        },
    }


def _provider_delta_stayed_head_refs_payload(
    *,
    request: object,
    baseline_dirty_preflight: Mapping[str, object],
) -> dict[str, object]:
    hydration = _mapping_value(
        baseline_dirty_preflight.get("baseline_hydration_preflight")
    )
    baseline_ref = _baseline_ref_payload(request=request) or {}
    source_commit_id = (
        _optional_text(hydration.get("source_object_instance_graph_commit_id"))
        or _optional_text(baseline_ref.get("source_object_instance_graph_commit_id"))
        or _optional_text(
            getattr(request, "baseline_source_object_instance_graph_commit_id", None)
        )
    )
    semantic_branch_id = _optional_text(
        hydration.get("semantic_branch_id")
    ) or _optional_text(baseline_ref.get("semantic_branch_id"))
    semantic_projection_name = _optional_text(
        hydration.get("semantic_projection_name")
    ) or _optional_text(baseline_ref.get("semantic_projection_name"))
    semantic_projection_hash = (
        _optional_text(hydration.get("semantic_projection_hash"))
        or _optional_text(baseline_ref.get("semantic_projection_hash"))
        or _optional_text(baseline_ref.get("projection_hash"))
    )
    semantic_package_id = _optional_text(
        hydration.get("semantic_package_id")
    ) or _optional_text(baseline_ref.get("semantic_package_id"))
    semantic_root_id = _optional_text(
        hydration.get("semantic_root_id")
    ) or _optional_text(baseline_ref.get("semantic_root_id"))
    semantic_package_commit_id = _optional_text(
        hydration.get("semantic_package_commit_id")
    ) or _optional_text(baseline_ref.get("semantic_package_commit_id"))
    semantic_oig_commit_id = (
        _optional_text(hydration.get("semantic_object_instance_graph_commit_id"))
        or _optional_text(baseline_ref.get("semantic_object_instance_graph_commit_id"))
        or _optional_text(
            getattr(
                request,
                "baseline_semantic_object_instance_graph_commit_id",
                None,
            )
        )
    )
    semantic_root_oig_commit_id = (
        _optional_text(hydration.get("semantic_root_object_instance_graph_commit_id"))
        or _optional_text(
            baseline_ref.get("semantic_root_object_instance_graph_commit_id")
        )
        or _optional_text(
            getattr(
                request,
                "baseline_semantic_root_object_instance_graph_commit_id",
                None,
            )
        )
    )
    return {
        "head_ref_status": "head_refs_unavailable",
        "source_object_instance_graph_commit_id": source_commit_id,
        "semantic_branch_id": semantic_branch_id,
        "semantic_projection_name": semantic_projection_name,
        "semantic_projection_hash": semantic_projection_hash,
        "semantic_package_id": semantic_package_id,
        "semantic_root_id": semantic_root_id,
        "semantic_package_commit_id": semantic_package_commit_id,
        "semantic_object_instance_graph_commit_id": semantic_oig_commit_id,
        "semantic_root_object_instance_graph_commit_id": (semantic_root_oig_commit_id),
        "details": {
            "head_ref_source": "workspace.baseline_ref.noop_head_stayed",
            "source_object_instance_graph_commit_id_source": ("workspace.baseline_ref"),
            "semantic_package_commit_id_source": "workspace.baseline_ref",
            "semantic_object_instance_graph_commit_id_source": (
                "workspace.baseline_ref"
            ),
            "semantic_root_object_instance_graph_commit_id_source": (
                "workspace.baseline_ref"
            ),
            "dirty_status_after_head_move": "clean",
        },
    }


def _provider_delta_head_ref_blockers(
    *,
    head_refs: Mapping[str, object],
) -> tuple[str, ...]:
    required_fields = (
        "source_object_instance_graph_commit_id",
        "semantic_branch_id",
        "semantic_projection_name",
        "semantic_package_id",
        "semantic_root_id",
        "semantic_package_commit_id",
        "semantic_object_instance_graph_commit_id",
        "semantic_root_object_instance_graph_commit_id",
    )
    return tuple(
        f"{field_name}_unavailable"
        for field_name in required_fields
        if _optional_text(head_refs.get(field_name)) is None
    )


def _provider_delta_final_invocation_receipt(
    *,
    provider_delta_oig_commit_receipt: Mapping[str, object],
) -> dict[str, object]:
    execution_receipt = _mapping_value(
        provider_delta_oig_commit_receipt.get(
            "ontology_function_call_execution_receipt"
        )
        or provider_delta_oig_commit_receipt.get(
            "ontology_invocation_execution_receipt"
        )
    )
    invocation_receipts = tuple(
        _mapping_value(item)
        for item in _sequence_value(execution_receipt.get("invocation_receipts"))
        if isinstance(item, Mapping)
    )
    return dict(invocation_receipts[-1]) if invocation_receipts else {}


def _sequence_value(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


def _provider_delta_unavailable_head_refs_payload() -> dict[str, object]:
    return {
        "head_ref_status": "head_refs_unavailable",
        "source_object_instance_graph_commit_id": None,
        "semantic_branch_id": None,
        "semantic_projection_name": None,
        "semantic_package_id": None,
        "semantic_root_id": None,
        "semantic_package_commit_id": None,
        "semantic_object_instance_graph_commit_id": None,
        "semantic_root_object_instance_graph_commit_id": None,
        "details": {},
    }


def _provider_delta_head_move_applied_receipt_payload(
    *,
    status: str,
    reason: str,
    provider_delta_oig_commit_receipt: Mapping[str, object],
    head_refs: Mapping[str, object],
    dirty_status_after_head_move: str,
    blockers: tuple[str, ...],
    blocked: bool,
    did_execute: bool | None = None,
    did_persist: bool | None = None,
) -> dict[str, object]:
    available = status == "head_move_applied_receipt_ready"
    executed = available if did_execute is None else did_execute
    persisted = available if did_persist is None else did_persist
    return {
        "receipt_kind": "meta_ocg_provider_delta_head_move_applied_receipt",
        "contract_version": _HEAD_MOVE_APPLIED_RECEIPT_CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "available": available,
        "blocked": blocked,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "provider_delta_oig_commit_receipt_status": _optional_text(
            provider_delta_oig_commit_receipt.get("status")
        ),
        "provider_delta_oig_commit_receipt_reason": _optional_text(
            provider_delta_oig_commit_receipt.get("reason")
        ),
        "provider_delta_oig_commit_receipt_commit_id": _optional_text(
            provider_delta_oig_commit_receipt.get("commit_id")
        ),
        "head_refs": dict(head_refs),
        "dirty_status_after_head_move": dirty_status_after_head_move,
        "semantic_dirty_status_cleared": available,
        "did_execute": executed,
        "did_persist": persisted,
        "would_execute": bool(provider_delta_oig_commit_receipt.get("would_execute")),
        "would_persist": bool(provider_delta_oig_commit_receipt.get("would_persist")),
        "execution_wired": available,
        "production_execution_wired": available,
    }


async def _provider_delta_oig_commit_receipt(
    *,
    request: object,
    baseline_dirty_preflight: Mapping[str, object],
    provider_delta_mutation_plan: Mapping[str, object],
    provider_delta_ontology_execution_plan: Mapping[str, object] | None = None,
    provider_delta_execute_flag_preflight: Mapping[str, object],
) -> dict[str, object]:
    flag_requested = _operation_execution_requested(request=request)
    if not flag_requested:
        return _provider_delta_oig_commit_receipt_payload(
            status="execute_flag_commit_not_requested",
            reason="meta_ocg_provider_delta_execute_flag_commit_not_requested",
            flag_requested=False,
        )
    if (
        provider_delta_execute_flag_preflight.get("status")
        != "execute_flag_preflight_ready"
    ):
        return _provider_delta_oig_commit_receipt_payload(
            status="execute_flag_commit_blocked",
            reason="meta_ocg_provider_delta_execute_flag_preflight_blocked",
            flag_requested=True,
            blockers=_tuple_text(provider_delta_execute_flag_preflight.get("blockers")),
            execute_flag_preflight_status=_optional_text(
                provider_delta_execute_flag_preflight.get("status")
            ),
        )

    ontology_execution_plan = dict(provider_delta_ontology_execution_plan or {})
    if provider_delta_execute_flag_preflight.get("noop_apply") is True:
        return _provider_delta_oig_commit_receipt_payload(
            status="execute_flag_commit_noop",
            reason="meta_ocg_provider_delta_no_semantic_operations",
            flag_requested=True,
            execute_flag_preflight_status=_optional_text(
                provider_delta_execute_flag_preflight.get("status")
            ),
            ontology_execution_plan=ontology_execution_plan,
        )
    if ontology_execution_plan.get("status") != "ontology_execution_plan_ready":
        return _provider_delta_oig_commit_receipt_payload(
            status="execute_flag_commit_blocked",
            reason="meta_ocg_provider_delta_ontology_execution_plan_not_ready",
            flag_requested=True,
            blockers=_tuple_text(ontology_execution_plan.get("blockers"))
            or (
                "ontology_execution_plan_not_ready:"
                + (_optional_text(ontology_execution_plan.get("status")) or "unknown"),
            ),
            execute_flag_preflight_status=_optional_text(
                provider_delta_execute_flag_preflight.get("status")
            ),
            ontology_execution_plan=ontology_execution_plan,
        )
    ontology_invocation_execution_receipt = (
        await _provider_delta_ontology_function_call_execution_receipt(
            request=request,
            baseline_dirty_preflight=baseline_dirty_preflight,
            provider_delta_ontology_execution_plan=ontology_execution_plan,
        )
    )
    execution_status = _optional_text(
        ontology_invocation_execution_receipt.get("status")
    )
    if execution_status != "ontology_function_call_execution_applied":
        failed = execution_status == "ontology_function_call_execution_failed"
        return _provider_delta_oig_commit_receipt_payload(
            status=(
                "execute_flag_commit_failed"
                if failed
                else "execute_flag_commit_blocked"
            ),
            reason=(
                "meta_ocg_provider_delta_ontology_function_call_execution_failed"
                if failed
                else "meta_ocg_provider_delta_ontology_function_call_execution_blocked"
            ),
            flag_requested=True,
            blockers=_tuple_text(ontology_invocation_execution_receipt.get("blockers")),
            execute_flag_preflight_status=_optional_text(
                provider_delta_execute_flag_preflight.get("status")
            ),
            branch_id=_optional_text(
                ontology_invocation_execution_receipt.get("branch_id")
            ),
            projection_hash=_optional_text(
                ontology_invocation_execution_receipt.get("projection_hash")
            ),
            graph_hash_pre=_optional_text(
                ontology_invocation_execution_receipt.get("graph_hash_pre")
            ),
            graph_hash_post=_optional_text(
                ontology_invocation_execution_receipt.get("graph_hash_post")
            ),
            commit_id=_optional_text(
                ontology_invocation_execution_receipt.get("commit_id")
            ),
            domain_commit_id=_optional_text(
                ontology_invocation_execution_receipt.get("domain_commit_id")
            ),
            object_instance_graph_commit_id=_optional_text(
                ontology_invocation_execution_receipt.get(
                    "object_instance_graph_commit_id"
                )
            ),
            commit_backend=_optional_text(
                ontology_invocation_execution_receipt.get("runtime_backend")
            ),
            ontology_execution_plan=ontology_execution_plan,
            ontology_invocation_execution_receipt=(
                ontology_invocation_execution_receipt
            ),
            error_type=_optional_text(
                ontology_invocation_execution_receipt.get("error_type")
            ),
            error_message=_optional_text(
                ontology_invocation_execution_receipt.get("error_message")
            ),
        )
    return _provider_delta_oig_commit_receipt_payload(
        status="execute_flag_commit_applied",
        reason="meta_ocg_provider_delta_ontology_function_call_commit_applied",
        flag_requested=True,
        execute_flag_preflight_status=_optional_text(
            provider_delta_execute_flag_preflight.get("status")
        ),
        branch_id=_optional_text(
            ontology_invocation_execution_receipt.get("branch_id")
        ),
        projection_hash=_optional_text(
            ontology_invocation_execution_receipt.get("projection_hash")
        ),
        graph_hash_pre=_optional_text(
            ontology_invocation_execution_receipt.get("graph_hash_pre")
        ),
        graph_hash_post=_optional_text(
            ontology_invocation_execution_receipt.get("graph_hash_post")
        ),
        commit_id=_optional_text(
            ontology_invocation_execution_receipt.get("commit_id")
        ),
        domain_commit_id=_optional_text(
            ontology_invocation_execution_receipt.get("domain_commit_id")
        ),
        object_instance_graph_commit_id=_optional_text(
            ontology_invocation_execution_receipt.get("object_instance_graph_commit_id")
        ),
        commit_backend=_optional_text(
            ontology_invocation_execution_receipt.get("runtime_backend")
        ),
        ontology_execution_plan=ontology_execution_plan,
        ontology_invocation_execution_receipt=(ontology_invocation_execution_receipt),
    )


async def _provider_delta_ontology_function_call_execution_receipt(
    *,
    request: object,
    baseline_dirty_preflight: Mapping[str, object],
    provider_delta_ontology_execution_plan: Mapping[str, object],
) -> dict[str, object]:
    hydration = _mapping_value(
        baseline_dirty_preflight.get("baseline_hydration_preflight")
    )
    baseline_ref = _baseline_ref_payload(request=request) or {}
    branch_id_text = (
        _optional_text(
            _request_or_durable_execution_input_value(
                request=request,
                keys=("semantic_branch_id",),
            )
        )
        or _optional_text(hydration.get("semantic_branch_id"))
        or _optional_text(baseline_ref.get("semantic_branch_id"))
    )
    graph_runtime_context = _request_value(
        request=request,
        key=_META_GRAPH_RUNTIME_CONTEXT_KEY,
    )
    semantic_projection_hash = _provider_delta_semantic_projection_hash(
        request=request,
        hydration=hydration,
        baseline_ref=baseline_ref,
    )
    projection_hash = _provider_delta_ontology_invocation_projection_hash(
        request=request,
        hydration=hydration,
        baseline_ref=baseline_ref,
        graph_runtime_context=graph_runtime_context,
    )
    actor_id_text = _request_provider_delta_author_id_text(request=request)
    branch_id = _uuid_value(branch_id_text)
    actor_id = _uuid_value(actor_id_text)
    invocation_intents = _tuple_mappings(
        provider_delta_ontology_execution_plan.get("invocation_intents")
    )
    blockers: list[str] = []
    if branch_id is None:
        blockers.append("semantic_branch_id_unavailable_or_invalid")
    if projection_hash is None:
        blockers.append("semantic_projection_hash_unavailable")
    if actor_id is None:
        blockers.append("author_id_unavailable_or_invalid")
    if not invocation_intents:
        blockers.append("ontology_invocation_intents_empty")
    runtime = _request_value(request=request, key="runtime")
    if runtime is None:
        blockers.append("runtime_unavailable")
    if graph_runtime_context is None:
        blockers.append("graph_runtime_context_unavailable")
    if blockers:
        return {
            "execution_kind": "meta_ocg_provider_delta_ontology_invocation_execution",
            "status": "ontology_function_call_execution_blocked",
            "reason": "meta_ocg_ontology_function_call_execution_inputs_blocked",
            "available": False,
            "blocked": True,
            "blockers": tuple(dict.fromkeys(blockers)),
            "blocker_count": len(tuple(dict.fromkeys(blockers))),
            "runtime_backend": (
                type(runtime).__name__ if runtime is not None else None
            ),
            "graph_runtime_context_backend": (
                type(graph_runtime_context).__name__
                if graph_runtime_context is not None
                else None
            ),
            "actor_id": actor_id_text,
            "branch_id": branch_id_text,
            "projection_hash": projection_hash,
            "invocation_intent_count": len(invocation_intents),
            "did_execute": False,
            "did_persist": False,
            "execution_wired": False,
            "production_execution_wired": False,
        }
    assert branch_id is not None
    assert actor_id is not None
    assert runtime is not None
    assert graph_runtime_context is not None
    assert projection_hash is not None
    empty_lane_genesis_execution = _provider_delta_empty_lane_genesis_apply_ready(
        request=request,
        provider_delta_ontology_execution_plan=provider_delta_ontology_execution_plan,
    )
    if empty_lane_genesis_execution:
        execution_hydration: dict[str, object] = {
            "status": "empty_lane_genesis_baseline_not_required",
            "reason": "meta_ocg_empty_lane_genesis_uses_constructor_bootstrap",
            "did_hydrate_oig": False,
            "execution_full_baseline_oig_required": False,
        }
        initial_head_context: dict[str, UUID | None] = {}
        initial_expected_head_commit_id: UUID | None = None
    else:
        execution_hydration = await _provider_delta_execution_baseline_hydration(
            request=request,
            baseline_dirty_preflight=baseline_dirty_preflight,
            hydration=hydration,
            baseline_ref=baseline_ref,
        )
        execution_hydration_status = _optional_text(execution_hydration.get("status"))
        if execution_hydration_status != "baseline_hydrated":
            return {
                "execution_kind": "meta_ocg_provider_delta_ontology_invocation_execution",
                "status": "ontology_function_call_execution_blocked",
                "reason": (
                    "meta_ocg_ontology_function_call_execution_requires_full_baseline_oig"
                ),
                "available": False,
                "blocked": True,
                "blockers": (
                    "full_baseline_oig_hydration_not_ready:"
                    f"{execution_hydration_status or 'unknown'}",
                ),
                "blocker_count": 1,
                "runtime_backend": type(runtime).__name__,
                "graph_runtime_context_backend": type(graph_runtime_context).__name__,
                "actor_id": actor_id_text,
                "branch_id": branch_id_text,
                "projection_hash": projection_hash,
                "semantic_projection_hash": semantic_projection_hash,
                "invocation_intent_count": len(invocation_intents),
                "baseline_execution_hydration_status": execution_hydration_status,
                "baseline_execution_hydration_reason": _optional_text(
                    execution_hydration.get("reason")
                ),
                "did_execute": False,
                "did_persist": False,
                "execution_wired": False,
                "production_execution_wired": False,
            }
        hydration = execution_hydration
        initial_head_context = await _provider_delta_initial_head_context(
            request=request,
            hydration=hydration,
            baseline_ref=baseline_ref,
            branch_id=branch_id,
            projection_hash=projection_hash,
            semantic_projection_hash=semantic_projection_hash,
        )
        initial_expected_head_commit_id = _uuid_value(
            initial_head_context.get("domain_commit_id")
        )
        if initial_expected_head_commit_id is None:
            return {
                "execution_kind": "meta_ocg_provider_delta_ontology_invocation_execution",
                "status": "ontology_function_call_execution_blocked",
                "reason": "meta_ocg_ontology_function_call_execution_inputs_blocked",
                "available": False,
                "blocked": True,
                "blockers": ("ontology_expected_head_commit_id_unavailable",),
                "blocker_count": 1,
                "runtime_backend": type(runtime).__name__,
                "graph_runtime_context_backend": type(graph_runtime_context).__name__,
                "actor_id": actor_id_text,
                "branch_id": branch_id_text,
                "projection_hash": projection_hash,
                "semantic_projection_hash": semantic_projection_hash,
                "invocation_intent_count": len(invocation_intents),
                "did_execute": False,
                "did_persist": False,
                "execution_wired": False,
                "production_execution_wired": False,
            }
    execution_receipt = await execute_ontology_invocation_intents(
        runtime=runtime,
        graph_runtime_context=graph_runtime_context,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash or "",
        domain_object_instance_graph_id=_uuid_value(
            initial_head_context.get("object_instance_graph_id")
        ),
        domain_object_instance_graph_identity_id=_uuid_value(
            initial_head_context.get("object_instance_graph_identity_id")
        ),
        invocation_intents=invocation_intents,
        initial_expected_head_commit_id=initial_expected_head_commit_id,
    )
    return {
        **execution_receipt,
        "baseline_execution_hydration_status": _optional_text(hydration.get("status")),
        "baseline_execution_hydration_reason": _optional_text(hydration.get("reason")),
        "baseline_execution_hydration_did_force_full_oig": (
            hydration.get("execution_full_baseline_oig_required") is True
        ),
        "baseline_execution_hydration_did_hydrate_oig": (
            hydration.get("did_hydrate_oig") is True
        ),
    }


async def _provider_delta_execution_baseline_hydration(
    *,
    request: object,
    baseline_dirty_preflight: Mapping[str, object],
    hydration: Mapping[str, object],
    baseline_ref: Mapping[str, object],
) -> dict[str, object]:
    if not _baseline_hydration_skipped_full_oig(hydration=hydration):
        return dict(hydration)
    if _request_baseline_oig_hydrator(request=request) is None:
        blocked = dict(hydration)
        blocked.update(
            {
                "status": "baseline_hydrator_unavailable",
                "reason": (
                    "meta_ocg_ontology_function_call_execution_requires_full_oig_hydrator"
                ),
                "execution_full_baseline_oig_required": True,
            }
        )
        return blocked

    execution_request = _FullBaselineOigHydrationRequest(request=request)
    execution_hydration = await _baseline_hydration_preflight(
        request=execution_request,
        baseline_ref=baseline_ref,
        commit_backed_baseline_available=(
            baseline_dirty_preflight.get("commit_backed_baseline_available") is True
        ),
        missing_baseline_ref_fields=_tuple_text(
            baseline_dirty_preflight.get("baseline_ref_missing_required_fields")
        ),
    )
    if _optional_text(execution_hydration.get("status")) == "baseline_hydrated":
        execution_hydration = dict(execution_hydration)
        execution_hydration["execution_full_baseline_oig_required"] = True
        execution_hydration["did_hydrate_oig"] = True
    return execution_hydration


def _baseline_hydration_skipped_full_oig(
    *,
    hydration: Mapping[str, object],
) -> bool:
    details = _mapping_value(hydration.get("details"))
    materializer_metadata = _mapping_value(details.get("materializer_metadata"))
    if hydration.get("did_hydrate_oig") is False:
        return True
    if materializer_metadata.get("oig_materialization_skipped") is True:
        return True
    return (
        _optional_text(
            materializer_metadata.get("baseline_semantic_object_index_source")
        )
        == "aware_meta.runtime.package_index"
    )


class _FullBaselineOigHydrationRequest:
    require_full_baseline_oig = True
    meta_baseline_hydration_requires_oig = True

    def __init__(self, *, request: object) -> None:
        self._request = request

    def __getattr__(self, name: str) -> object:
        request = self._request
        if isinstance(request, Mapping):
            try:
                return request[name]
            except KeyError:
                pass
        return getattr(request, name)


def _tuple_mappings(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        {str(key): item for key, item in entry.items()}
        for entry in value
        if isinstance(entry, Mapping)
    )


def _provider_delta_semantic_projection_hash(
    *,
    request: object,
    hydration: Mapping[str, object],
    baseline_ref: Mapping[str, object],
) -> str | None:
    return (
        _optional_text(
            _request_or_durable_execution_input_value(
                request=request,
                keys=(
                    "provider_delta_semantic_projection_hash",
                    "semantic_projection_hash",
                    "projection_hash",
                ),
            )
        )
        or _optional_text(hydration.get("semantic_projection_hash"))
        or _optional_text(baseline_ref.get("semantic_projection_hash"))
    )


def _provider_delta_ontology_invocation_projection_hash(
    *,
    request: object,
    hydration: Mapping[str, object],
    baseline_ref: Mapping[str, object],
    graph_runtime_context: object,
) -> str | None:
    return (
        _optional_text(
            _request_or_durable_execution_input_value(
                request=request,
                keys=(
                    "provider_delta_ontology_projection_hash",
                    "semantic_root_projection_hash",
                    "root_semantic_projection_hash",
                    "object_config_graph_projection_hash",
                ),
            )
        )
        or _graph_context_projection_hash_for_name(
            graph_runtime_context=graph_runtime_context,
            projection_name=_OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
        )
        or _provider_delta_semantic_projection_hash(
            request=request,
            hydration=hydration,
            baseline_ref=baseline_ref,
        )
    )


def _graph_context_projection_hash_for_name(
    *,
    graph_runtime_context: object,
    projection_name: str,
) -> str | None:
    projection_hash_for_name = getattr(
        graph_runtime_context,
        "projection_hash_for_name",
        None,
    )
    if callable(projection_hash_for_name):
        try:
            return _optional_text(projection_hash_for_name(projection_name))
        except Exception:
            return None
    projection_hash_by_name = getattr(
        graph_runtime_context,
        "projection_hash_by_name",
        None,
    )
    if isinstance(projection_hash_by_name, Mapping):
        return _optional_text(projection_hash_by_name.get(projection_name))
    return None


async def _provider_delta_initial_head_context(
    *,
    request: object,
    hydration: Mapping[str, object],
    baseline_ref: Mapping[str, object],
    branch_id: UUID,
    projection_hash: str,
    semantic_projection_hash: str | None,
) -> dict[str, UUID | None]:
    explicit_head_commit_id = _uuid_value(
        _optional_text(
            _request_or_durable_execution_input_value(
                request=request,
                keys=(
                    "provider_delta_ontology_head_commit_id",
                    "semantic_root_commit_id",
                    "root_semantic_commit_id",
                ),
            )
        )
    )
    if explicit_head_commit_id is not None:
        return _merge_head_context(
            {"domain_commit_id": explicit_head_commit_id},
            _provider_delta_hydrated_head_context(
                hydration=hydration,
                baseline_ref=baseline_ref,
            ),
        )
    if projection_hash != semantic_projection_hash:
        return await _provider_delta_root_head_context(
            request=request,
            hydration=hydration,
            baseline_ref=baseline_ref,
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
    domain_commit_id = (
        _provider_delta_baseline_domain_commit_id(
            request=request,
            hydration=hydration,
            baseline_ref=baseline_ref,
        )
        or _uuid_value(
            _optional_text(
                _request_or_durable_execution_input_value(
                    request=request,
                    keys=(
                        "baseline_semantic_object_instance_graph_commit_id",
                        "semantic_object_instance_graph_commit_id",
                    ),
                )
            )
        )
        or _uuid_value(hydration.get("semantic_object_instance_graph_commit_id"))
        or _uuid_value(baseline_ref.get("semantic_object_instance_graph_commit_id"))
    )
    context = _merge_head_context(
        {"domain_commit_id": domain_commit_id},
        _provider_delta_hydrated_head_context(
            hydration=hydration,
            baseline_ref=baseline_ref,
        ),
    )
    if domain_commit_id is not None and (
        context.get("object_instance_graph_id") is None
        or context.get("object_instance_graph_identity_id") is None
    ):
        context = _merge_head_context(
            context,
            await _provider_delta_domain_commit_head_context(
                request=request,
                branch_id=branch_id,
                projection_hash=projection_hash,
                domain_commit_id=domain_commit_id,
            ),
        )
    return context


async def _provider_delta_root_head_context(
    *,
    request: object,
    hydration: Mapping[str, object],
    baseline_ref: Mapping[str, object],
    branch_id: UUID,
    projection_hash: str,
) -> dict[str, UUID | None]:
    root_oig_commit_id = (
        _uuid_value(
            _optional_text(
                _request_or_durable_execution_input_value(
                    request=request,
                    keys=(
                        "baseline_semantic_root_object_instance_graph_commit_id",
                        "semantic_root_object_instance_graph_commit_id",
                    ),
                )
            )
        )
        or _uuid_value(hydration.get("semantic_root_object_instance_graph_commit_id"))
        or _uuid_value(
            baseline_ref.get("semantic_root_object_instance_graph_commit_id")
        )
    )
    if root_oig_commit_id is None:
        return {}
    try:
        store = FSCommitStore(root_dir=_provider_delta_workspace_root(request=request))
        domain_commit_id = (
            await store.domain_commit_id_for_object_instance_graph_commit_id(
                branch_id=branch_id,
                projection_hash=projection_hash,
                object_instance_graph_commit_id=root_oig_commit_id,
            )
        )
        if domain_commit_id is None:
            return {}
    except Exception:
        return {}
    return _merge_head_context(
        {"domain_commit_id": domain_commit_id},
        await _provider_delta_domain_commit_head_context(
            request=request,
            branch_id=branch_id,
            projection_hash=projection_hash,
            domain_commit_id=domain_commit_id,
        ),
    )


async def _provider_delta_domain_commit_head_context(
    *,
    request: object,
    branch_id: UUID,
    projection_hash: str,
    domain_commit_id: UUID,
) -> dict[str, UUID | None]:
    object_instance_graph_id: UUID | None = None
    object_instance_graph_identity_id: UUID | None = None
    store = FSCommitStore(root_dir=_provider_delta_workspace_root(request=request))
    try:
        head = await store.head(branch_id=branch_id, projection_hash=projection_hash)
        if head is not None and _uuid_value(head.get("commit_id")) == domain_commit_id:
            object_instance_graph_id = _uuid_value(head.get("object_instance_graph_id"))
            object_instance_graph_identity_id = _uuid_value(
                head.get("object_instance_graph_identity_id")
            )
    except Exception:
        pass
    if object_instance_graph_id is None or object_instance_graph_identity_id is None:
        try:
            domain_commit = await store.get_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=domain_commit_id,
            )
            object_instance_graph_id = object_instance_graph_id or _uuid_value(
                getattr(domain_commit, "object_instance_graph_id", None)
            )
            object_instance_graph_identity_id = (
                object_instance_graph_identity_id
                or _uuid_value(
                    getattr(domain_commit, "object_instance_graph_identity_id", None)
                )
            )
        except Exception:
            pass
    return {
        "object_instance_graph_id": object_instance_graph_id,
        "object_instance_graph_identity_id": object_instance_graph_identity_id,
    }


def _provider_delta_hydrated_head_context(
    *,
    hydration: Mapping[str, object],
    baseline_ref: Mapping[str, object],
) -> dict[str, UUID | None]:
    details = _mapping_value(hydration.get("details"))
    materializer_metadata = _mapping_value(details.get("materializer_metadata"))
    return {
        "object_instance_graph_id": (
            _uuid_value(materializer_metadata.get("object_instance_graph_id"))
            or _uuid_value(hydration.get("object_instance_graph_id"))
            or _uuid_value(baseline_ref.get("object_instance_graph_id"))
        ),
        "object_instance_graph_identity_id": (
            _uuid_value(materializer_metadata.get("object_instance_graph_identity_id"))
            or _uuid_value(hydration.get("object_instance_graph_identity_id"))
            or _uuid_value(baseline_ref.get("object_instance_graph_identity_id"))
        ),
    }


def _merge_head_context(
    *contexts: Mapping[str, UUID | None],
) -> dict[str, UUID | None]:
    merged: dict[str, UUID | None] = {}
    for context in contexts:
        for key, value in context.items():
            if value is not None or key not in merged:
                merged[key] = value
    return merged


def _provider_delta_baseline_domain_commit_id(
    *,
    request: object,
    hydration: Mapping[str, object],
    baseline_ref: Mapping[str, object],
) -> UUID | None:
    details = _mapping_value(hydration.get("details"))
    materializer_metadata = _mapping_value(details.get("materializer_metadata"))
    return (
        _uuid_value(materializer_metadata.get("domain_commit_id"))
        or _uuid_value(hydration.get("domain_commit_id"))
        or _uuid_value(
            _optional_text(
                _request_or_durable_execution_input_value(
                    request=request,
                    keys=(
                        "provider_delta_ontology_head_commit_id",
                        "baseline_semantic_object_instance_graph_commit_id",
                        "semantic_object_instance_graph_commit_id",
                    ),
                )
            )
        )
        or _uuid_value(hydration.get("semantic_object_instance_graph_commit_id"))
        or _uuid_value(baseline_ref.get("semantic_object_instance_graph_commit_id"))
        or _uuid_value(
            _optional_text(
                _request_or_durable_execution_input_value(
                    request=request,
                    keys=(
                        "baseline_semantic_package_commit_id",
                        "semantic_package_commit_id",
                        "semantic_head_commit_id",
                    ),
                )
            )
        )
        or _uuid_value(baseline_ref.get("semantic_package_commit_id"))
        or _uuid_value(baseline_ref.get("semantic_head_commit_id"))
    )


def _provider_delta_durable_execution_inputs_payload(
    *,
    request: object,
) -> dict[str, object]:
    value = _request_value(
        request=request,
        key=SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    )
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="python")
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    return {}


def _provider_delta_durable_execution_input_value(
    *,
    request: object,
    keys: tuple[str, ...],
) -> object | None:
    payload = _provider_delta_durable_execution_inputs_payload(request=request)
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    provider_inputs = payload.get("provider_inputs")
    if isinstance(provider_inputs, Mapping):
        for key in keys:
            value = provider_inputs.get(key)
            if value is not None:
                return value
    return None


def _request_or_durable_execution_input_value(
    *,
    request: object,
    keys: tuple[str, ...],
) -> object | None:
    value = _provider_delta_durable_execution_input_value(
        request=request,
        keys=keys,
    )
    if value is not None:
        return value
    for key in keys:
        value = _request_value(request=request, key=key)
        if value is not None:
            return value
    return None


def _provider_delta_shared_execution_inputs_available(
    *,
    request: object,
) -> bool:
    payload = _provider_delta_durable_execution_inputs_payload(request=request)
    return bool(payload)


def _request_provider_delta_author_id_text(*, request: object) -> str | None:
    return _optional_text(
        _request_or_durable_execution_input_value(
            request=request,
            keys=("provider_delta_author_id", "author_id", "actor_id"),
        )
    )


def _provider_delta_workspace_root(*, request: object) -> Path | None:
    value = _request_or_durable_execution_input_value(
        request=request,
        keys=("workspace_root",),
    )
    text = _optional_text(value)
    return Path(text).expanduser().resolve() if text is not None else None


def _provider_delta_oig_commit_receipt_payload(
    *,
    status: str,
    reason: str,
    flag_requested: bool,
    blockers: tuple[str, ...] = (),
    execute_flag_preflight_status: str | None = None,
    branch_id: str | None = None,
    projection_hash: str | None = None,
    object_instance_graph_id: str | None = None,
    object_instance_graph_identity_id: str | None = None,
    graph_hash_pre: str | None = None,
    graph_hash_post: str | None = None,
    commit_id: str | None = None,
    domain_commit_id: str | None = None,
    object_instance_graph_commit_id: str | None = None,
    commit_backend: str | None = None,
    ontology_execution_plan: Mapping[str, object] | None = None,
    ontology_invocation_execution_receipt: Mapping[str, object] | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
) -> dict[str, object]:
    applied = status == "execute_flag_commit_applied"
    noop = status == "execute_flag_commit_noop"
    ontology_invocation_receipt = dict(ontology_invocation_execution_receipt or {})
    return {
        "receipt_kind": "meta_ocg_provider_delta_execute_flag_commit_receipt",
        "contract_version": _EXECUTE_FLAG_COMMIT_RECEIPT_CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "available": applied or noop,
        "blocked": status == "execute_flag_commit_blocked",
        "blockers": blockers,
        "blocker_count": len(blockers),
        "flag_requested": flag_requested,
        "execute_flag_preflight_status": execute_flag_preflight_status,
        "branch_id": branch_id,
        "projection_hash": projection_hash,
        "object_instance_graph_id": object_instance_graph_id,
        "object_instance_graph_identity_id": object_instance_graph_identity_id,
        "graph_hash_pre": graph_hash_pre,
        "graph_hash_post": graph_hash_post,
        "commit_id": commit_id,
        "domain_commit_id": domain_commit_id,
        "object_instance_graph_commit_id": object_instance_graph_commit_id,
        "commit_backend": commit_backend,
        "error_type": error_type,
        "error_message": error_message,
        "provider_delta_ontology_execution_plan": dict(ontology_execution_plan or {}),
        "provider_delta_ontology_execution_status": _optional_text(
            (ontology_execution_plan or {}).get("status")
        ),
        "provider_delta_ontology_execution_reason": _optional_text(
            (ontology_execution_plan or {}).get("reason")
        ),
        "ontology_function_call_execution_receipt": ontology_invocation_receipt,
        "ontology_function_call_execution_status": _optional_text(
            ontology_invocation_receipt.get("status")
        ),
        "ontology_function_call_execution_reason": _optional_text(
            ontology_invocation_receipt.get("reason")
        ),
        "ontology_function_call_execution_invocation_count": _int_payload_value(
            ontology_invocation_receipt,
            "invocation_intent_count",
        ),
        "ontology_function_call_execution_applied_invocation_count": (
            _int_payload_value(
                ontology_invocation_receipt,
                "applied_invocation_count",
            )
        ),
        "did_execute": applied,
        "did_persist": applied,
        "would_execute": flag_requested and not noop,
        "would_persist": flag_requested and not noop,
        "execution_wired": applied or noop,
        "production_execution_wired": applied or noop,
    }


def _operation_execution_detail(
    *,
    request: object,
    function_call_plans: tuple[SemanticCapabilityFunctionCallPlan, ...],
    baseline_dirty_preflight: Mapping[str, object] | None = None,
    provider_delta_execute_flag_preflight: Mapping[str, object] | None = None,
    provider_delta_oig_commit_receipt: Mapping[str, object] | None = None,
) -> dict[str, object]:
    flag_requested = _operation_execution_requested(request=request)
    preflight_status = (
        _optional_text(provider_delta_execute_flag_preflight.get("status"))
        if provider_delta_execute_flag_preflight is not None
        else None
    )
    preflight_blocked = preflight_status == "execute_flag_preflight_blocked"
    commit_status = (
        _optional_text(provider_delta_oig_commit_receipt.get("status"))
        if provider_delta_oig_commit_receipt is not None
        else None
    )
    active_execution_rail = (
        _mapping_value(
            provider_delta_execute_flag_preflight.get(
                "provider_delta_active_execution_rail"
            )
        )
        if provider_delta_execute_flag_preflight is not None
        else {}
    )
    commit_applied = commit_status == "execute_flag_commit_applied"
    commit_noop = commit_status == "execute_flag_commit_noop"
    commit_failed = commit_status == "execute_flag_commit_failed"
    commit_blocked = commit_status == "execute_flag_commit_blocked"
    return {
        "execution_kind": "meta_ocg_provider_delta_operation_execution",
        "required_flag": _DELTA_OPERATION_EXECUTION_FLAG,
        "flag_requested": flag_requested,
        "operation_count": len(function_call_plans),
        "semantic_function_call_plan_count": len(function_call_plans),
        "would_execute": (
            flag_requested
            and preflight_status != "execute_flag_preflight_blocked"
            and not commit_noop
        ),
        "did_execute": commit_applied,
        "would_persist": flag_requested and not preflight_blocked and not commit_noop,
        "receipt_persistence_contract_ready": commit_applied or commit_noop,
        "status": (
            "flag_required"
            if not flag_requested
            else (
                "executed"
                if commit_applied
                else (
                    "executed_noop"
                    if commit_noop
                    else (
                        "execution_commit_failed"
                        if commit_failed
                        else (
                            "execution_commit_blocked"
                            if commit_blocked and not preflight_blocked
                            else (
                                "execute_preflight_blocked"
                                if preflight_blocked
                                else "execution_not_wired"
                            )
                        )
                    )
                )
            )
        ),
        "reason": (
            "meta_ocg_provider_delta_operation_execution_requires_explicit_flag"
            if not flag_requested
            else (
                "meta_ocg_provider_delta_operation_execution_committed"
                if commit_applied
                else (
                    "meta_ocg_provider_delta_operation_execution_noop"
                    if commit_noop
                    else (
                        "meta_ocg_provider_delta_operation_execution_commit_failed"
                        if commit_failed
                        else (
                            "meta_ocg_provider_delta_operation_execution_commit_blocked"
                            if commit_blocked and not preflight_blocked
                            else (
                                "meta_ocg_provider_delta_operation_execution_preflight_blocked"
                                if preflight_blocked
                                else "meta_ocg_provider_delta_operation_execution_not_wired"
                            )
                        )
                    )
                )
            )
        ),
        "execution_wired": commit_applied or commit_noop,
        "did_persist": commit_applied,
        "execute_flag_preflight_status": preflight_status,
        "active_execution_rail": _optional_text(
            active_execution_rail.get("active_execution_rail")
        ),
        "active_execution_status": _optional_text(active_execution_rail.get("status")),
        "active_execution_reason": _optional_text(active_execution_rail.get("reason")),
        "provider_delta_active_execution_rail": active_execution_rail,
        "execute_flag_preflight": (
            dict(provider_delta_execute_flag_preflight)
            if provider_delta_execute_flag_preflight is not None
            else None
        ),
        "oig_commit_receipt_status": commit_status,
        "oig_commit_receipt": (
            dict(provider_delta_oig_commit_receipt)
            if provider_delta_oig_commit_receipt is not None
            else None
        ),
        "baseline_dirty_preflight": (
            dict(baseline_dirty_preflight)
            if baseline_dirty_preflight is not None
            else None
        ),
        "semantic_function_call_resolution_count": 0,
        "semantic_function_call_resolution_status_counts": {},
    }


def _baseline_context_missing_operation_execution_detail(
    *,
    request: object,
    baseline_dirty_preflight: Mapping[str, object],
    provider_delta_execute_flag_preflight: Mapping[str, object] | None = None,
) -> dict[str, object]:
    active_execution_rail = (
        _mapping_value(
            provider_delta_execute_flag_preflight.get(
                "provider_delta_active_execution_rail"
            )
        )
        if provider_delta_execute_flag_preflight is not None
        else {}
    )
    return {
        "execution_kind": "meta_ocg_provider_delta_operation_execution",
        "required_flag": _DELTA_OPERATION_EXECUTION_FLAG,
        "flag_requested": _operation_execution_requested(request=request),
        "operation_count": 0,
        "semantic_function_call_plan_count": 0,
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "receipt_persistence_contract_ready": False,
        "status": "baseline_context_missing",
        "reason": (
            "meta_ocg_provider_delta_operation_execution_requires_commit_backed_baseline"
        ),
        "execution_wired": False,
        "execute_flag_preflight_status": (
            _optional_text(provider_delta_execute_flag_preflight.get("status"))
            if provider_delta_execute_flag_preflight is not None
            else None
        ),
        "active_execution_rail": _optional_text(
            active_execution_rail.get("active_execution_rail")
        ),
        "active_execution_status": _optional_text(active_execution_rail.get("status")),
        "active_execution_reason": _optional_text(active_execution_rail.get("reason")),
        "provider_delta_active_execution_rail": active_execution_rail,
        "execute_flag_preflight": (
            dict(provider_delta_execute_flag_preflight)
            if provider_delta_execute_flag_preflight is not None
            else None
        ),
        "baseline_dirty_preflight": dict(baseline_dirty_preflight),
        "semantic_function_call_resolution_count": 0,
        "semantic_function_call_resolution_status_counts": {},
    }


def _operation_execution_requested(*, request: object) -> bool:
    return (
        getattr(request, _DELTA_OPERATION_EXECUTION_FLAG, False) is True
        or getattr(request, "enable_provider_delta_operation_execution", False) is True
        or getattr(request, "provider_delta_operation_execution_enabled", False) is True
    )


def _mapping_tuple_text(value: object) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): _tuple_text(item) for key, item in value.items() if _tuple_text(item)
    }


__all__ = [
    "_baseline_context_missing_operation_execution_detail",
    "_operation_execution_detail",
    "_operation_execution_requested",
    "_provider_delta_execute_flag_preflight",
    "_provider_delta_execution_context_preflight",
    "_provider_delta_head_move_applied_receipt",
    "_provider_delta_oig_commit_receipt",
    "_provider_delta_shared_execution_inputs_available",
]
