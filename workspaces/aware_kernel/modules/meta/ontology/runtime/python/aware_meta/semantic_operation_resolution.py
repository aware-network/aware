from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from uuid import UUID
from typing import Literal

from aware_code.semantic_capability import (
    SemanticCapabilityTypedOperation,
)


META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY = (
    "semantic_operation_function_call_resolution"
)
META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION = (
    "aware.meta.object_config_graph.semantic_operation_function_call_resolution.v0"
)
META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.attribute.type.update"
)
META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DEFAULT_VALUE_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.attribute.default_value.update"
)
META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_MEMBERSHIP_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.attribute.membership.update"
)
META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION = (
    "aware_meta.object_config_graph.attribute.create"
)
META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION = (
    "aware_meta.object_config_graph.attribute.delete"
)
META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION = (
    "aware_meta.object_config_graph.attribute.identity.rename"
)
META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION = (
    "aware_meta.object_config_graph.function.create"
)
META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION = (
    "aware_meta.object_config_graph.function.delete"
)
META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.function.signature.update"
)
META_OBJECT_CONFIG_GRAPH_FUNCTION_IMPL_BODY_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.function_impl.body.update"
)
META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION = (
    "aware_meta.object_config_graph.class.create"
)
META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION = (
    "aware_meta.object_config_graph.class.delete"
)
META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.class.description.update"
)
META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.enum.description.update"
)
META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION = (
    "aware_meta.object_config_graph.enum.create"
)
META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION = (
    "aware_meta.object_config_graph.enum.delete"
)
META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION = (
    "aware_meta.object_config_graph.enum_option.create"
)
META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.enum_option.position.update"
)
META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION = (
    "aware_meta.object_config_graph.enum_option.delete"
)
META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.relationship.load_policy.update"
)
META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION = (
    "aware_meta.object_config_graph.relationship.create"
)
META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_DELETE_OPERATION = (
    "aware_meta.object_config_graph.relationship.delete"
)
META_ATTRIBUTE_TYPE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.attribute.type.generated_materialization_intent.v0"
)
META_ATTRIBUTE_DEFAULT_VALUE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.attribute.default_value.generated_materialization_intent.v0"
)
META_ATTRIBUTE_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.attribute.create.generated_materialization_intent.v0"
)
META_ATTRIBUTE_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.attribute.delete.generated_materialization_intent.v0"
)
META_FUNCTION_SIGNATURE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.function.signature.generated_materialization_intent.v0"
)
META_FUNCTION_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.function.delete.generated_materialization_intent.v0"
)
META_CLASS_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.class.create.generated_materialization_intent.v0"
)
META_CLASS_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.class.delete.generated_materialization_intent.v0"
)
META_CLASS_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.class.description.generated_materialization_intent.v0"
)
META_ENUM_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.enum.create.generated_materialization_intent.v0"
)
META_ENUM_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.enum.delete.generated_materialization_intent.v0"
)
META_ENUM_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.enum.description.generated_materialization_intent.v0"
)
META_ENUM_OPTION_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.enum_option.create.generated_materialization_intent.v0"
)
META_ENUM_OPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.enum_option.generated_materialization_intent.v0"
)
META_RELATIONSHIP_LOAD_POLICY_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.relationship.load_policy.generated_materialization_intent.v0"
)
META_RELATIONSHIP_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.relationship.create.generated_materialization_intent.v0"
)
META_RELATIONSHIP_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.relationship.delete.generated_materialization_intent.v0"
)

ATTRIBUTE_CONFIG_UPDATE_PRIMITIVE_FUNCTION_REF = (
    "aware_meta_ontology.attribute.attribute_config." "AttributeConfig.update_primitive"
)
ATTRIBUTE_CONFIG_UPDATE_ENUM_FUNCTION_REF = (
    "aware_meta_ontology.attribute.attribute_config.AttributeConfig.update_enum"
)
ATTRIBUTE_CONFIG_UPDATE_CLASS_FUNCTION_REF = (
    "aware_meta_ontology.attribute.attribute_config.AttributeConfig.update_class"
)
CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config.ClassConfig.create_function_config"
)
CLASS_CONFIG_UPDATE_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config.ClassConfig.update_config"
)

MetaSemanticOperationResolutionStatus = Literal[
    "function_call_plan_ready",
    "function_call_plan_blocked",
    "unsupported_operation",
]

_PRIMITIVE_TYPE_NAMES = frozenset(
    {
        "Any",
        "Bool",
        "Boolean",
        "Date",
        "DateTime",
        "Decimal",
        "Float",
        "Int",
        "Json",
        "Number",
        "String",
        "Text",
        "UUID",
        "Uuid",
        "any",
        "bool",
        "boolean",
        "date",
        "datetime",
        "decimal",
        "float",
        "int",
        "json",
        "number",
        "string",
        "text",
        "uuid",
    }
)


@dataclass(frozen=True, slots=True)
class MetaSemanticOperationFunctionCallPlan:
    operation_key: str
    semantic_operation_type: str
    semantic_key: str
    function_ref: str
    binding_key: str | None = None
    event_key: str | None = None
    receiver_semantic_key: str | None = None
    receiver_object_id: str | None = None
    arguments: Mapping[str, object] = field(default_factory=dict)
    argument_refs: Mapping[str, str] = field(default_factory=dict)
    result_semantic_key: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "plan_kind": "meta_semantic_operation_function_call_plan_preview",
            "contract_version": (
                META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION
            ),
            "operation_key": self.operation_key,
            "semantic_operation_type": self.semantic_operation_type,
            "semantic_key": self.semantic_key,
            "function_ref": self.function_ref,
            "arguments": dict(self.arguments),
            "argument_refs": dict(self.argument_refs),
            "metadata": dict(self.metadata),
            "mutates": False,
            "execution_status": "not_requested",
            "would_execute": False,
            "did_execute": False,
        }
        if self.binding_key is not None:
            payload["binding_key"] = self.binding_key
        if self.event_key is not None:
            payload["event_key"] = self.event_key
        if self.receiver_semantic_key is not None:
            payload["receiver_semantic_key"] = self.receiver_semantic_key
        if self.receiver_object_id is not None:
            payload["receiver_object_id"] = self.receiver_object_id
        if self.result_semantic_key is not None:
            payload["result_semantic_key"] = self.result_semantic_key
        return payload


@dataclass(frozen=True, slots=True)
class MetaSemanticOperationResolution:
    operation_key: str
    semantic_operation_type: str
    semantic_key: str
    status: MetaSemanticOperationResolutionStatus
    reason: str
    function_call_plan: MetaSemanticOperationFunctionCallPlan | None = None
    blockers: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return self.status == "function_call_plan_ready"

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "resolution_kind": ("meta_semantic_operation_function_call_resolution"),
            "contract_version": (
                META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION
            ),
            "operation_key": self.operation_key,
            "semantic_operation_type": self.semantic_operation_type,
            "semantic_key": self.semantic_key,
            "status": self.status,
            "reason": self.reason,
            "blocker_count": len(self.blockers),
            "blockers": self.blockers,
            "metadata": dict(self.metadata),
            "mutates": False,
            "execution_status": "not_requested",
            "would_execute": False,
            "did_execute": False,
        }
        if self.function_call_plan is not None:
            payload["function_call_plan"] = self.function_call_plan.evidence_payload()
        return payload


def resolve_meta_semantic_operation_function_call_plan_previews(
    *,
    typed_operations: Iterable[object],
    current_semantic_object_ids: Mapping[str, object] | None = None,
    baseline_semantic_object_identities: (
        Mapping[str, Mapping[str, object]] | None
    ) = None,
) -> tuple[MetaSemanticOperationResolution, ...]:
    current_objects = _normalize_object_id_map(current_semantic_object_ids)
    current_object_identities = _normalize_semantic_object_identities(
        baseline_semantic_object_identities,
    )
    operation_payloads = tuple(
        _operation_payload(raw_operation) for raw_operation in typed_operations
    )
    current_objects = _current_objects_with_signature_update_aliases(
        operations=operation_payloads,
        current_objects=current_objects,
    )
    return tuple(
        _resolve_operation(
            operation=operation,
            operation_group=operation_payloads,
            current_objects=current_objects,
            current_object_identities=current_object_identities,
        )
        for operation in operation_payloads
    )


def _resolve_operation(
    *,
    operation: Mapping[str, object],
    operation_group: tuple[Mapping[str, object], ...],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    operation_type = _string_value(operation.get("semantic_operation_type"))
    feature_resolution = _resolve_operation_from_feature_provider(
        operation_type=operation_type,
        operation=operation,
        operation_group=operation_group,
        current_objects=current_objects,
        current_object_identities=current_object_identities,
    )
    if feature_resolution is not None:
        return feature_resolution
    return _unsupported_resolution(
        operation=operation,
        reason="meta_ocg_semantic_operation_type_not_supported",
        blockers=(f"unsupported_operation_type:{operation_type or 'unknown'}",),
    )


def _resolve_operation_from_feature_provider(
    *,
    operation_type: str,
    operation: Mapping[str, object],
    operation_group: tuple[Mapping[str, object], ...],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution | None:
    from aware_meta.materialization.deltas.feature_registry import (  # noqa: WPS433,E501
        semantic_operation_resolver_for_type,
    )

    resolver = semantic_operation_resolver_for_type(operation_type)
    if resolver is None:
        return None
    resolution = resolver(
        operation=operation,
        operation_group=operation_group,
        current_objects=current_objects,
        current_object_identities=current_object_identities,
    )
    if isinstance(resolution, MetaSemanticOperationResolution):
        return resolution
    return _blocked_resolution(
        operation=operation,
        reason="meta_ocg_semantic_operation_feature_resolver_invalid_result",
        blockers=(f"invalid_feature_resolver_result:{operation_type or 'unknown'}",),
    )



def _provider_delta_typed_operation_metadata_for_signature_update(
    *,
    operation: Mapping[str, object],
    function_config_id: str | None = None,
) -> dict[str, object]:
    from aware_meta.function.config.deltas.semantic_operation_resolution import (  # noqa: WPS433,E501
        provider_delta_typed_operation_metadata_for_signature_update,
    )

    return provider_delta_typed_operation_metadata_for_signature_update(
        operation=operation,
        function_config_id=function_config_id,
    )


def _blocked_resolution(
    *,
    operation: Mapping[str, object],
    reason: str,
    blockers: tuple[str, ...],
    metadata: Mapping[str, object] | None = None,
) -> MetaSemanticOperationResolution:
    return MetaSemanticOperationResolution(
        operation_key=_operation_key(operation),
        semantic_operation_type=_semantic_operation_type(operation),
        semantic_key=_semantic_key(operation),
        status="function_call_plan_blocked",
        reason=reason,
        blockers=blockers,
        metadata=metadata or {},
    )


def _unsupported_resolution(
    *,
    operation: Mapping[str, object],
    reason: str,
    blockers: tuple[str, ...],
) -> MetaSemanticOperationResolution:
    return MetaSemanticOperationResolution(
        operation_key=_operation_key(operation),
        semantic_operation_type=_semantic_operation_type(operation),
        semantic_key=_semantic_key(operation),
        status="unsupported_operation",
        reason=reason,
        blockers=blockers,
    )


def _operation_payload(value: object) -> Mapping[str, object]:
    if isinstance(value, SemanticCapabilityTypedOperation):
        return value.evidence_payload()
    if isinstance(value, Mapping):
        return _mapping_value(value)
    return {}


def _operation_key(operation: Mapping[str, object]) -> str:
    return _string_value(operation.get("operation_key")) or "unknown_operation"


def _semantic_operation_type(operation: Mapping[str, object]) -> str:
    return (
        _string_value(operation.get("semantic_operation_type"))
        or "unknown_semantic_operation_type"
    )


def _semantic_key(operation: Mapping[str, object]) -> str:
    return _string_value(operation.get("semantic_key")) or "unknown_semantic_key"


def _normalize_object_id_map(
    value: Mapping[str, object] | None,
) -> dict[str, str]:
    if value is None:
        return {}
    return {
        str(key): str(item)
        for key, item in value.items()
        if str(key).strip() and str(item).strip()
    }


def _normalize_semantic_object_identities(
    value: Mapping[str, Mapping[str, object]] | None,
) -> dict[str, dict[str, object]]:
    if value is None:
        return {}
    identities: dict[str, dict[str, object]] = {}
    for key, item in value.items():
        semantic_key = str(key).strip()
        if not semantic_key or not isinstance(item, Mapping):
            continue
        identities[semantic_key] = dict(item)
    return identities


def _current_objects_with_signature_update_aliases(
    *,
    operations: tuple[Mapping[str, object], ...],
    current_objects: Mapping[str, str],
) -> dict[str, str]:
    enriched = dict(current_objects)
    for operation in operations:
        if _semantic_operation_type(operation) != (
            META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION
        ):
            continue
        for alias, object_id in _signature_update_current_input_aliases(
            operation=operation,
            current_objects=enriched,
        ).items():
            enriched.setdefault(alias, object_id)
    return enriched


def _signature_update_current_input_aliases(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
) -> dict[str, str]:
    typed_operation = _provider_delta_typed_operation_for_signature_update(
        operation=operation,
    )
    if typed_operation is None:
        return {}
    current = _mapping_value(typed_operation.get("current"))
    payload = _mapping_value(current.get("payload"))
    signature = _mapping_value(
        current.get("function_signature") or payload.get("function_signature")
    )
    class_name = _first_text(
        _class_name_from_semantic_key(_semantic_key(operation)),
        current.get("owner_key"),
        payload.get("owner_key"),
    )
    function_name = _first_text(
        current.get("function_name"),
        current.get("name"),
        payload.get("function_name"),
        payload.get("name"),
        signature.get("name"),
        _function_name_from_semantic_key(_semantic_key(operation)),
    )
    function_config_id = _function_config_id_for_signature_update(
        operation=operation,
        current=current,
        payload=payload,
        class_name=class_name,
        function_name=function_name,
        current_objects=current_objects,
    )
    function_config_uuid = _uuid_value(function_config_id)
    if class_name is None or function_name is None or function_config_uuid is None:
        return {}
    aliases: dict[str, str] = {}
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_function_config_attribute_config_id,
    )

    for input_item in (
        _mapping_value(item) for item in _tuple_values(signature.get("inputs"))
    ):
        input_name = _optional_text(input_item.get("name"))
        input_type = _first_text(input_item.get("type"), "input")
        if input_name is None:
            continue
        input_id = stable_function_config_attribute_config_id(
            function_config_id=function_config_uuid,
            name=input_name,
            type=input_type or "input",
        )
        aliases[
            f"meta.function_input_edge:{class_name}.{function_name}.{input_name}"
        ] = str(input_id)
        aliases[
            f"meta.function_attribute_edge:{class_name}.{function_name}.{input_name}"
        ] = str(input_id)
    return aliases


def _provider_delta_typed_operation_for_signature_update(
    *,
    operation: Mapping[str, object],
) -> Mapping[str, object] | None:
    metadata = _provider_delta_typed_operation_metadata_for_signature_update(
        operation=operation,
    )
    typed_operation = metadata.get("provider_delta_typed_operation")
    if isinstance(typed_operation, Mapping):
        return typed_operation
    return None


def _function_config_id_for_signature_update(
    *,
    operation: Mapping[str, object],
    current: Mapping[str, object],
    payload: Mapping[str, object],
    class_name: str | None,
    function_name: str | None,
    current_objects: Mapping[str, str],
) -> str | None:
    direct = _first_text(
        current.get("entity_id"),
        current.get("function_config_id"),
        payload.get("entity_id"),
        payload.get("function_config_id"),
        current_objects.get(_semantic_key(operation)),
    )
    if direct is not None:
        return direct
    if class_name is None or function_name is None:
        return None
    meta_key = f"meta.function:{class_name}.{function_name}"
    direct = _optional_text(current_objects.get(meta_key))
    if direct is not None:
        return direct
    suffix = f".{class_name}.{function_name}"
    for semantic_key, object_id in sorted(current_objects.items()):
        if semantic_key.endswith(suffix):
            return object_id
    return None


def _relationship_class_from_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.relationship:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        if "." in raw:
            return raw.rsplit(".", maxsplit=1)[0]
    marker = "/relationship:"
    if marker in semantic_key:
        owner = semantic_key.rsplit(marker, maxsplit=1)[0]
        return owner.rsplit(".", maxsplit=1)[-1]
    return None


def _relationship_key_from_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.relationship:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        if "." in raw:
            return raw.rsplit(".", maxsplit=1)[-1]
    marker = "/relationship:"
    if marker in semantic_key:
        return semantic_key.rsplit(marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
    return None


def _uuid_value(value: object) -> UUID | None:
    text = _optional_text(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _mapping_value(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _tuple_values(value: object) -> tuple[object, ...]:
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
        return tuple(value)
    return ()


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _set_missing_text(target: dict[str, object], key: str, value: str) -> None:
    if _optional_text(target.get(key)) is None:
        target[key] = value


def _function_name_from_semantic_key(semantic_key: str) -> str | None:
    raw_name = semantic_key.rsplit(":", maxsplit=1)[-1].rsplit(".", maxsplit=1)[-1]
    if not raw_name or raw_name == semantic_key:
        return None
    return raw_name


def _class_name_from_semantic_key(semantic_key: str) -> str | None:
    marker = "meta.function:"
    if marker not in semantic_key:
        return None
    path = semantic_key.split(marker, maxsplit=1)[-1]
    class_name = path.rsplit(".", maxsplit=1)[0]
    return class_name or None


def _class_name_from_attribute_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.attribute:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        if "." in raw:
            return raw.rsplit(".", maxsplit=1)[0] or None
    marker = "/attribute:"
    if marker in semantic_key:
        owner = semantic_key.rsplit(marker, maxsplit=1)[0]
        return owner.rsplit(".", maxsplit=1)[-1] or None
    return None


def _attribute_name_from_attribute_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.attribute:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        if "." in raw:
            return raw.rsplit(".", maxsplit=1)[-1] or None
    marker = "/attribute:"
    if marker in semantic_key:
        raw_attribute = semantic_key.rsplit(marker, maxsplit=1)[-1]
        return raw_attribute.rsplit("/", maxsplit=1)[0].rsplit(":", maxsplit=1)[-1]
    return None


def _function_name_from_function_impl_semantic_key(semantic_key: str) -> str | None:
    marker = "meta.function_impl:"
    if marker not in semantic_key:
        return None
    path = semantic_key.split(marker, maxsplit=1)[-1]
    if ":" in path:
        path = path.split(":", maxsplit=1)[0]
    raw_name = path.rsplit(".", maxsplit=1)[-1]
    return raw_name or None


def _class_name_from_function_impl_semantic_key(semantic_key: str) -> str | None:
    marker = "meta.function_impl:"
    if marker not in semantic_key:
        return None
    path = semantic_key.split(marker, maxsplit=1)[-1]
    if ":" in path:
        path = path.split(":", maxsplit=1)[0]
    class_name = path.rsplit(".", maxsplit=1)[0]
    return class_name or None


def _class_name_from_class_semantic_key(semantic_key: str) -> str | None:
    marker = "meta.class:"
    if marker in semantic_key:
        class_name = semantic_key.split(marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
        return class_name.rsplit(".", maxsplit=1)[-1] or None
    node_marker = "/node:"
    if node_marker in semantic_key:
        node_key = semantic_key.split(node_marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
        return node_key.rsplit(".", maxsplit=1)[-1] or None
    return None


def _class_fqn_from_class_semantic_key(semantic_key: str) -> str | None:
    marker = "meta.class:"
    if marker in semantic_key:
        return _optional_text(
            semantic_key.split(marker, maxsplit=1)[-1].split("/", maxsplit=1)[0],
        )
    node_marker = "/node:"
    if node_marker in semantic_key:
        return _optional_text(
            semantic_key.split(node_marker, maxsplit=1)[-1].split("/", maxsplit=1)[0],
        )
    return None


def _class_config_id_for_class_update(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    class_name: str | None,
    receiver_semantic_key: str,
) -> str | None:
    direct = _first_text(
        current_objects.get(receiver_semantic_key),
        current_objects.get(_semantic_key(operation)),
    )
    if direct is not None:
        return direct
    if class_name is None:
        return None
    for semantic_key, object_id in sorted(current_objects.items()):
        if semantic_key.endswith(f".{class_name}") or semantic_key.endswith(
            f"/node:{class_name}"
        ):
            return object_id
    return None


def _enum_config_id_for_enum_update(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    enum_name: str | None,
    enum_fqn: str | None,
    receiver_semantic_key: str,
) -> str | None:
    direct = _first_text(
        current_objects.get(receiver_semantic_key),
        current_objects.get(_semantic_key(operation)),
    )
    if direct is not None:
        return direct
    candidates = tuple(
        candidate
        for candidate in (enum_fqn, enum_name)
        if candidate is not None and candidate.strip()
    )
    for candidate in candidates:
        for semantic_key, object_id in sorted(current_objects.items()):
            if semantic_key.endswith(f"/node:{candidate}") or semantic_key.endswith(
                f".{candidate}"
            ):
                return object_id
    return None


def _enum_config_id_for_structural_enum(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
    enum_name: str | None,
    enum_fqn: str | None,
    enum_semantic_key: str,
) -> str | None:
    existing = _enum_config_id_for_enum_update(
        operation=operation,
        current_objects=current_objects,
        enum_name=enum_name,
        enum_fqn=enum_fqn,
        receiver_semantic_key=enum_semantic_key,
    )
    if existing is not None:
        return existing
    after_payload = _mapping_value(operation.get("after_payload"))
    graph_semantic_key = _first_text(
        after_payload.get("graph_semantic_key"),
        operation.get("graph_semantic_key"),
        _graph_semantic_key_from_enum_semantic_key(enum_semantic_key),
        _graph_semantic_key_from_operation_package_context(operation),
    )
    graph_receiver_object_id = _enum_create_graph_object_id(
        operation=operation,
        current_objects=current_objects,
        graph_semantic_key=graph_semantic_key,
    )
    graph_source_object_id = _enum_create_graph_source_object_id(
        operation=operation,
        current_object_identities=current_object_identities,
        graph_semantic_key=graph_semantic_key,
        fallback_object_id=graph_receiver_object_id,
    )
    object_config_graph_node_id = _stable_object_config_graph_node_id_for_enum_create(
        graph_object_id=graph_source_object_id,
        enum_fqn=enum_fqn,
    )
    return _stable_enum_config_id_for_create(
        object_config_graph_node_id=object_config_graph_node_id,
        enum_fqn=enum_fqn,
    )


def _enum_create_graph_object_id(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    graph_semantic_key: str | None,
) -> str | None:
    after_payload = _mapping_value(operation.get("after_payload"))
    direct = _first_text(
        after_payload.get("object_config_graph_id"),
        after_payload.get("graph_object_id"),
        after_payload.get("graph_id"),
        current_objects.get(graph_semantic_key or ""),
    )
    if direct is not None:
        return direct
    ocg_candidates = tuple(
        (semantic_key, object_id)
        for semantic_key, object_id in current_objects.items()
        if semantic_key.startswith("ocg:")
    )
    if len(ocg_candidates) == 1:
        return ocg_candidates[0][1]
    return None


def _enum_create_graph_source_object_id(
    *,
    operation: Mapping[str, object],
    current_object_identities: Mapping[str, Mapping[str, object]],
    graph_semantic_key: str | None,
    fallback_object_id: str | None,
) -> str | None:
    after_payload = _mapping_value(operation.get("after_payload"))
    identity = current_object_identities.get(graph_semantic_key or "")
    direct = _first_text(
        after_payload.get("semantic_source_object_id"),
        after_payload.get("source_object_id"),
        after_payload.get("object_config_graph_id"),
        after_payload.get("graph_source_object_id"),
        None if identity is None else identity.get("semantic_source_object_id"),
        None if identity is None else identity.get("source_object_id"),
        None if identity is None else identity.get("object_id"),
        None if identity is None else identity.get("entity_id"),
        fallback_object_id,
    )
    return direct


def _graph_semantic_key_from_operation_package_context(
    operation: Mapping[str, object],
) -> str | None:
    fqn_prefix = _first_text(
        operation.get("fqn_prefix"),
        operation.get("source_fqn_prefix"),
        _fqn_prefix_from_package_root(operation.get("package_root")),
        _fqn_prefix_from_package_name(operation.get("package_name")),
    )
    if fqn_prefix is None:
        return None
    return f"ocg:{fqn_prefix}"


def _enum_fqn_from_package_context(
    *,
    enum_name: str | None,
    raw_enum_fqn: str | None,
    operation: Mapping[str, object],
) -> str | None:
    if raw_enum_fqn is None:
        return enum_name
    if "." in raw_enum_fqn:
        return raw_enum_fqn
    fqn_prefix = _first_text(
        operation.get("fqn_prefix"),
        operation.get("source_fqn_prefix"),
        _fqn_prefix_from_package_root(operation.get("package_root")),
        _fqn_prefix_from_package_name(operation.get("package_name")),
    )
    source_namespace = _enum_source_namespace_from_operation(operation=operation)
    resolved_name = enum_name or raw_enum_fqn
    if fqn_prefix is None or source_namespace is None or resolved_name is None:
        return raw_enum_fqn or enum_name
    return ".".join((fqn_prefix, "default", source_namespace, resolved_name))


def _class_fqn_from_package_context(
    *,
    class_name: str | None,
    raw_class_fqn: str | None,
    operation: Mapping[str, object],
) -> str | None:
    if raw_class_fqn is None:
        return class_name
    if "." in raw_class_fqn:
        return raw_class_fqn
    fqn_prefix = _first_text(
        operation.get("fqn_prefix"),
        operation.get("source_fqn_prefix"),
        _fqn_prefix_from_package_root(operation.get("package_root")),
        _fqn_prefix_from_package_name(operation.get("package_name")),
    )
    source_namespace = _enum_source_namespace_from_operation(operation=operation)
    resolved_name = class_name or raw_class_fqn
    if fqn_prefix is None or source_namespace is None or resolved_name is None:
        return raw_class_fqn or class_name
    return ".".join((fqn_prefix, "default", source_namespace, resolved_name))


def _enum_source_namespace_from_operation(
    *,
    operation: Mapping[str, object],
) -> str | None:
    for source_ref_value in _tuple_values(operation.get("source_refs")):
        source_ref = _optional_text(source_ref_value)
        if source_ref is None:
            continue
        normalized = source_ref.replace("\\", "/").strip("/")
        if not normalized.endswith(".aware"):
            continue
        parts = tuple(part for part in normalized.split("/") if part)
        if "aware" in parts:
            parts = parts[parts.index("aware") + 1 :]
        if len(parts) < 2:
            continue
        namespace = ".".join(parts[:-1])
        if namespace:
            return namespace
    return None


def _fqn_prefix_from_package_name(value: object) -> str | None:
    text = _optional_text(value)
    if text is None or not text.endswith("-ontology"):
        return None
    package_key = text[: -len("-ontology")].replace("-", "_").strip("_")
    if not package_key:
        return None
    if package_key.startswith("aware_"):
        return package_key
    return f"aware_{package_key}"


def _fqn_prefix_from_package_root(value: object) -> str | None:
    text = _optional_text(value)
    if text is None:
        return None
    parts = tuple(part for part in text.replace("\\", "/").split("/") if part)
    for index, part in enumerate(parts):
        if part == "modules" and index + 3 < len(parts):
            if parts[index + 2 : index + 4] == ("structure", "ontology"):
                module_key = parts[index + 1].replace("-", "_").strip("_")
                if module_key:
                    return (
                        module_key
                        if module_key.startswith("aware_")
                        else f"aware_{module_key}"
                    )
    return None


def _stable_object_config_graph_node_id_for_enum_create(
    *,
    graph_object_id: str | None,
    enum_fqn: str | None,
) -> str | None:
    graph_uuid = _uuid_value(graph_object_id)
    if graph_uuid is None or enum_fqn is None:
        return None
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_object_config_graph_node_id,
    )

    return str(
        stable_object_config_graph_node_id(
            object_config_graph_id=graph_uuid,
            type="enum",
            node_key=enum_fqn,
        )
    )


def _stable_object_config_graph_node_id_for_class_create(
    *,
    graph_object_id: str | None,
    class_fqn: str | None,
) -> str | None:
    graph_uuid = _uuid_value(graph_object_id)
    if graph_uuid is None or class_fqn is None:
        return None
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_object_config_graph_node_id,
    )

    return str(
        stable_object_config_graph_node_id(
            object_config_graph_id=graph_uuid,
            type="class",
            node_key=class_fqn,
        )
    )


def _stable_class_config_id_for_create(
    *,
    object_config_graph_node_id: str | None,
    class_fqn: str | None,
) -> str | None:
    node_uuid = _uuid_value(object_config_graph_node_id)
    if node_uuid is None or class_fqn is None:
        return None
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_class_config_id,
    )

    return str(
        stable_class_config_id(
            object_config_graph_node_id=node_uuid,
            class_fqn=class_fqn,
        )
    )


def _stable_enum_config_id_for_create(
    *,
    object_config_graph_node_id: str | None,
    enum_fqn: str | None,
) -> str | None:
    node_uuid = _uuid_value(object_config_graph_node_id)
    if node_uuid is None or enum_fqn is None:
        return None
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_enum_config_id,
    )

    return str(
        stable_enum_config_id(
            object_config_graph_node_id=node_uuid,
            enum_fqn=enum_fqn,
        )
    )


def _stable_attribute_config_id_for_create(
    *,
    owner_key: str | None,
    attribute_name: str | None,
) -> str | None:
    if owner_key is None or attribute_name is None:
        return None
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_attribute_config_id,
    )

    return str(stable_attribute_config_id(owner_key=owner_key, name=attribute_name))


def _stable_function_config_id_for_create(
    *,
    owner_key: str | None,
    function_name: str | None,
    kind: str | None = "instance",
) -> str | None:
    if owner_key is None or function_name is None:
        return None
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_function_config_id,
    )

    return str(
        stable_function_config_id(
            owner_key=owner_key,
            name=function_name,
            kind=kind or "instance",
        )
    )


def _stable_relationship_config_id_for_create(
    *,
    source_class_config_id: str | None,
    target_class_config_id: str | None,
    relationship_key: str | None,
) -> str | None:
    source_uuid = _uuid_value(source_class_config_id)
    target_uuid = _uuid_value(target_class_config_id)
    if source_uuid is None or target_uuid is None or relationship_key is None:
        return None
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_class_relationship_id,
    )

    return str(
        stable_class_relationship_id(
            source_class_id=source_uuid,
            target_class_id=target_uuid,
            relationship_key=relationship_key,
        )
    )


def _relationship_target_class_fqn_from_payload(
    *,
    payload: Mapping[str, object],
    source_class_fqn: str | None,
) -> str | None:
    target_class_fqn = _optional_text(payload.get("target_class_fqn"))
    if target_class_fqn is not None:
        return target_class_fqn
    target_class_name = _optional_text(payload.get("target_class_name"))
    if target_class_name is None:
        return None
    if "." in target_class_name:
        return target_class_name
    if source_class_fqn is None or "." not in source_class_fqn:
        return target_class_name
    namespace = source_class_fqn.rsplit(".", maxsplit=1)[0]
    return f"{namespace}.{target_class_name}"


def _enum_option_id_for_existing(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    semantic_key: str,
    option_value: str | None,
) -> str | None:
    before_payload = _mapping_value(operation.get("before_payload"))
    after_payload = _mapping_value(operation.get("after_payload"))
    direct = _first_text(
        current_objects.get(semantic_key),
        current_objects.get(_semantic_key(operation)),
        operation.get("enum_option_id"),
        operation.get("entity_id"),
        operation.get("result_object_id"),
        before_payload.get("enum_option_id"),
        before_payload.get("entity_id"),
        after_payload.get("enum_option_id"),
        after_payload.get("entity_id"),
    )
    if direct is not None:
        return direct
    if option_value is None:
        return None
    for candidate_semantic_key, object_id in sorted(current_objects.items()):
        if candidate_semantic_key.endswith(f"/option:{option_value}"):
            return object_id
    return None


def _enum_name_from_enum_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.enum:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        return raw.rsplit(".", maxsplit=1)[-1] or None
    marker = "/node:"
    if marker in semantic_key:
        node_key = semantic_key.split(marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
        return node_key.rsplit(".", maxsplit=1)[-1] or None
    return None


def _enum_fqn_from_enum_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.enum:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        return raw or None
    marker = "/node:"
    if marker in semantic_key:
        node_key = semantic_key.split(marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
        return node_key or None
    return None


def _graph_semantic_key_from_enum_semantic_key(value: str) -> str | None:
    graph_key, separator, _ = value.partition("/node:")
    if not separator:
        return None
    return _optional_text(graph_key)


def _graph_semantic_key_from_class_semantic_key(value: str) -> str | None:
    graph_key, separator, _ = value.partition("/node:")
    if not separator:
        return None
    return _optional_text(graph_key)


def _enum_semantic_key_from_enum_option_semantic_key(value: str) -> str | None:
    enum_key, separator, _ = value.partition("/option:")
    if not separator:
        return None
    return _optional_text(enum_key)


def _enum_name_from_enum_option_semantic_key(value: str) -> str | None:
    enum_key = _enum_semantic_key_from_enum_option_semantic_key(value)
    if enum_key is None:
        return None
    return _enum_name_from_enum_semantic_key(enum_key)


def _enum_option_value_from_semantic_key(value: str) -> str | None:
    _, separator, option_key = value.partition("/option:")
    if not separator:
        return None
    return _optional_text(option_key)


def _int_value(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _optional_text(value: object) -> str | None:
    text = _string_value(value)
    return text or None


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "ATTRIBUTE_CONFIG_UPDATE_CLASS_FUNCTION_REF",
    "ATTRIBUTE_CONFIG_UPDATE_ENUM_FUNCTION_REF",
    "ATTRIBUTE_CONFIG_UPDATE_PRIMITIVE_FUNCTION_REF",
    "CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF",
    "CLASS_CONFIG_UPDATE_CONFIG_FUNCTION_REF",
    "META_ATTRIBUTE_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_ATTRIBUTE_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_ATTRIBUTE_DEFAULT_VALUE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_ATTRIBUTE_TYPE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_CLASS_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_CLASS_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_CLASS_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_ENUM_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_ENUM_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_ENUM_OPTION_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_ENUM_OPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_FUNCTION_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_FUNCTION_SIGNATURE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_RELATIONSHIP_LOAD_POLICY_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_RELATIONSHIP_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_RELATIONSHIP_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DEFAULT_VALUE_UPDATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_FUNCTION_IMPL_BODY_UPDATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_DELETE_OPERATION",
    "META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION",
    "META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY",
    "META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION",
    "MetaSemanticOperationFunctionCallPlan",
    "MetaSemanticOperationResolution",
    "MetaSemanticOperationResolutionStatus",
    "resolve_meta_semantic_operation_function_call_plan_previews",
]
