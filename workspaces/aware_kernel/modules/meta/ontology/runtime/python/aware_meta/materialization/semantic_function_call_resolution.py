from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from aware_code.semantic_capability import SemanticCapabilityFunctionCallPlan
from aware_meta.materialization.function_refs import meta_ontology_function_ref
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_package import (
    ObjectConfigGraphPackage,
)


META_OCG_PACKAGE_BUILD_FUNCTION = meta_ontology_function_ref(
    ObjectConfigGraphPackage.build
)
META_OCG_PACKAGE_ATTACH_GRAPH_FUNCTION = meta_ontology_function_ref(
    ObjectConfigGraphPackage.attach_object_config_graph
)
META_OCG_BUILD_FUNCTION = meta_ontology_function_ref(ObjectConfigGraph.build)
META_OCG_CREATE_NODE_FUNCTION = meta_ontology_function_ref(
    ObjectConfigGraph.create_node
)
META_OCG_DELETE_NODE_FUNCTION_REF = (
    "aware_meta_ontology.graph.config.object_config_graph."
    "ObjectConfigGraph.delete_node"
)
META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION = meta_ontology_function_ref(
    ClassConfig.create_primitive_attribute_config
)
META_CLASS_CONFIG_CREATE_ENUM_ATTRIBUTE_FUNCTION = meta_ontology_function_ref(
    ClassConfig.create_enum_attribute_config
)
META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION = meta_ontology_function_ref(
    ClassConfig.create_class_attribute_config
)
META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION = meta_ontology_function_ref(
    FunctionConfig.add_primitive_attribute_config
)
META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION = meta_ontology_function_ref(
    FunctionConfig.add_enum_attribute_config
)
META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION = meta_ontology_function_ref(
    FunctionConfig.add_class_attribute_config
)

META_OCG_PACKAGE_BUILD_FUNCTION_REF = META_OCG_PACKAGE_BUILD_FUNCTION.ref
META_OCG_PACKAGE_ATTACH_GRAPH_FUNCTION_REF = (
    META_OCG_PACKAGE_ATTACH_GRAPH_FUNCTION.ref
)
META_OCG_BUILD_FUNCTION_REF = META_OCG_BUILD_FUNCTION.ref
META_OCG_CREATE_NODE_FUNCTION_REF = META_OCG_CREATE_NODE_FUNCTION.ref
META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION_REF = (
    META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION.ref
)
META_CLASS_CONFIG_CREATE_ENUM_ATTRIBUTE_FUNCTION_REF = (
    META_CLASS_CONFIG_CREATE_ENUM_ATTRIBUTE_FUNCTION.ref
)
META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION_REF = (
    META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION.ref
)
META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF = (
    META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION.ref
)
META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION_REF = (
    META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION.ref
)
META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION_REF = (
    META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION.ref
)

META_SEMANTIC_FUNCTION_REFS = frozenset(
    {
        META_OCG_PACKAGE_BUILD_FUNCTION_REF,
        META_OCG_PACKAGE_ATTACH_GRAPH_FUNCTION_REF,
        META_OCG_BUILD_FUNCTION_REF,
        META_OCG_CREATE_NODE_FUNCTION_REF,
        META_OCG_DELETE_NODE_FUNCTION_REF,
        META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
        META_CLASS_CONFIG_CREATE_ENUM_ATTRIBUTE_FUNCTION_REF,
        META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION_REF,
        META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
        META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION_REF,
        META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION_REF,
    }
)

MetaSemanticFunctionCallResolutionStatus = Literal[
    "create_root",
    "create_child",
    "noop_existing",
    "unresolved_receiver",
    "unsupported_function",
    "invalid_runtime_graph_scope",
]


@dataclass(frozen=True, slots=True)
class MetaSemanticFunctionCallResolution:
    plan: SemanticCapabilityFunctionCallPlan
    status: MetaSemanticFunctionCallResolutionStatus
    receiver_source: str | None = None
    receiver_semantic_key: str | None = None
    receiver_object_id: str | None = None
    result_semantic_key: str | None = None
    result_object_id: str | None = None
    dependencies: tuple[str, ...] = ()
    reason: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": self.status,
            "function_ref": self.plan.function_ref,
            "arguments": dict(self.plan.arguments),
            "argument_refs": dict(self.plan.argument_refs),
            "dependencies": self.dependencies,
            "metadata": dict(self.metadata),
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


def resolve_meta_semantic_function_call_plan_previews(
    *,
    plans: tuple[SemanticCapabilityFunctionCallPlan, ...],
    current_semantic_object_ids: Mapping[str, object] | None = None,
) -> tuple[MetaSemanticFunctionCallResolution, ...]:
    current_objects = _normalize_object_id_map(current_semantic_object_ids)
    planned_result_keys: set[str] = set()
    resolutions: list[MetaSemanticFunctionCallResolution] = []
    for plan in plans:
        resolution = _resolve_plan(
            plan=plan,
            current_objects=current_objects,
            planned_result_keys=frozenset(planned_result_keys),
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
) -> MetaSemanticFunctionCallResolution:
    metadata = dict(plan.metadata)
    result_key = _clean_optional(plan.result_semantic_key)
    if metadata.get("semantic_truth_graph") != "runtime_ocg":
        return MetaSemanticFunctionCallResolution(
            plan=plan,
            status="invalid_runtime_graph_scope",
            result_semantic_key=result_key,
            metadata=metadata,
            reason="Meta semantic materialization plans must target runtime OCG truth.",
        )
    if plan.function_ref not in META_SEMANTIC_FUNCTION_REFS:
        return MetaSemanticFunctionCallResolution(
            plan=plan,
            status="unsupported_function",
            result_semantic_key=result_key,
            metadata=metadata,
            reason=f"Unsupported Meta semantic function ref: {plan.function_ref}",
        )
    if result_key is not None and result_key in current_objects:
        return MetaSemanticFunctionCallResolution(
            plan=plan,
            status="noop_existing",
            result_semantic_key=result_key,
            result_object_id=current_objects[result_key],
            metadata=metadata,
            reason="Semantic result already exists in current Meta OCG head.",
        )

    receiver = _resolve_receiver(
        receiver_semantic_key=plan.receiver_semantic_key,
        current_objects=current_objects,
        planned_result_keys=planned_result_keys,
    )
    if _requires_receiver(plan.function_ref) and receiver.status == "unresolved":
        return MetaSemanticFunctionCallResolution(
            plan=plan,
            status="unresolved_receiver",
            receiver_semantic_key=receiver.semantic_key,
            result_semantic_key=result_key,
            metadata=metadata,
            reason="Receiver semantic key is neither current nor planned in batch.",
        )
    status: MetaSemanticFunctionCallResolutionStatus = (
        "create_child" if _requires_receiver(plan.function_ref) else "create_root"
    )
    return MetaSemanticFunctionCallResolution(
        plan=plan,
        status=status,
        receiver_source=receiver.source,
        receiver_semantic_key=receiver.semantic_key,
        receiver_object_id=receiver.object_id,
        result_semantic_key=result_key,
        dependencies=receiver.dependencies,
        metadata=metadata,
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
    return _ReceiverResolution(status="unresolved", semantic_key=receiver_key)


def _requires_receiver(function_ref: str) -> bool:
    return function_ref in {
        META_OCG_PACKAGE_ATTACH_GRAPH_FUNCTION_REF,
        META_OCG_CREATE_NODE_FUNCTION_REF,
        META_OCG_DELETE_NODE_FUNCTION_REF,
        META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
        META_CLASS_CONFIG_CREATE_ENUM_ATTRIBUTE_FUNCTION_REF,
        META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION_REF,
        META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
        META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION_REF,
        META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION_REF,
    }


def _contributes_planned_result(resolution: MetaSemanticFunctionCallResolution) -> bool:
    return resolution.status in {"create_root", "create_child"} and bool(
        resolution.result_semantic_key
    )


def _normalize_object_id_map(value: Mapping[str, object] | None) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, str] = {}
    for key, item in value.items():
        normalized_key = str(key).strip()
        normalized_value = str(item).strip()
        if normalized_key and normalized_value:
            normalized[normalized_key] = normalized_value
    return normalized


def _clean_optional(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION",
    "META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION_REF",
    "META_CLASS_CONFIG_CREATE_ENUM_ATTRIBUTE_FUNCTION",
    "META_CLASS_CONFIG_CREATE_ENUM_ATTRIBUTE_FUNCTION_REF",
    "META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION",
    "META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION_REF",
    "META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION",
    "META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION_REF",
    "META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION",
    "META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION_REF",
    "META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION",
    "META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF",
    "META_OCG_BUILD_FUNCTION",
    "META_OCG_BUILD_FUNCTION_REF",
    "META_OCG_CREATE_NODE_FUNCTION",
    "META_OCG_CREATE_NODE_FUNCTION_REF",
    "META_OCG_DELETE_NODE_FUNCTION_REF",
    "META_OCG_PACKAGE_ATTACH_GRAPH_FUNCTION",
    "META_OCG_PACKAGE_ATTACH_GRAPH_FUNCTION_REF",
    "META_OCG_PACKAGE_BUILD_FUNCTION",
    "META_OCG_PACKAGE_BUILD_FUNCTION_REF",
    "META_SEMANTIC_FUNCTION_REFS",
    "MetaSemanticFunctionCallResolution",
    "MetaSemanticFunctionCallResolutionStatus",
    "resolve_meta_semantic_function_call_plan_previews",
]
