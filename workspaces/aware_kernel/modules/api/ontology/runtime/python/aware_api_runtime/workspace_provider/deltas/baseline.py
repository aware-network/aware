from __future__ import annotations

from collections.abc import Mapping

from aware_code.semantic_function_call_execution import (
    SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY,
)
from aware_code.semantic_materialization import (
    SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY,
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    SemanticFunctionCallContext,
    SemanticProviderDeltaDurableExecutionInputs,
)
from aware_api_runtime.semantic_functions.execution import (
    API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY,
)


API_BASELINE_HYDRATION_PREFLIGHT_CONTRACT_VERSION = (
    "aware.api.provider-delta.baseline-hydration-preflight.v1"
)
API_BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION = (
    "aware.api.provider-delta.baseline-semantic-object-index.v1"
)
API_DURABLE_EXECUTION_INPUTS_PREFLIGHT_CONTRACT_VERSION = (
    "aware.api.provider-delta-durable-execution-inputs-preflight.v1"
)
API_BASELINE_COMMIT_REF_FIELDS = (
    "baseline_source_object_instance_graph_commit_id",
    "baseline_semantic_object_instance_graph_commit_id",
    "baseline_semantic_root_object_instance_graph_commit_id",
)
API_BASELINE_REF_HYDRATOR_REQUIRED_FIELDS = (
    "source_object_instance_graph_commit_id",
    "semantic_branch_id",
    "semantic_projection_name",
    "semantic_package_id",
    "semantic_object_instance_graph_commit_id",
    "semantic_root_kind",
    "semantic_root_id",
    "semantic_root_object_instance_graph_commit_id",
)
API_PROVIDER_KEY = "aware_api"


def api_delta_baseline_hydration_preflight(
    *,
    request: object,
) -> dict[str, object]:
    baseline_refs = api_delta_baseline_commit_refs(request=request)
    baseline_ref = api_delta_baseline_ref_payload(request=request)
    missing_fields = tuple(
        field_name
        for field_name in API_BASELINE_COMMIT_REF_FIELDS
        if not baseline_refs.get(field_name)
    )
    missing_baseline_ref_fields = api_delta_baseline_ref_missing_required_fields(
        baseline_ref=baseline_ref,
    )
    context = api_delta_operation_execution_context(request=request)
    function_call_context = SemanticFunctionCallContext.from_materialization_context(
        context,
        provider_key=API_PROVIDER_KEY,
    )
    current_object_count = len(function_call_context.current_semantic_object_ids)
    current_head_context_sources = api_delta_current_head_context_sources(
        request=request,
    )
    resolved_argument_ref_count = len(
        function_call_context.resolved_argument_ref_object_ids
    )
    durable_execution_inputs_preflight = api_delta_durable_execution_inputs_preflight(
        request=request
    )
    commit_backed_baseline_available = not missing_fields
    baseline_ref_hydrator_ready = (
        baseline_ref is not None and not missing_baseline_ref_fields
    )
    current_head_context_available = current_object_count > 0
    status = api_delta_baseline_hydration_status(
        commit_backed_baseline_available=commit_backed_baseline_available,
        baseline_ref_available=baseline_ref is not None,
        baseline_ref_hydrator_ready=baseline_ref_hydrator_ready,
        current_head_context_available=current_head_context_available,
    )
    return {
        "preflight_kind": "api_provider_delta_baseline_hydration_preflight",
        "contract_version": API_BASELINE_HYDRATION_PREFLIGHT_CONTRACT_VERSION,
        "status": status,
        "reason": api_delta_baseline_hydration_reason(status=status),
        "source": "workspace.provider_delta_request",
        "baseline_identity_source": "workspace.baseline_ref",
        "commit_backed_baseline_available": commit_backed_baseline_available,
        "baseline_ref_available": baseline_ref is not None,
        "baseline_ref_hydrator_ready": baseline_ref_hydrator_ready,
        "current_head_context_available": current_head_context_available,
        "current_head_context_sources": current_head_context_sources,
        "current_semantic_object_id_count": current_object_count,
        "resolved_argument_ref_object_id_count": resolved_argument_ref_count,
        "durable_execution_inputs_preflight": durable_execution_inputs_preflight,
        "durable_execution_inputs_status": (
            durable_execution_inputs_preflight["status"]
        ),
        "shared_execution_inputs_contract_available": (
            durable_execution_inputs_preflight[
                "shared_execution_inputs_contract_available"
            ]
        ),
        "would_persist": False,
        "did_persist": False,
        "did_hydrate": current_head_context_available,
        "required_fields": API_BASELINE_COMMIT_REF_FIELDS,
        "missing_required_fields": missing_fields,
        "baseline_commit_refs": baseline_refs,
        "baseline_ref_required_fields": API_BASELINE_REF_HYDRATOR_REQUIRED_FIELDS,
        "baseline_ref_missing_required_fields": missing_baseline_ref_fields,
        "baseline_ref": baseline_ref,
    }


def api_delta_baseline_hydration_status(
    *,
    commit_backed_baseline_available: bool,
    baseline_ref_available: bool,
    baseline_ref_hydrator_ready: bool,
    current_head_context_available: bool,
) -> str:
    if current_head_context_available:
        return "current_head_context_available"
    if not commit_backed_baseline_available:
        return "baseline_context_missing"
    if not baseline_ref_available:
        return "baseline_ref_missing"
    if not baseline_ref_hydrator_ready:
        return "baseline_ref_incomplete"
    return "current_head_context_missing"


def api_delta_baseline_hydration_reason(*, status: str) -> str:
    reasons = {
        "baseline_context_missing": (
            "api_provider_delta_baseline_hydration_requires_commit_backed_baseline"
        ),
        "baseline_ref_incomplete": (
            "api_provider_delta_baseline_ref_missing_required_hydration_fields"
        ),
        "baseline_ref_missing": (
            "api_provider_delta_baseline_hydration_requires_workspace_baseline_ref"
        ),
        "current_head_context_available": (
            "api_provider_delta_baseline_current_head_context_available"
        ),
        "current_head_context_missing": (
            "api_provider_delta_baseline_current_head_context_not_hydrated"
        ),
    }
    return reasons.get(
        status,
        "api_provider_delta_baseline_hydration_status_unknown",
    )


def api_delta_baseline_commit_refs(*, request: object) -> dict[str, object]:
    baseline_ref = api_delta_baseline_ref_payload(request=request)
    return {
        "baseline_source_object_instance_graph_commit_id": (
            _optional_text(
                getattr(
                    request, "baseline_source_object_instance_graph_commit_id", None
                )
            )
            or (
                _optional_text(
                    baseline_ref.get("source_object_instance_graph_commit_id")
                )
                if baseline_ref is not None
                else None
            )
        ),
        "baseline_semantic_object_instance_graph_commit_id": (
            _optional_text(
                getattr(
                    request,
                    "baseline_semantic_object_instance_graph_commit_id",
                    None,
                )
            )
            or (
                _optional_text(
                    baseline_ref.get("semantic_object_instance_graph_commit_id")
                )
                if baseline_ref is not None
                else None
            )
        ),
        "baseline_semantic_root_object_instance_graph_commit_id": (
            _optional_text(
                getattr(
                    request,
                    "baseline_semantic_root_object_instance_graph_commit_id",
                    None,
                )
            )
            or (
                _optional_text(
                    baseline_ref.get("semantic_root_object_instance_graph_commit_id")
                )
                if baseline_ref is not None
                else None
            )
        ),
    }


def api_delta_baseline_ref_payload(
    *,
    request: object,
) -> dict[str, object] | None:
    raw_ref = getattr(request, "baseline_ref", None)
    if raw_ref is None:
        evidence = getattr(request, "previous_materialization_evidence", None)
        if isinstance(evidence, Mapping):
            raw_ref = evidence.get("baseline_ref")
    payload = _model_payload(raw_ref)
    return payload or None


def api_delta_baseline_ref_missing_required_fields(
    *,
    baseline_ref: Mapping[str, object] | None,
) -> tuple[str, ...]:
    if baseline_ref is None:
        return API_BASELINE_REF_HYDRATOR_REQUIRED_FIELDS
    return tuple(
        field_name
        for field_name in API_BASELINE_REF_HYDRATOR_REQUIRED_FIELDS
        if _optional_text(baseline_ref.get(field_name)) is None
    )


def api_delta_current_semantic_object_ids(*, request: object) -> dict[str, str]:
    context = api_delta_operation_execution_context(request=request)
    return api_delta_context_current_semantic_object_ids(context=context)


def api_delta_context_current_semantic_object_ids(
    *,
    context: Mapping[str, object],
) -> dict[str, str]:
    function_call_context = SemanticFunctionCallContext.from_materialization_context(
        context,
        provider_key=API_PROVIDER_KEY,
    )
    return {
        semantic_key: object_id
        for semantic_key, object_id in (
            (
                _optional_text(raw_key),
                _optional_text(raw_value),
            )
            for raw_key, raw_value in (
                function_call_context.current_semantic_object_ids.items()
            )
        )
        if semantic_key is not None and object_id is not None
    }


def api_delta_current_head_context_sources(*, request: object) -> tuple[str, ...]:
    sources: list[str] = []
    if api_delta_previous_materialization_current_semantic_object_ids(
        request=request,
    ):
        sources.append("previous_materialization_evidence")
    raw_context = api_delta_raw_operation_execution_context(request=request)
    if api_delta_context_current_semantic_object_ids(context=raw_context):
        sources.append("semantic_function_call_context")
    return tuple(sources)


def api_delta_previous_materialization_current_semantic_object_ids(
    *,
    request: object,
) -> dict[str, str]:
    evidence = api_delta_request_value(
        request=request,
        key="previous_materialization_evidence",
    )
    if not isinstance(evidence, Mapping):
        return {}
    current_objects = evidence.get("current_semantic_object_ids")
    if not isinstance(current_objects, Mapping):
        return {}
    return api_delta_string_map(current_objects)


def api_delta_previous_evidence_current_object_count(
    *,
    evidence: Mapping[str, object],
) -> int:
    raw_count = evidence.get("current_semantic_object_id_count")
    if isinstance(raw_count, int):
        return max(raw_count, 0)
    current_objects = evidence.get("current_semantic_object_ids")
    if isinstance(current_objects, Mapping):
        return len(current_objects)
    return 0


def api_delta_operation_execution_context(
    *,
    request: object,
) -> Mapping[str, object]:
    raw_context = api_delta_raw_operation_execution_context(request=request)
    context: dict[str, object] = (
        dict(raw_context) if isinstance(raw_context, Mapping) else {}
    )
    _api_delta_merge_previous_materialization_context(
        context=context,
        request=request,
    )
    durable_execution_inputs = api_delta_request_value(
        request=request,
        key=SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    )
    if durable_execution_inputs is not None:
        context.setdefault(
            SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
            durable_execution_inputs,
        )
    raw_config = context.get(SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY)
    if isinstance(raw_config, Mapping):
        config_payload = dict(raw_config)
        config_payload["enabled"] = True
    else:
        config_payload = {"enabled": True}
    context[SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY] = config_payload
    return context


def api_delta_raw_operation_execution_context(
    *,
    request: object,
) -> Mapping[str, object]:
    raw_context = getattr(request, "semantic_function_call_execution_context", None)
    if not isinstance(raw_context, Mapping):
        raw_context = getattr(request, "context", None)
    return raw_context if isinstance(raw_context, Mapping) else {}


def api_delta_durable_execution_inputs_preflight(
    *,
    request: object,
) -> dict[str, object]:
    payload = api_delta_durable_execution_inputs_payload(request=request)
    provider_inputs = _model_payload(payload.get("provider_inputs"))
    if not payload:
        status = "durable_execution_inputs_unavailable"
        missing_common_fields: tuple[str, ...] = ()
        normalized_payload: Mapping[str, object] = {}
    else:
        normalized = SemanticProviderDeltaDurableExecutionInputs.model_validate(payload)
        normalized_payload = normalized.model_dump(mode="python")
        missing_common_fields = normalized.missing_common_fields()
        status = (
            "durable_execution_inputs_ready"
            if not missing_common_fields
            else "durable_execution_inputs_partial"
        )
    return {
        "preflight_kind": "api_provider_delta_durable_execution_inputs_preflight",
        "contract_version": API_DURABLE_EXECUTION_INPUTS_PREFLIGHT_CONTRACT_VERSION,
        "status": status,
        "reason": api_delta_durable_execution_inputs_reason(status=status),
        "available": bool(payload),
        "blocked": False,
        "shared_execution_inputs_key": (
            SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY
        ),
        "shared_execution_inputs_contract_available": bool(payload),
        "shared_execution_inputs_contract_version": _optional_text(
            normalized_payload.get("contract_version")
        ),
        "common_inputs_available": status == "durable_execution_inputs_ready",
        "missing_common_fields": missing_common_fields,
        "provider_input_keys": tuple(sorted(str(key) for key in provider_inputs)),
        "api_execution_backend_provider_input_available": (
            API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY in provider_inputs
        ),
        "provider_key": _optional_text(normalized_payload.get("provider_key")),
        "semantic_owner": _optional_text(normalized_payload.get("semantic_owner")),
        "semantic_branch_id": _optional_text(
            normalized_payload.get("semantic_branch_id")
        ),
        "semantic_projection_hash": _optional_text(
            normalized_payload.get("semantic_projection_hash")
        ),
        "semantic_projection_name": _optional_text(
            normalized_payload.get("semantic_projection_name")
        ),
        "author_id": _optional_text(normalized_payload.get("author_id")),
        "would_execute": False,
        "would_persist": False,
        "did_execute": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }


def api_delta_durable_execution_inputs_reason(*, status: str) -> str:
    return {
        "durable_execution_inputs_ready": (
            "api_provider_delta_durable_execution_inputs_ready"
        ),
        "durable_execution_inputs_partial": (
            "api_provider_delta_durable_execution_inputs_partial"
        ),
        "durable_execution_inputs_unavailable": (
            "api_provider_delta_durable_execution_inputs_unavailable"
        ),
    }.get(status, "api_provider_delta_durable_execution_inputs_status_unknown")


def api_delta_durable_execution_inputs_payload(
    *,
    request: object,
) -> dict[str, object]:
    value = api_delta_request_value(
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


def api_delta_request_value(*, request: object, key: str) -> object | None:
    if isinstance(request, Mapping):
        value = request.get(key)
        if value is not None:
            return value
    value = getattr(request, key, None)
    if value is not None:
        return value
    for context_name in ("semantic_function_call_execution_context", "context"):
        context = getattr(request, context_name, None)
        if isinstance(context, Mapping):
            value = context.get(key)
            if value is not None:
                return value
    return None


def api_delta_string_map(value: Mapping[object, object]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for raw_key, raw_value in value.items():
        key = _optional_text(raw_key)
        item = _optional_text(raw_value)
        if key is not None and item is not None:
            normalized[key] = item
    return normalized


def _api_delta_merge_previous_materialization_context(
    *,
    context: dict[str, object],
    request: object,
) -> None:
    previous_object_ids = (
        api_delta_previous_materialization_current_semantic_object_ids(
            request=request,
        )
    )
    if not previous_object_ids:
        return
    previous_context = SemanticFunctionCallContext(
        current_semantic_object_ids=previous_object_ids,
    )
    explicit_context = SemanticFunctionCallContext.from_materialization_context(
        context,
        provider_key=API_PROVIDER_KEY,
    )
    merged_context = previous_context.merge(explicit_context)
    provider_contexts = _model_payload(
        context.get(SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY)
    )
    provider_contexts[API_PROVIDER_KEY] = merged_context.evidence_payload()
    context[SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY] = provider_contexts


def _model_payload(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="json")
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    if hasattr(value, "__dict__"):
        return {str(key): item for key, item in vars(value).items()}
    return {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "API_BASELINE_COMMIT_REF_FIELDS",
    "API_BASELINE_HYDRATION_PREFLIGHT_CONTRACT_VERSION",
    "API_BASELINE_REF_HYDRATOR_REQUIRED_FIELDS",
    "API_BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION",
    "API_DURABLE_EXECUTION_INPUTS_PREFLIGHT_CONTRACT_VERSION",
    "api_delta_baseline_commit_refs",
    "api_delta_baseline_hydration_preflight",
    "api_delta_baseline_hydration_reason",
    "api_delta_baseline_hydration_status",
    "api_delta_baseline_ref_missing_required_fields",
    "api_delta_baseline_ref_payload",
    "api_delta_context_current_semantic_object_ids",
    "api_delta_current_head_context_sources",
    "api_delta_current_semantic_object_ids",
    "api_delta_durable_execution_inputs_payload",
    "api_delta_durable_execution_inputs_preflight",
    "api_delta_durable_execution_inputs_reason",
    "api_delta_operation_execution_context",
    "api_delta_previous_evidence_current_object_count",
    "api_delta_previous_materialization_current_semantic_object_ids",
    "api_delta_raw_operation_execution_context",
    "api_delta_request_value",
    "api_delta_string_map",
]
