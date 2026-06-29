from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)

from aware_meta.graph.config.model_bootstrap import get_node_function_config

_REQUIRED_NAMESPACE_MEMBERSHIP_KEYS = frozenset(
    {
        "entity_id",
        "entity_kind",
        "fqn",
        "node_id",
        "package",
        "symbol",
    }
)


def build_namespace_membership_payload_from_ocg_identity(
    *,
    ocg: ObjectConfigGraph,
) -> tuple[dict[str, object], ...]:
    """Build portable namespace evidence from committed node FQN identity."""

    package = _non_empty_text(getattr(ocg, "fqn_prefix", None))
    if package is None:
        return ()
    entries: list[dict[str, object]] = []
    for node in ocg.object_config_graph_nodes:
        entity = _node_identity_entity(node)
        if entity is None:
            continue
        entity_kind, entity_id, symbol, fqn = entity
        entries.append(
            {
                "entity_id": str(entity_id),
                "entity_kind": entity_kind,
                "fqn": fqn,
                "node_id": str(node.id),
                "package": package,
                "symbol": symbol,
            }
        )
    return tuple(
        sorted(
            entries,
            key=lambda item: (
                str(item["entity_kind"]),
                str(item["fqn"]),
                str(item["entity_id"]),
            ),
        )
    )


def object_config_graph_payload_has_exported_namespace_evidence(
    payload: Mapping[str, object],
) -> bool:
    if not _payload_has_graph_nodes(payload):
        return True
    return (
        object_config_graph_payload_has_namespace_membership(payload)
        and object_config_graph_payload_has_current_namespace_shape(payload)
    )


def object_config_graph_payload_has_namespace_membership(
    payload: Mapping[str, object],
) -> bool:
    membership = payload.get("namespace_membership")
    if not isinstance(membership, list) or not membership:
        return False
    return all(_is_valid_namespace_membership_entry(item) for item in membership)


def object_config_graph_payload_has_current_namespace_shape(
    payload: Mapping[str, object],
) -> bool:
    """Reject domain/schema-era nested records that predate namespace fields."""

    annotations = payload.get("object_config_graph_annotations")
    if isinstance(annotations, list):
        for annotation in annotations:
            if not _annotation_payload_has_current_namespace_shape(annotation):
                return False

    declarations = payload.get("object_projection_graph_declarations")
    if isinstance(declarations, list):
        for declaration in declarations:
            if not _projection_declaration_has_current_namespace_shape(declaration):
                return False

    return True


def _node_identity_entity(
    node: ObjectConfigGraphNode,
) -> tuple[str, UUID, str, str] | None:
    if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
        fqn = _non_empty_text(node.class_config.class_fqn)
        symbol = _non_empty_text(node.class_config.name)
        if fqn is None or symbol is None:
            return None
        return ("class", node.class_config.id, symbol, fqn)
    if node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
        fqn = _non_empty_text(node.enum_config.enum_fqn)
        symbol = _non_empty_text(node.enum_config.name)
        if fqn is None or symbol is None:
            return None
        return ("enum", node.enum_config.id, symbol, fqn)
    if node.type == ObjectConfigGraphNodeType.function:
        function_config = get_node_function_config(node)
        if function_config is not None:
            owner_key = _non_empty_text(function_config.owner_key)
            symbol = _non_empty_text(function_config.name)
            if symbol is None:
                return None
            fqn = f"{owner_key}.{symbol}" if owner_key is not None else node.node_key
            fqn = _non_empty_text(fqn)
            if fqn is None:
                return None
            return ("function", function_config.id, symbol, fqn)
    if (
        node.type == ObjectConfigGraphNodeType.relationship
        and node.class_config_relationship is not None
    ):
        relationship = node.class_config_relationship
        symbol = _non_empty_text(relationship.relationship_key)
        fqn = _non_empty_text(node.node_key)
        if fqn is None or symbol is None:
            return None
        return ("relationship", relationship.id, symbol, fqn)
    return None


def _payload_has_graph_nodes(payload: Mapping[str, object]) -> bool:
    nodes = payload.get("object_config_graph_nodes")
    return isinstance(nodes, list) and bool(nodes)


def _annotation_payload_has_current_namespace_shape(value: object) -> bool:
    if not isinstance(value, Mapping):
        return True
    for key, nested in value.items():
        if not str(key).startswith("code_section_annotation_"):
            continue
        if isinstance(nested, Mapping) and "namespace" not in nested:
            return False
    return True


def _projection_declaration_has_current_namespace_shape(value: object) -> bool:
    if not isinstance(value, Mapping):
        return True
    bindings = value.get("object_projection_graph_bindings")
    if not isinstance(bindings, list):
        return True
    return all(
        not isinstance(binding, Mapping) or "namespace" in binding
        for binding in bindings
    )


def _is_valid_namespace_membership_entry(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    if not _REQUIRED_NAMESPACE_MEMBERSHIP_KEYS.issubset(value.keys()):
        return False
    return all(
        _non_empty_text(value.get(key)) is not None
        for key in _REQUIRED_NAMESPACE_MEMBERSHIP_KEYS
    )


def _non_empty_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
