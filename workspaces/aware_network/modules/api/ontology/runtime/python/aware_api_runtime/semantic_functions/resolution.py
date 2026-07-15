from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from aware_api_runtime.semantic_function_refs import (
    API_CREATE_FUNCTION_REF,
    API_SEMANTIC_FUNCTION_REFS,
)
from aware_code.semantic_capability import SemanticCapabilityFunctionCallPlan


ApiSemanticFunctionCallResolutionStatus = Literal[
    "create_root",
    "create_child",
    "noop_existing",
    "needs_ref_resolution",
    "unresolved_receiver",
    "unresolved_argument_ref",
    "unsupported_function",
]


@dataclass(frozen=True, slots=True)
class ApiSemanticFunctionCallResolution:
    plan: SemanticCapabilityFunctionCallPlan
    status: ApiSemanticFunctionCallResolutionStatus
    receiver_source: str | None = None
    receiver_semantic_key: str | None = None
    receiver_object_id: str | None = None
    result_semantic_key: str | None = None
    result_object_id: str | None = None
    resolved_argument_refs: Mapping[str, str] = field(default_factory=dict)
    unresolved_argument_refs: Mapping[str, str] = field(default_factory=dict)
    dependencies: tuple[str, ...] = ()
    reason: str | None = None

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": self.status,
            "function_ref": self.plan.function_ref,
            "arguments": dict(self.plan.arguments),
            "argument_refs": dict(self.plan.argument_refs),
            "resolved_argument_refs": dict(self.resolved_argument_refs),
            "unresolved_argument_refs": dict(self.unresolved_argument_refs),
            "dependencies": self.dependencies,
        }
        if self.plan.binding_key is not None:
            payload["binding_key"] = self.plan.binding_key
        if self.plan.action_key is not None:
            payload["action_key"] = self.plan.action_key
        if self.plan.event_key is not None:
            payload["event_key"] = self.plan.event_key
        if self.receiver_source is not None:
            payload["receiver_source"] = self.receiver_source
        if self.receiver_semantic_key is not None:
            payload["receiver_semantic_key"] = self.receiver_semantic_key
        if self.receiver_object_id is not None:
            payload["receiver_object_id"] = self.receiver_object_id
        if self.result_semantic_key is not None:
            payload["result_semantic_key"] = self.result_semantic_key
        if self.result_object_id is not None:
            payload["result_object_id"] = self.result_object_id
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


def resolve_api_semantic_function_call_plan_previews(
    *,
    plans: tuple[SemanticCapabilityFunctionCallPlan, ...],
    current_semantic_object_ids: Mapping[str, object] | None = None,
    resolved_argument_ref_object_ids: Mapping[str, object] | None = None,
) -> tuple[ApiSemanticFunctionCallResolution, ...]:
    current_objects = _normalize_object_id_map(current_semantic_object_ids)
    resolved_refs = _normalize_object_id_map(resolved_argument_ref_object_ids)
    planned_result_keys: set[str] = set()
    resolutions: list[ApiSemanticFunctionCallResolution] = []
    for plan in plans:
        resolution = _resolve_plan(
            plan=plan,
            current_objects=current_objects,
            planned_result_keys=frozenset(planned_result_keys),
            resolved_refs=resolved_refs,
        )
        resolutions.append(resolution)
        if _contributes_planned_result(resolution):
            planned_result_keys.add(str(resolution.result_semantic_key))
    return tuple(resolutions)


def _resolve_plan(
    *,
    plan: SemanticCapabilityFunctionCallPlan,
    current_objects: Mapping[str, str],
    planned_result_keys: frozenset[str],
    resolved_refs: Mapping[str, str],
) -> ApiSemanticFunctionCallResolution:
    result_key = _clean_optional(plan.result_semantic_key)
    if plan.function_ref not in API_SEMANTIC_FUNCTION_REFS:
        return ApiSemanticFunctionCallResolution(
            plan=plan,
            status="unsupported_function",
            result_semantic_key=result_key,
            reason=f"Unsupported API semantic function ref: {plan.function_ref}",
        )
    if result_key is not None and result_key in current_objects:
        return ApiSemanticFunctionCallResolution(
            plan=plan,
            status="noop_existing",
            result_semantic_key=result_key,
            result_object_id=current_objects[result_key],
            reason="Semantic result already exists in current API head.",
        )
    receiver = _resolve_receiver(
        receiver_semantic_key=plan.receiver_semantic_key,
        current_objects=current_objects,
        planned_result_keys=planned_result_keys,
    )
    if plan.function_ref != API_CREATE_FUNCTION_REF and receiver.status == "unresolved":
        return ApiSemanticFunctionCallResolution(
            plan=plan,
            status="unresolved_receiver",
            receiver_semantic_key=receiver.semantic_key,
            result_semantic_key=result_key,
            reason="Receiver semantic key is neither current nor planned in batch.",
        )
    argument_refs = _resolve_argument_refs(
        argument_refs=plan.argument_refs,
        resolved_refs=resolved_refs,
    )
    if argument_refs.has_missing_ref:
        return ApiSemanticFunctionCallResolution(
            plan=plan,
            status="unresolved_argument_ref",
            receiver_source=receiver.source,
            receiver_semantic_key=receiver.semantic_key,
            receiver_object_id=receiver.object_id,
            result_semantic_key=result_key,
            resolved_argument_refs=argument_refs.resolved,
            unresolved_argument_refs=argument_refs.unresolved,
            dependencies=receiver.dependencies,
            reason="Function-call plan contains an empty argument ref.",
        )
    if argument_refs.unresolved:
        return ApiSemanticFunctionCallResolution(
            plan=plan,
            status="needs_ref_resolution",
            receiver_source=receiver.source,
            receiver_semantic_key=receiver.semantic_key,
            receiver_object_id=receiver.object_id,
            result_semantic_key=result_key,
            resolved_argument_refs=argument_refs.resolved,
            unresolved_argument_refs=argument_refs.unresolved,
            dependencies=receiver.dependencies,
            reason="Semantic argument refs must be hydrated before execution.",
        )
    if plan.function_ref == API_CREATE_FUNCTION_REF:
        status: ApiSemanticFunctionCallResolutionStatus = "create_root"
    else:
        status = "create_child"
    return ApiSemanticFunctionCallResolution(
        plan=plan,
        status=status,
        receiver_source=receiver.source,
        receiver_semantic_key=receiver.semantic_key,
        receiver_object_id=receiver.object_id,
        result_semantic_key=result_key,
        resolved_argument_refs=argument_refs.resolved,
        dependencies=receiver.dependencies,
    )


@dataclass(frozen=True, slots=True)
class _ReceiverResolution:
    status: Literal["root", "current", "planned", "unresolved"]
    source: str | None = None
    semantic_key: str | None = None
    object_id: str | None = None
    dependencies: tuple[str, ...] = ()


def _resolve_receiver(
    *,
    receiver_semantic_key: str | None,
    current_objects: Mapping[str, str],
    planned_result_keys: frozenset[str],
) -> _ReceiverResolution:
    receiver_key = _clean_optional(receiver_semantic_key)
    if receiver_key is None:
        return _ReceiverResolution(status="root", source="root")
    if receiver_key in current_objects:
        return _ReceiverResolution(
            status="current",
            source="current",
            semantic_key=receiver_key,
            object_id=current_objects[receiver_key],
        )
    if receiver_key in planned_result_keys:
        return _ReceiverResolution(
            status="planned",
            source="planned",
            semantic_key=receiver_key,
            dependencies=(receiver_key,),
        )
    return _ReceiverResolution(
        status="unresolved",
        semantic_key=receiver_key,
    )


@dataclass(frozen=True, slots=True)
class _ArgumentRefResolution:
    resolved: Mapping[str, str]
    unresolved: Mapping[str, str]
    has_missing_ref: bool = False


def _resolve_argument_refs(
    *,
    argument_refs: Mapping[str, str],
    resolved_refs: Mapping[str, str],
) -> _ArgumentRefResolution:
    resolved: dict[str, str] = {}
    unresolved: dict[str, str] = {}
    has_missing_ref = False
    for argument_name, semantic_ref in sorted(argument_refs.items()):
        cleaned_ref = _clean_optional(semantic_ref)
        if cleaned_ref is None:
            has_missing_ref = True
            unresolved[argument_name] = semantic_ref
            continue
        if cleaned_ref in resolved_refs:
            resolved[argument_name] = resolved_refs[cleaned_ref]
            continue
        unresolved[argument_name] = cleaned_ref
    return _ArgumentRefResolution(
        resolved=resolved,
        unresolved=unresolved,
        has_missing_ref=has_missing_ref,
    )


def _contributes_planned_result(
    resolution: ApiSemanticFunctionCallResolution,
) -> bool:
    return resolution.result_semantic_key is not None and resolution.status in {
        "create_root",
        "create_child",
        "needs_ref_resolution",
    }


def _normalize_object_id_map(
    values: Mapping[str, object] | None,
) -> dict[str, str]:
    if values is None:
        return {}
    return {
        str(key).strip(): str(value).strip()
        for key, value in values.items()
        if str(key).strip() and str(value).strip()
    }


def _clean_optional(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "ApiSemanticFunctionCallResolution",
    "ApiSemanticFunctionCallResolutionStatus",
    "resolve_api_semantic_function_call_plan_previews",
]
