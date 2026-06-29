from __future__ import annotations

from collections.abc import Mapping

from aware_code.semantic_materialization import (
    build_semantic_provider_delta_head_move_plan,
)
from aware_meta.materialization.deltas.baseline import (
    _baseline_ref_payload,
    _int_payload_value,
    _mapping_value,
    _model_payload,
    _optional_text,
)


def _operation_plan_with_provider_delta_head_move_plan(
    *,
    operation_plan: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
) -> dict[str, object]:
    return {
        **dict(operation_plan),
        "provider_delta_head_move_status": _string_value(
            provider_delta_head_move_plan.get("status")
        ),
        "provider_delta_head_move_reason": _string_value(
            provider_delta_head_move_plan.get("reason")
        ),
        "provider_delta_head_move_planned_operation_count": _int_payload_value(
            provider_delta_head_move_plan,
            "planned_operation_count",
        ),
        "provider_delta_head_move_plan": dict(provider_delta_head_move_plan),
    }


def _provider_delta_head_move_plan(
    *,
    request: object,
    semantic_dirty_diff: Mapping[str, object],
    head_refs: Mapping[str, object] | None = None,
) -> dict[str, object]:
    plan = build_semantic_provider_delta_head_move_plan(
        request=_provider_delta_head_move_request_payload(request=request),
        semantic_dirty_diff=semantic_dirty_diff,
        head_refs=head_refs,
    )
    return dict(plan.model_dump(mode="json"))


def _provider_delta_head_move_request_payload(
    *,
    request: object,
) -> dict[str, object]:
    previous_evidence = getattr(request, "previous_materialization_evidence", None)
    return {
        "package": _model_payload(getattr(request, "package", None)),
        "semantic_contract": _model_payload(
            getattr(request, "semantic_contract", None)
        ),
        "current_delta_fingerprint": _string_value(
            getattr(request, "current_delta_fingerprint", None)
        ),
        "delta_cause_hints": _model_payload(
            getattr(request, "delta_cause_hints", None)
        ),
        "previous_materialization_evidence": (
            _mapping_value(previous_evidence)
            if isinstance(previous_evidence, Mapping)
            else _model_payload(previous_evidence)
        ),
        "baseline_ref": _baseline_ref_payload(request=request),
        "baseline_source_object_instance_graph_commit_id": _optional_text(
            getattr(request, "baseline_source_object_instance_graph_commit_id", None)
        ),
        "baseline_semantic_object_instance_graph_commit_id": _optional_text(
            getattr(request, "baseline_semantic_object_instance_graph_commit_id", None)
        ),
        "baseline_semantic_root_object_instance_graph_commit_id": _optional_text(
            getattr(
                request,
                "baseline_semantic_root_object_instance_graph_commit_id",
                None,
            )
        ),
    }


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "_operation_plan_with_provider_delta_head_move_plan",
    "_provider_delta_head_move_plan",
    "_provider_delta_head_move_request_payload",
]
