"""Bootstrap helpers for node-first meta models against stale generated artifacts."""

from __future__ import annotations

from typing import cast
from uuid import UUID

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_meta_ontology.graph.config.object_config_graph_node import ObjectConfigGraphNode
from aware_meta_ontology.graph.config.object_config_graph_node_layout import ObjectConfigGraphNodeLayout


def class_config_supports_class_fqn() -> bool:
    return "class_fqn" in ClassConfig.model_fields


def class_config_supports_node_fk() -> bool:
    return "object_config_graph_node_id" in ClassConfig.model_fields


def enum_config_supports_node_fk() -> bool:
    return "object_config_graph_node_id" in EnumConfig.model_fields


def object_config_graph_node_supports_node_key() -> bool:
    return "node_key" in ObjectConfigGraphNode.model_fields


def object_config_graph_node_supports_function_config() -> bool:
    return "function_config" in ObjectConfigGraphNode.model_fields


def _as_object_dict(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    if not all(isinstance(key, str) for key in value):
        return None
    return cast(dict[str, object], value)


def _as_object_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, object]] = []
    for item in value:
        obj = _as_object_dict(item)
        if obj is not None:
            out.append(obj)
    return out


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _node_type(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    return text.casefold()


def _reference_attribute_name(relationship_payload: dict[str, object]) -> str | None:
    for rel_attr in _as_object_list(relationship_payload.get("class_config_relationship_attributes")):
        direction = _node_type(rel_attr.get("direction"))
        role = _node_type(rel_attr.get("role"))
        if direction != "forward" or role != "reference":
            continue
        attribute_payload = _as_object_dict(rel_attr.get("attribute_config"))
        if attribute_payload is None:
            continue
        name = _text(attribute_payload.get("name"))
        if name:
            return name
    return None


def _derive_function_node_key(
    *,
    node_payload: dict[str, object],
    owner_fqn_by_function_id: dict[str, str],
) -> str | None:
    function_payload = _as_object_dict(node_payload.get("function_config"))
    function_id = _text(node_payload.get("function_config_id"))
    if function_payload is None and function_id is None:
        return None
    name = _text(function_payload.get("name")) if function_payload is not None else None
    kind = _text(function_payload.get("kind")) if function_payload is not None else None
    owner_fqn = owner_fqn_by_function_id.get(function_id or "")
    if owner_fqn and name and kind:
        return f"{owner_fqn}:{kind}:{name}"
    if function_id:
        return function_id
    if name and kind:
        return f"{kind}:{name}"
    return name


def _derive_relationship_node_key(
    *,
    relationship_payload: dict[str, object],
    class_fqn_by_id: dict[str, str],
) -> str | None:
    source_id = _text(relationship_payload.get("class_config_id"))
    target_id = _text(relationship_payload.get("target_class_config_id"))
    source_fqn = class_fqn_by_id.get(source_id or "")
    target_fqn = class_fqn_by_id.get(target_id or "")
    relationship_key = _text(relationship_payload.get("relationship_key")) or _reference_attribute_name(relationship_payload)
    relationship_type = _text(relationship_payload.get("relationship_type"))
    if source_fqn and target_fqn and relationship_key and relationship_type:
        return f"{source_fqn}:{relationship_key}:{relationship_type}:{target_fqn}"
    return _text(relationship_payload.get("id"))


def normalize_object_config_graph_payload_for_bootstrap(*, payload: object) -> object:
    graph_payload = _as_object_dict(payload)
    if graph_payload is None:
        return payload

    class_fqn_by_id: dict[str, str] = {}
    owner_fqn_by_function_id: dict[str, str] = {}
    for node_payload in _as_object_list(graph_payload.get("object_config_graph_nodes")):
        node_id = _text(node_payload.get("id"))

        class_payload = _as_object_dict(node_payload.get("class_config"))
        if class_payload is not None:
            class_fqn = _text(class_payload.get("class_fqn"))
            if class_fqn:
                class_payload["class_fqn"] = class_fqn
                class_id = _text(class_payload.get("id")) or _text(node_payload.get("class_config_id"))
                if class_id:
                    class_fqn_by_id[class_id] = class_fqn
            if node_id and "object_config_graph_node_id" not in class_payload:
                class_payload["object_config_graph_node_id"] = node_id
            for edge_payload in _as_object_list(class_payload.get("class_config_function_configs")):
                function_payload = _as_object_dict(edge_payload.get("function_config"))
                function_id = _text(edge_payload.get("function_config_id"))
                if function_payload is not None:
                    function_id = function_id or _text(function_payload.get("id"))
                if class_fqn and function_id:
                    owner_fqn_by_function_id[function_id] = class_fqn

        enum_payload = _as_object_dict(node_payload.get("enum_config"))
        if enum_payload is not None:
            enum_fqn = _text(enum_payload.get("enum_fqn"))
            if enum_fqn:
                enum_payload["enum_fqn"] = enum_fqn
            if node_id and "object_config_graph_node_id" not in enum_payload:
                enum_payload["object_config_graph_node_id"] = node_id

    for node_payload in _as_object_list(graph_payload.get("object_config_graph_nodes")):
        relationship_payload = _as_object_dict(node_payload.get("class_config_relationship"))
        if relationship_payload is not None and "relationship_key" not in relationship_payload:
            relationship_key = _reference_attribute_name(relationship_payload) or _text(relationship_payload.get("id"))
            if relationship_key:
                relationship_payload["relationship_key"] = relationship_key

        node_key = _text(node_payload.get("node_key"))
        if node_key:
            continue

        node_type = _node_type(node_payload.get("type"))
        derived_node_key: str | None = None
        if node_type in {"class", "class_"}:
            class_payload = _as_object_dict(node_payload.get("class_config"))
            if class_payload is not None:
                derived_node_key = _text(class_payload.get("class_fqn")) or _text(class_payload.get("name"))
            if derived_node_key is None:
                derived_node_key = class_fqn_by_id.get(_text(node_payload.get("class_config_id")) or "")
        elif node_type == "enum":
            enum_payload = _as_object_dict(node_payload.get("enum_config"))
            if enum_payload is not None:
                derived_node_key = _text(enum_payload.get("enum_fqn")) or _text(enum_payload.get("id"))
            if derived_node_key is None:
                derived_node_key = _text(node_payload.get("enum_config_id"))
        elif node_type == "function":
            derived_node_key = _derive_function_node_key(
                node_payload=node_payload,
                owner_fqn_by_function_id=owner_fqn_by_function_id,
            )
        elif node_type == "relationship":
            relationship_payload = _as_object_dict(node_payload.get("class_config_relationship"))
            if relationship_payload is not None:
                derived_node_key = _derive_relationship_node_key(
                    relationship_payload=relationship_payload,
                    class_fqn_by_id=class_fqn_by_id,
                )
            if derived_node_key is None:
                derived_node_key = _text(node_payload.get("class_config_relationship_id"))

        if derived_node_key is None:
            derived_node_key = (
                _text(node_payload.get("class_config_id"))
                or _text(node_payload.get("enum_config_id"))
                or _text(node_payload.get("function_config_id"))
                or _text(node_payload.get("class_config_relationship_id"))
                or _text(node_payload.get("id"))
            )
        if derived_node_key:
            node_payload["node_key"] = derived_node_key

    return graph_payload


def normalize_environment_config_payload_for_bootstrap(*, payload: object) -> object:
    environment_payload = _as_object_dict(payload)
    if environment_payload is None:
        return payload
    for graph_payload in _as_object_list(environment_payload.get("object_config_graphs")):
        normalize_object_config_graph_payload_for_bootstrap(payload=graph_payload)
    return environment_payload


def get_class_config_fqn(class_config: ClassConfig) -> str | None:
    if not class_config_supports_class_fqn():
        return None
    value = class_config.class_fqn
    return (value or "").strip() or None


def get_function_config_owner_key(function_config: FunctionConfig) -> str | None:
    value = function_config.owner_key
    return (value or "").strip() or None


def get_object_config_graph_node_key(node: ObjectConfigGraphNode) -> str | None:
    if not object_config_graph_node_supports_node_key():
        return None
    value = node.node_key
    return (value or "").strip() or None


def get_object_config_graph_node_class_config_id(node: ObjectConfigGraphNode) -> UUID | None:
    value = getattr(node, "class_config_id", None)
    if isinstance(value, UUID):
        return value
    class_config = node.class_config
    if class_config is None:
        return None
    return class_config.id


def get_object_config_graph_node_enum_config_id(node: ObjectConfigGraphNode) -> UUID | None:
    value = getattr(node, "enum_config_id", None)
    if isinstance(value, UUID):
        return value
    enum_config = node.enum_config
    if enum_config is None:
        return None
    return enum_config.id


def get_object_config_graph_node_relationship_id(node: ObjectConfigGraphNode) -> UUID | None:
    value = getattr(node, "class_config_relationship_id", None)
    if isinstance(value, UUID):
        return value
    relationship = node.class_config_relationship
    if relationship is None:
        return None
    return relationship.id


def get_object_config_graph_node_function_id(node: ObjectConfigGraphNode) -> UUID | None:
    value = getattr(node, "function_config_id", None)
    if isinstance(value, UUID):
        return value
    function_config = get_node_function_config(node)
    if function_config is None:
        return None
    return function_config.id


def get_node_function_config(node: ObjectConfigGraphNode) -> FunctionConfig | None:
    if not object_config_graph_node_supports_function_config():
        return None
    value = getattr(node, "function_config", None)
    return value if isinstance(value, FunctionConfig) else None


def set_class_config_identity_fields(
    *,
    class_config: ClassConfig,
    object_config_graph_node_id: UUID,
    class_fqn: str,
) -> None:
    if class_config_supports_node_fk():
        class_config.object_config_graph_node_id = object_config_graph_node_id
    if class_config_supports_class_fqn():
        class_config.class_fqn = class_fqn


def set_enum_config_identity_fields(
    *,
    enum_config: EnumConfig,
    object_config_graph_node_id: UUID,
) -> None:
    if enum_config_supports_node_fk():
        enum_config.object_config_graph_node_id = object_config_graph_node_id


def build_class_config(
    *,
    class_config_id: UUID,
    name: str,
    is_base: bool,
    is_edge: bool,
    description: str | None,
    value_mode: ClassValueMode,
    object_config_graph_node_id: UUID,
    class_fqn: str,
    parent_class_id: UUID | None = None,
    class_config_relationships: list[ClassConfigRelationship] | None = None,
    class_config_attribute_configs: list[object] | None = None,
    class_config_function_configs: list[object] | None = None,
) -> ClassConfig:
    payload: dict[str, object] = {
        "id": class_config_id,
        "name": name,
        "is_base": is_base,
        "is_edge": is_edge,
        "description": description,
        "value_mode": value_mode,
        "parent_class_id": parent_class_id,
        "class_config_relationships": class_config_relationships or [],
        "class_config_attribute_configs": class_config_attribute_configs or [],
        "class_config_function_configs": class_config_function_configs or [],
    }
    if class_config_supports_node_fk():
        payload["object_config_graph_node_id"] = object_config_graph_node_id
    if class_config_supports_class_fqn():
        payload["class_fqn"] = class_fqn
    return ClassConfig(**payload)


def build_enum_config(
    *,
    enum_config_id: UUID,
    enum_fqn: str,
    name: str,
    description: str | None,
    enum_options: list[object] | None = None,
    object_config_graph_node_id: UUID,
) -> EnumConfig:
    payload: dict[str, object] = {
        "id": enum_config_id,
        "enum_fqn": enum_fqn,
        "name": name,
        "description": description,
        "enum_options": enum_options or [],
    }
    if enum_config_supports_node_fk():
        payload["object_config_graph_node_id"] = object_config_graph_node_id
    return EnumConfig(**payload)


def build_object_config_graph_node(
    *,
    object_config_graph_node_id: UUID,
    object_config_graph_id: UUID,
    type: ObjectConfigGraphNodeType,
    node_key: str,
    class_config: ClassConfig | None = None,
    enum_config: EnumConfig | None = None,
    function_config: FunctionConfig | None = None,
    class_config_relationship: ClassConfigRelationship | None = None,
    layouts: list[ObjectConfigGraphNodeLayout] | None = None,
) -> ObjectConfigGraphNode:
    payload: dict[str, object] = {
        "id": object_config_graph_node_id,
        "object_config_graph_id": object_config_graph_id,
        "type": type,
        "layouts": layouts or [],
        "class_config": class_config,
        "class_config_id": class_config.id if class_config is not None else None,
        "enum_config": enum_config,
        "enum_config_id": enum_config.id if enum_config is not None else None,
        "class_config_relationship": class_config_relationship,
        "class_config_relationship_id": (
            class_config_relationship.id if class_config_relationship is not None else None
        ),
    }
    if object_config_graph_node_supports_function_config():
        payload["function_config"] = function_config
        payload["function_config_id"] = function_config.id if function_config is not None else None
    if object_config_graph_node_supports_node_key():
        payload["node_key"] = node_key
    return ObjectConfigGraphNode(**payload)


__all__ = [
    "build_class_config",
    "build_enum_config",
    "build_object_config_graph_node",
    "class_config_supports_class_fqn",
    "class_config_supports_node_fk",
    "enum_config_supports_node_fk",
    "get_class_config_fqn",
    "get_object_config_graph_node_class_config_id",
    "get_object_config_graph_node_enum_config_id",
    "get_object_config_graph_node_function_id",
    "get_node_function_config",
    "get_object_config_graph_node_key",
    "get_object_config_graph_node_relationship_id",
    "normalize_environment_config_payload_for_bootstrap",
    "normalize_object_config_graph_payload_for_bootstrap",
    "object_config_graph_node_supports_function_config",
    "object_config_graph_node_supports_node_key",
    "set_class_config_identity_fields",
    "set_enum_config_identity_fields",
]
