"""Canonical OIG appliers.

This module supports two closely-related, delta-only apply paths:
- `apply_object_instance_graph_deltas`: applies the internal `ObjectInstanceGraphDelta` tree
  (implementation detail of the Meta graph support diff protocol).
- `apply_object_instance_graph_changes`: applies the SSOT commit payload:
  Commit → ObjectInstanceGraphChange tree → Change(type) → ChangeDelta[].

Design goals:
- Honest: applies deltas as the SSOT ledger (no old/new storage).
- Typed: no duck-typed getattr introspection; operates on canonical ontology models.
- Value-tree aware: understands descriptor-driven `Attribute.value_root` trees.

Scope (v0):
- ClassInstance membership + Attribute value trees
- ClassInstanceRelationship membership

Not implemented (v0):
- Legacy Attribute.primitive / Attribute.enum paths (deprecated)
- Any DB lookups / lazy hydration (applier is pure in-memory)
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Mapping, MutableMapping
from typing import TypeVar, cast
from uuid import UUID

from aware_code.types import Json, JsonValue

# History Ontology
from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_delta import ChangeDelta
from aware_history_ontology.change.change_enums import ChangeType, ChangeDeltaKind

# Meta Ontology
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_change import AttributeChange
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as DescKind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange
from aware_meta_ontology.attribute.attribute_value_link import AttributeValueLink
from aware_meta_ontology.attribute.attribute_value_link_change import (
    AttributeValueLinkChange,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.class_.class_instance_relationship_change import (
    ClassInstanceRelationshipChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)

# Meta Runtime
from aware_meta.attribute.instance.value.validator import (
    canonicalize_attribute_value_tree,
    validate_attribute_value_tree_with_context,
)
from aware_meta.class_.instance.handlers import link_attribute
from aware_meta.graph.instance.diff import ObjectInstanceGraphDelta
from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind as K

# ORM
from aware_orm.models.orm_model import ORMModel
from aware_orm.session.autobind import disable_autobind


class OigDeltaApplyError(ValueError):
    pass


T_OrmModel = TypeVar("T_OrmModel", bound=ORMModel)


def apply_object_instance_graph_deltas(
    *,
    graph: ObjectInstanceGraph,
    deltas: Iterable[ObjectInstanceGraphDelta],
    attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None = None,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
) -> ObjectInstanceGraph:
    """
    Apply canonical OIG deltas to `graph` in-place.

    Args:
        graph: Target ObjectInstanceGraph snapshot to mutate.
        deltas: Root delta nodes produced by `diff_object_instance_graph`.
        attribute_configs_by_id: Required when deltas include Attribute/Value creation.

    Returns:
        The mutated graph (same instance).
    """
    attr_cfgs = attribute_configs_by_id or {}

    # Root deltas are emitted at member level (ClassInstances / Relationships).
    for delta in deltas:
        if delta.kind == K.class_instance:
            _apply_class_instance_delta(
                graph=graph,
                delta=delta,
                attribute_configs_by_id=attr_cfgs,
                class_configs_by_id=class_configs_by_id,
            )
            continue
        if delta.kind == K.relationship_instance:
            _apply_relationship_delta(graph=graph, delta=delta)
            continue
        raise OigDeltaApplyError(f"Unsupported root delta kind={delta.kind} op={delta.operation} path={delta.path_key}")

    # Deterministic ordering for stable downstream operations (hash/diff).
    graph.class_instances.sort(key=lambda ci: (str(ci.class_config_id), str(ci.id)))
    graph.class_instance_relationships.sort(
        key=lambda r: (
            str(r.class_config_relationship_id),
            str(r.source_class_instance_id),
            str(r.target_class_instance_id),
        )
    )
    return graph


def _apply_class_instance_delta(
    *,
    graph: ObjectInstanceGraph,
    delta: ObjectInstanceGraphDelta,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> None:
    existing = _find_by_id(graph.class_instances, delta.stable_id)

    if delta.operation == ChangeType.create:
        if existing is not None:
            raise OigDeltaApplyError(f"CREATE ClassInstance {delta.stable_id} already exists")
        class_config_id = _require_field_uuid(delta, "class_config_id")
        source_object_id = _require_field_uuid(delta, "source_object_id")
        with disable_autobind():
            ci = ClassInstance(
                id=delta.stable_id,
                object_instance_graph_id=graph.id,
                class_config_id=class_config_id,
                source_object_id=source_object_id,
                attributes=[],
            )
        graph.class_instances.append(ci)
        existing = ci

    elif delta.operation == ChangeType.update:
        if existing is None:
            raise OigDeltaApplyError(f"UPDATE ClassInstance {delta.stable_id} missing from base graph")
        for fd in delta.field_deltas:
            if fd.property == "class_config_id":
                existing.class_config_id = _as_uuid(fd.value)
            elif fd.property == "source_object_id":
                existing.source_object_id = _as_uuid(fd.value)
            else:
                raise OigDeltaApplyError(f"Unsupported ClassInstance field delta: {fd.property}")

    elif delta.operation == ChangeType.delete:
        if existing is None:
            raise OigDeltaApplyError(f"DELETE ClassInstance {delta.stable_id} missing from base graph")
        graph.class_instances = [ci for ci in graph.class_instances if ci.id != delta.stable_id]
        return  # Deletion implies subtree deletion; do not descend.

    else:
        raise OigDeltaApplyError(f"Unsupported operation for ClassInstance: {delta.operation}")

    # Apply attribute deltas (child membership under this ClassInstance).
    for attr_delta in delta.child_deltas.get(K.attribute, []):
        _apply_attribute_delta(
            class_instance=existing,
            delta=attr_delta,
            attribute_configs_by_id=attribute_configs_by_id,
            class_configs_by_id=class_configs_by_id,
        )

    # Stable ordering for deterministic serialization/diffs.
    _sort_class_instance_attributes(
        class_instance=existing,
        class_configs_by_id=class_configs_by_id,
    )


def _apply_attribute_delta(
    *,
    class_instance: ClassInstance,
    delta: ObjectInstanceGraphDelta,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> None:
    existing = _find_by_id(class_instance.attributes, delta.stable_id)

    if delta.operation == ChangeType.create:
        if existing is not None:
            raise OigDeltaApplyError(f"CREATE Attribute {delta.stable_id} already exists")
        attr_cfg_id = _require_field_uuid(delta, "attribute_config_id")
        cfg = attribute_configs_by_id.get(attr_cfg_id)
        if cfg is None:
            raise OigDeltaApplyError(f"AttributeConfig not provided for id={attr_cfg_id}")
        value_delta = _require_attribute_create_value_root_delta(delta)
        node = _create_value_node(delta=value_delta, type_descriptor=cfg.type_descriptor)
        _apply_value_node_children(
            node=node,
            delta=value_delta,
            attribute_configs_by_id=attribute_configs_by_id,
        )
        canonicalize_attribute_value_tree(node)
        validate_attribute_value_tree_with_context(node, class_configs_by_id=class_configs_by_id)
        with disable_autobind():
            attr = Attribute(
                id=delta.stable_id,
                owner_key=class_instance.source_object_id,
                attribute_config_id=attr_cfg_id,
                value_root=node,
                value_root_id=node.id,
            )
        _ = link_attribute(class_instance, attr)
        existing = attr

    elif delta.operation == ChangeType.update:
        if existing is None:
            raise OigDeltaApplyError(f"UPDATE Attribute {delta.stable_id} missing from base graph")
        for fd in delta.field_deltas:
            if fd.property == "attribute_config_id":
                existing.attribute_config_id = _as_uuid(fd.value)
            else:
                raise OigDeltaApplyError(f"Unsupported Attribute field delta: {fd.property}")

    elif delta.operation == ChangeType.delete:
        if existing is None:
            raise OigDeltaApplyError(f"DELETE Attribute {delta.stable_id} missing from base graph")
        class_instance.class_instance_attributes = [
            edge
            for edge in class_instance.class_instance_attributes
            if edge.attribute_id != delta.stable_id
            and getattr(edge.attribute, "id", None) != delta.stable_id
        ]
        return

    else:
        raise OigDeltaApplyError(f"Unsupported operation for Attribute: {delta.operation}")

    existing.owner_key = class_instance.source_object_id

    if delta.operation == ChangeType.update:
        value_deltas = delta.child_deltas.get(K.attribute_value, [])
        if len(value_deltas) > 1:
            raise OigDeltaApplyError(
                f"Attribute delta {delta.path_key} has {len(value_deltas)} value roots; expected <= 1"
            )
        if value_deltas:
            _apply_attribute_value_delta_under_attribute(
                attribute=existing,
                delta=value_deltas[0],
                attribute_configs_by_id=attribute_configs_by_id,
            )
        canonicalize_attribute_value_tree(existing.value_root)
        validate_attribute_value_tree_with_context(existing.value_root, class_configs_by_id=class_configs_by_id)
        existing.value_root_id = existing.value_root.id


def _apply_attribute_value_delta_under_attribute(
    *,
    attribute: Attribute,
    delta: ObjectInstanceGraphDelta,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
) -> None:
    attr_cfg = attribute_configs_by_id.get(attribute.attribute_config_id)
    if attr_cfg is None:
        raise OigDeltaApplyError(f"AttributeConfig not provided for id={attribute.attribute_config_id}")

    if delta.operation == ChangeType.create:
        raise OigDeltaApplyError(
            "CREATE value_root under an existing Attribute is not supported; create the Attribute with its value_root"
        )
    if delta.operation == ChangeType.delete:
        raise OigDeltaApplyError(
            "DELETE value_root is not supported when Attribute.value_root is required; delete the Attribute instead"
        )

    node = attribute.value_root
    if node.id != delta.stable_id:
        raise OigDeltaApplyError(f"value_root id mismatch: have={node.id} delta={delta.stable_id}")
    _apply_value_node_update(node=node, delta=delta)

    _apply_value_node_children(node=node, delta=delta, attribute_configs_by_id=attribute_configs_by_id)


def _apply_value_node_children(
    *,
    node: AttributeValue,
    delta: ObjectInstanceGraphDelta,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
) -> None:
    # Apply link deltas under this node.
    for link_delta in delta.child_deltas.get(K.attribute_value_link, []):
        _apply_value_link_delta(
            parent=node,
            delta=link_delta,
            attribute_configs_by_id=attribute_configs_by_id,
        )


def _apply_value_link_delta(
    *,
    parent: AttributeValue,
    delta: ObjectInstanceGraphDelta,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
) -> None:
    existing = _find_by_id(parent.child_links, delta.stable_id)

    if delta.operation == ChangeType.delete:
        if existing is None:
            raise OigDeltaApplyError(f"DELETE AttributeValueLink {delta.stable_id} missing from base tree")
        parent.child_links = [link for link in parent.child_links if link.id != delta.stable_id]
        return  # subtree deletion

    # For CREATE/UPDATE we need to resolve the link slot key and child descriptor.
    slot = _parse_value_link_slot(delta.path_key)
    child_desc = _resolve_child_descriptor(parent.type_descriptor, slot)

    if delta.operation == ChangeType.create:
        if existing is not None:
            raise OigDeltaApplyError(f"CREATE AttributeValueLink {delta.stable_id} already exists")
        child_delta = _require_single_child(delta, kind=K.attribute_value)
        child_node = _create_value_node(delta=child_delta, type_descriptor=child_desc)
        _apply_value_node_children(
            node=child_node,
            delta=child_delta,
            attribute_configs_by_id=attribute_configs_by_id,
        )
        with disable_autobind():
            link = AttributeValueLink(
                id=delta.stable_id,
                attribute_value_id=parent.id,
                role=slot.role,
                position=slot.position,
                identity_key=slot.identity_key,
                child=child_node,
                child_id=child_node.id,
            )
        parent.child_links.append(link)
        canonicalize_attribute_value_tree(parent)
        return

    if delta.operation != ChangeType.update:
        raise OigDeltaApplyError(f"Unsupported operation for AttributeValueLink: {delta.operation}")

    if existing is None:
        raise OigDeltaApplyError(f"UPDATE AttributeValueLink {delta.stable_id} missing from base tree")

    # Link has no scalar payload; apply child value deltas.
    child_delta = _require_single_child(delta, kind=K.attribute_value)
    child_node = existing.child

    # If the stable_id matches, update in-place; for CREATE under UPDATE we'd see CREATE op.
    if child_node.id != child_delta.stable_id:
        raise OigDeltaApplyError(
            f"AttributeValueLink child id mismatch: have={child_node.id} delta={child_delta.stable_id}"
        )
    _apply_value_node_update(node=child_node, delta=child_delta)
    _apply_value_node_children(
        node=child_node,
        delta=child_delta,
        attribute_configs_by_id=attribute_configs_by_id,
    )


def _apply_value_node_update(*, node: AttributeValue, delta: ObjectInstanceGraphDelta) -> None:
    if delta.operation not in (ChangeType.update, ChangeType.create):
        raise OigDeltaApplyError(f"Cannot apply field updates for op={delta.operation}")
    for fd in delta.field_deltas:
        if fd.property == "primitive_value":
            node.primitive_value = _wrap_primitive(fd.value)
        elif fd.property == "enum_option_id":
            node.enum_option_id = _as_uuid(fd.value) if fd.value is not None else None
        elif fd.property == "class_instance_id":
            node.class_instance_id = _as_uuid(fd.value) if fd.value is not None else None
        elif fd.property == "inline_value_instance_id":
            node.inline_value_instance_id = _as_uuid(fd.value) if fd.value is not None else None
        else:
            raise OigDeltaApplyError(f"Unsupported AttributeValue field delta: {fd.property}")


def _create_value_node(*, delta: ObjectInstanceGraphDelta, type_descriptor: AttributeTypeDescriptor) -> AttributeValue:
    if delta.operation != ChangeType.create:
        raise OigDeltaApplyError(f"_create_value_node requires CREATE delta, got {delta.operation}")

    with disable_autobind():
        node = AttributeValue(
            id=delta.stable_id,
            type_descriptor=type_descriptor,
            type_descriptor_id=type_descriptor.id,
            child_links=[],
            primitive_value=None,
            enum_option_id=None,
            class_instance_id=None,
            inline_value_instance_id=None,
        )
    _apply_value_node_update(node=node, delta=delta)
    return node


def _apply_relationship_delta(*, graph: ObjectInstanceGraph, delta: ObjectInstanceGraphDelta) -> None:
    existing = _find_by_id(graph.class_instance_relationships, delta.stable_id)

    if delta.operation == ChangeType.create:
        if existing is not None:
            raise OigDeltaApplyError(f"CREATE ClassInstanceRelationship {delta.stable_id} already exists")
        spec = _parse_relationship_path_key(delta.path_key)
        with disable_autobind():
            rel = ClassInstanceRelationship(
                id=delta.stable_id,
                object_instance_graph_id=graph.id,
                class_config_relationship_id=spec.relationship_id,
                source_class_instance_id=spec.source_id,
                target_class_instance_id=spec.target_id,
            )
        graph.class_instance_relationships.append(rel)
        return

    if delta.operation == ChangeType.delete:
        if existing is None:
            raise OigDeltaApplyError(f"DELETE ClassInstanceRelationship {delta.stable_id} missing from base graph")
        graph.class_instance_relationships = [r for r in graph.class_instance_relationships if r.id != delta.stable_id]
        return

    if delta.operation == ChangeType.update:
        # v0: relationships are structural; treat updates as unsupported.
        raise OigDeltaApplyError(f"UPDATE ClassInstanceRelationship not supported: {delta.stable_id}")

    raise OigDeltaApplyError(f"Unsupported operation for relationship: {delta.operation}")


# ----------------------------
# Parsing / helpers
# ----------------------------


def _find_by_id(items: Iterable[T_OrmModel], entity_id: UUID) -> T_OrmModel | None:
    for item in items:
        if item.id == entity_id:
            return item
    return None


def _sort_class_instance_attributes(
    *,
    class_instance: ClassInstance,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> None:
    def _edge_attribute_config_id(edge) -> UUID | None:
        attribute = edge.attribute
        if attribute is not None:
            return attribute.attribute_config_id
        return None

    def _edge_fallback_id(edge) -> str:
        if edge.attribute_id is not None:
            return str(edge.attribute_id)
        attribute = edge.attribute
        if attribute is not None:
            return str(attribute.id)
        return str(edge.id)

    class_config = None if class_configs_by_id is None else class_configs_by_id.get(class_instance.class_config_id)
    if class_config is None:
        class_instance.class_instance_attributes.sort(
            key=lambda edge: (
                str(_edge_attribute_config_id(edge) or ""),
                _edge_fallback_id(edge),
            )
        )
        return

    order_by_attribute_id: dict[UUID, tuple[int, str, str]] = {}
    for edge in class_config.class_config_attribute_configs:
        attribute_config_id = edge.attribute_config_id
        if attribute_config_id is None and edge.attribute_config is not None:
            attribute_config_id = edge.attribute_config.id
        if attribute_config_id is None:
            continue
        name = ""
        if edge.attribute_config is not None:
            name = edge.attribute_config.name or ""
        order_by_attribute_id[attribute_config_id] = (
            edge.position,
            name,
            str(attribute_config_id),
        )

    class_instance.class_instance_attributes.sort(
        key=lambda edge: order_by_attribute_id.get(
            _edge_attribute_config_id(edge),
            (1_000_000, "", _edge_fallback_id(edge)),
        )
    )


def _as_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        return UUID(value)
    raise OigDeltaApplyError(f"Expected UUID or str UUID, got {type(value).__name__}")


def _field_uuid(delta: ObjectInstanceGraphDelta, name: str) -> UUID | None:
    for fd in delta.field_deltas:
        if fd.property == name:
            if fd.value is None:
                return None
            return _as_uuid(fd.value)
    return None


def _require_field_uuid(delta: ObjectInstanceGraphDelta, name: str) -> UUID:
    value = _field_uuid(delta, name)
    if value is None:
        raise OigDeltaApplyError(f"Missing required field delta: {name} for {delta.kind} {delta.operation}")
    return value


def _wrap_primitive(value: object) -> Json | None:
    if value is None:
        return None
    json_value = _coerce_json_value(value)
    if isinstance(json_value, dict):
        return _json_object_from_mapping(json_value)
    return Json({"value": json_value})


def _coerce_json_value(value: object) -> JsonValue:
    if value is None:
        return None
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        list_items = cast(list[object], value)
        normalized_items: list[object] = []
        for item in list_items:
            normalized_items.append(_coerce_json_value(item))
        return normalized_items
    if isinstance(value, dict):
        normalized: dict[str, object] = {}
        for key, item in cast(dict[object, object], value).items():
            if not isinstance(key, str):
                raise OigDeltaApplyError(f"JSON object keys must be strings, got {type(key).__name__}")
            normalized[key] = _coerce_json_value(item)
        return normalized
    raise OigDeltaApplyError(f"Expected JSON-compatible primitive value, got {type(value).__name__}")


def _json_object_from_mapping(mapping: dict[str, object]) -> Json:
    json_object = Json()
    for key, value in mapping.items():
        json_object[key] = cast(JsonValue, value)
    return json_object


def _require_single_child(delta: ObjectInstanceGraphDelta, *, kind: K) -> ObjectInstanceGraphDelta:
    children = delta.child_deltas.get(kind, [])
    if len(children) != 1:
        raise OigDeltaApplyError(f"Expected exactly 1 child of kind={kind}, got {len(children)} for {delta.path_key}")
    return children[0]


def _require_attribute_create_value_root_delta(delta: ObjectInstanceGraphDelta) -> ObjectInstanceGraphDelta:
    value_delta = _require_single_child(delta, kind=K.attribute_value)
    if value_delta.operation != ChangeType.create:
        raise OigDeltaApplyError(
            f"CREATE Attribute {delta.stable_id} requires CREATE value_root delta, got {value_delta.operation}"
        )
    return value_delta


@dataclass(frozen=True)
class _ValueLinkSlot:
    role: Role
    position: int | None
    identity_key: str | None


def _parse_value_link_slot(path_key: str) -> _ValueLinkSlot:
    # Expected: link:<role>[:<pos|identity>]
    parts = path_key.split(":")
    if len(parts) < 2 or parts[0] != "link":
        raise OigDeltaApplyError(f"Invalid AttributeValueLink path_key: {path_key!r}")
    role_str = parts[1]
    role = _role_from_value(role_str)
    if len(parts) == 2:
        return _ValueLinkSlot(role=role, position=None, identity_key=None)
    slot = parts[2]
    if slot.isdigit():
        return _ValueLinkSlot(role=role, position=int(slot), identity_key=None)
    return _ValueLinkSlot(role=role, position=None, identity_key=slot)


def _role_from_value(value: str) -> Role:
    try:
        return Role(value)
    except ValueError as exc:
        raise OigDeltaApplyError(f"Unknown AttributeTypeDescriptorRole value: {value!r}") from exc


def _resolve_child_descriptor(parent_desc: AttributeTypeDescriptor, slot: _ValueLinkSlot) -> AttributeTypeDescriptor:
    kind = parent_desc.kind

    # COLLECTION/MAPPING: role selects; slot keys are instance-level identity, not descriptor positions.
    if kind in (DescKind.collection, DescKind.mapping):
        for link in parent_desc.child_links or []:
            if link.role == slot.role:
                return link.child
        raise OigDeltaApplyError(f"Descriptor missing role={slot.role} child for kind={kind}")

    # TUPLE/UNION: MEMBER position selects.
    if kind in (DescKind.tuple, DescKind.union):
        if slot.role != Role.member:
            raise OigDeltaApplyError(f"{kind} expects member links, got role={slot.role}")
        if slot.position is None:
            raise OigDeltaApplyError(f"{kind} member link missing position")
        for link in parent_desc.child_links or []:
            if link.role == Role.member and link.position == slot.position:
                return link.child
        raise OigDeltaApplyError(f"{kind} missing member position={slot.position} in descriptor")

    # Leaf nodes should not have children.
    raise OigDeltaApplyError(f"Leaf descriptor kind={kind} cannot have child links")


@dataclass(frozen=True)
class _RelationshipSpec:
    source_id: UUID
    target_id: UUID
    relationship_id: UUID


def _parse_relationship_path_key(path_key: str) -> _RelationshipSpec:
    # Expected: <src_uuid>-><tgt_uuid>:<relationship_uuid>
    try:
        src_tgt, rel_id_str = path_key.split(":", 1)
        src_str, tgt_str = src_tgt.split("->", 1)
        return _RelationshipSpec(
            source_id=UUID(src_str),
            target_id=UUID(tgt_str),
            relationship_id=UUID(rel_id_str),
        )
    except Exception as e:
        raise OigDeltaApplyError(f"Invalid relationship path_key: {path_key!r}") from e


class OigChangeApplyError(ValueError):
    pass


def apply_object_instance_graph_changes(
    *,
    graph: ObjectInstanceGraph,
    changes: Iterable[ObjectInstanceGraphChange],
    attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None = None,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
) -> ObjectInstanceGraph:
    """
    Apply canonical ObjectInstanceGraphChange trees to `graph` in-place.

    Commit payload SSOT:
    Commit → ObjectInstanceGraphChange tree → Change(type) → ChangeDelta[] (delta-only)
    """
    attr_cfgs = attribute_configs_by_id or {}
    class_instances_by_id: dict[UUID, ClassInstance] = {ci.id: ci for ci in graph.class_instances}

    for change_tree in changes:
        if change_tree.type == ObjectInstanceGraphChangeType.object_instance:
            for ci_change in change_tree.class_instance_changes:
                _apply_class_instance_change(
                    graph=graph,
                    change=ci_change,
                    attribute_configs_by_id=attr_cfgs,
                    class_configs_by_id=class_configs_by_id,
                    class_instances_by_id=class_instances_by_id,
                )
            continue

        if change_tree.type == ObjectInstanceGraphChangeType.object_instance_relationship:
            _apply_relationship_changes_bulk(
                graph=graph,
                changes=change_tree.class_instance_relationship_changes,
            )
            continue

        raise OigChangeApplyError(f"Unsupported ObjectInstanceGraphChangeType: {change_tree.type}")

    # Deterministic ordering for stable downstream operations (hash/diff).
    graph.class_instances.sort(key=lambda ci: (str(ci.class_config_id), str(ci.id)))
    graph.class_instance_relationships.sort(
        key=lambda r: (
            str(r.class_config_relationship_id),
            str(r.source_class_instance_id),
            str(r.target_class_instance_id),
        )
    )
    return graph


def _apply_class_instance_change(
    *,
    graph: ObjectInstanceGraph,
    change: ClassInstanceChange,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
    class_instances_by_id: MutableMapping[UUID, ClassInstance] | None = None,
) -> None:
    op = change.change.type

    ci_id = change.class_instance_id
    existing = (
        class_instances_by_id.get(ci_id)
        if class_instances_by_id is not None
        else _find_by_id(graph.class_instances, ci_id)
    )

    if op == ChangeType.create:
        if existing is not None:
            raise OigChangeApplyError(f"CREATE ClassInstance {ci_id} already exists")
        class_config_id = _require_scalar_uuid(change.change, "class_config_id")
        source_object_id = _require_scalar_uuid(change.change, "source_object_id")
        with disable_autobind():
            existing = ClassInstance(
                id=ci_id,
                object_instance_graph_id=graph.id,
                class_config_id=class_config_id,
                source_object_id=source_object_id,
                attributes=[],
            )
        graph.class_instances.append(existing)
        if class_instances_by_id is not None:
            class_instances_by_id[ci_id] = existing

    elif op == ChangeType.update:
        if existing is None:
            raise OigChangeApplyError(f"UPDATE ClassInstance {ci_id} missing from base graph")
        for cd in change.change.change_deltas:
            _apply_scalar_set_to_class_instance(ci=existing, delta=cd)

    elif op == ChangeType.delete:
        if existing is None:
            raise OigChangeApplyError(f"DELETE ClassInstance {ci_id} missing from base graph")
        graph.class_instances = [ci for ci in graph.class_instances if ci.id != ci_id]
        if class_instances_by_id is not None:
            _ = class_instances_by_id.pop(ci_id, None)
        return

    else:
        raise OigChangeApplyError(f"Unsupported ClassInstance change type: {op}")

    for attr_change in change.attribute_changes:
        _apply_attribute_change(
            class_instance=existing,
            change=attr_change,
            attribute_configs_by_id=attribute_configs_by_id,
            class_configs_by_id=class_configs_by_id,
        )

    _sort_class_instance_attributes(
        class_instance=existing,
        class_configs_by_id=class_configs_by_id,
    )


def _apply_scalar_set_to_class_instance(*, ci: ClassInstance, delta: ChangeDelta) -> None:
    if delta.kind != ChangeDeltaKind.scalar_set:
        raise OigChangeApplyError(f"Unsupported ChangeDeltaKind for ClassInstance: {delta.kind}")
    if delta.property == "class_config_id":
        ci.class_config_id = _as_uuid(_delta_value(delta))
        return
    if delta.property == "source_object_id":
        ci.source_object_id = _as_uuid(_delta_value(delta))
        return
    raise OigChangeApplyError(f"Unsupported ClassInstance delta property: {delta.property!r}")


def _apply_attribute_change(
    *,
    class_instance: ClassInstance,
    change: AttributeChange,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> None:
    op = change.change.type
    attr_id = change.attribute_id
    existing = _find_by_id(class_instance.attributes, attr_id)

    if op == ChangeType.create:
        if existing is not None:
            raise OigChangeApplyError(f"CREATE Attribute {attr_id} already exists")
        attr_cfg_id = _require_scalar_uuid(change.change, "attribute_config_id")
        cfg = attribute_configs_by_id.get(attr_cfg_id)
        if cfg is None:
            raise OigChangeApplyError(
                "Missing AttributeConfig for "
                + f"attribute_config_id={attr_cfg_id} "
                + f"class_instance_id={class_instance.id} "
                + f"class_config_id={class_instance.class_config_id} "
                + f"attribute_id={attr_id}"
            )
        if change.value_root_change is None:
            raise OigChangeApplyError(
                f"CREATE Attribute {attr_id} requires value_root_change when Attribute.value_root is required"
            )
        if change.value_root_change.change.type != ChangeType.create:
            raise OigChangeApplyError(
                "CREATE Attribute "
                + str(attr_id)
                + " requires CREATE value_root_change, got "
                + str(change.value_root_change.change.type)
            )

        node = _create_value_node_from_change(change=change.value_root_change, type_descriptor=cfg.type_descriptor)
        _apply_value_node_children_from_change(
            node=node,
            change=change.value_root_change,
            attribute_configs_by_id=attribute_configs_by_id,
        )
        canonicalize_attribute_value_tree(node)
        validate_attribute_value_tree_with_context(node, class_configs_by_id=class_configs_by_id)
        with disable_autobind():
            existing = Attribute(
                id=attr_id,
                owner_key=class_instance.source_object_id,
                attribute_config_id=attr_cfg_id,
                value_root=node,
                value_root_id=node.id,
            )
        _ = link_attribute(class_instance, existing)

    elif op == ChangeType.update:
        if existing is None:
            raise OigChangeApplyError(f"UPDATE Attribute {attr_id} missing from base graph")
        for cd in change.change.change_deltas:
            if cd.kind != ChangeDeltaKind.scalar_set:
                raise OigChangeApplyError(f"Unsupported ChangeDeltaKind for Attribute: {cd.kind}")
            if cd.property == "attribute_config_id":
                existing.attribute_config_id = _as_uuid(_delta_value(cd))
                continue
            raise OigChangeApplyError(f"Unsupported Attribute delta property: {cd.property!r}")

    elif op == ChangeType.delete:
        if existing is None:
            raise OigChangeApplyError(f"DELETE Attribute {attr_id} missing from base graph")
        class_instance.class_instance_attributes = [
            edge
            for edge in class_instance.class_instance_attributes
            if edge.attribute_id != attr_id and getattr(edge.attribute, "id", None) != attr_id
        ]
        return

    else:
        raise OigChangeApplyError(f"Unsupported Attribute change type: {op}")

    existing.owner_key = class_instance.source_object_id

    if change.value_root_change is not None:
        if op != ChangeType.create:
            _apply_attribute_value_change_under_attribute(
                attribute=existing,
                change=change.value_root_change,
                attribute_configs_by_id=attribute_configs_by_id,
                class_configs_by_id=class_configs_by_id,
            )


def _apply_attribute_value_change_under_attribute(
    *,
    attribute: Attribute,
    change: AttributeValueChange,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> None:
    op = change.change.type

    cfg = attribute_configs_by_id.get(attribute.attribute_config_id)
    if cfg is None:
        raise OigChangeApplyError(
            "Missing AttributeConfig for "
            + f"attribute_config_id={attribute.attribute_config_id} "
            + f"owner_key={attribute.owner_key} "
            + f"attribute_id={attribute.id}"
        )

    if op == ChangeType.create:
        raise OigChangeApplyError(
            "CREATE value_root under an existing Attribute is not supported; create the Attribute with its value_root"
        )

    elif op == ChangeType.update:
        node = attribute.value_root
        if node.id != change.attribute_value_id:
            raise OigChangeApplyError(f"value_root id mismatch: have={node.id} change={change.attribute_value_id}")
        _apply_value_node_update_from_change(node=node, change=change)

    elif op == ChangeType.delete:
        raise OigChangeApplyError(
            "DELETE value_root is not supported when Attribute.value_root is required; delete the Attribute instead"
        )

    else:
        raise OigChangeApplyError(f"Unsupported AttributeValue change type: {op}")

    _apply_value_node_children_from_change(node=node, change=change, attribute_configs_by_id=attribute_configs_by_id)
    canonicalize_attribute_value_tree(node)
    validate_attribute_value_tree_with_context(node, class_configs_by_id=class_configs_by_id)
    attribute.value_root_id = node.id


def _apply_value_node_children_from_change(
    *,
    node: AttributeValue,
    change: AttributeValueChange,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
) -> None:
    for link_change in change.attribute_value_link_changes:
        _apply_value_link_change(
            parent=node,
            change=link_change,
            attribute_configs_by_id=attribute_configs_by_id,
        )


def _apply_value_link_change(
    *,
    parent: AttributeValue,
    change: AttributeValueLinkChange,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
) -> None:
    op = change.change.type

    existing = _find_by_id(parent.child_links, change.attribute_value_link_id)

    if op == ChangeType.delete:
        if existing is None:
            raise OigChangeApplyError(
                f"DELETE AttributeValueLink {change.attribute_value_link_id} missing from base tree"
            )
        parent.child_links = [link for link in parent.child_links if link.id != change.attribute_value_link_id]
        return

    if op == ChangeType.create:
        role, pos, ident = _link_slot_from_change(change.change)
        slot = _ValueLinkSlot(role=role, position=pos, identity_key=ident)
        child_desc = _resolve_child_descriptor(parent.type_descriptor, slot)
        if existing is not None:
            raise OigChangeApplyError(f"CREATE AttributeValueLink {change.attribute_value_link_id} already exists")
        if change.child_attribute_value_change is None:
            raise OigChangeApplyError("CREATE AttributeValueLink missing child_attribute_value_change")

        child_node = _create_value_node_from_change(
            change=change.child_attribute_value_change, type_descriptor=child_desc
        )
        _apply_value_node_children_from_change(
            node=child_node,
            change=change.child_attribute_value_change,
            attribute_configs_by_id=attribute_configs_by_id,
        )
        with disable_autobind():
            link = AttributeValueLink(
                id=change.attribute_value_link_id,
                attribute_value_id=parent.id,
                role=slot.role,
                position=slot.position,
                identity_key=slot.identity_key,
                child=child_node,
                child_id=child_node.id,
            )
        parent.child_links.append(link)
        canonicalize_attribute_value_tree(parent)
        return

    if op != ChangeType.update:
        raise OigChangeApplyError(f"Unsupported operation for AttributeValueLink: {op}")

    if existing is None:
        raise OigChangeApplyError(f"UPDATE AttributeValueLink {change.attribute_value_link_id} missing from base tree")
    if change.child_attribute_value_change is None:
        raise OigChangeApplyError("UPDATE AttributeValueLink missing child_attribute_value_change")

    child_node = existing.child
    if child_node.id != change.child_attribute_value_change.attribute_value_id:
        raise OigChangeApplyError(
            "AttributeValueLink child id mismatch: "
            + f"have={child_node.id} "
            + f"change={change.child_attribute_value_change.attribute_value_id}"
        )
    _apply_value_node_update_from_change(node=child_node, change=change.child_attribute_value_change)
    _apply_value_node_children_from_change(
        node=child_node,
        change=change.child_attribute_value_change,
        attribute_configs_by_id=attribute_configs_by_id,
    )


def _apply_value_node_update_from_change(*, node: AttributeValue, change: AttributeValueChange) -> None:
    op = change.change.type
    if op not in (ChangeType.update, ChangeType.create):
        raise OigChangeApplyError(f"Cannot apply field updates for op={op}")

    for cd in change.change.change_deltas:
        if cd.kind != ChangeDeltaKind.scalar_set:
            raise OigChangeApplyError(f"Unsupported ChangeDeltaKind for AttributeValue: {cd.kind}")
        raw = _delta_value(cd)
        if cd.property == "primitive_value":
            node.primitive_value = _wrap_primitive(raw)
        elif cd.property == "enum_option_id":
            node.enum_option_id = _as_uuid(raw) if raw is not None else None
        elif cd.property == "class_instance_id":
            node.class_instance_id = _as_uuid(raw) if raw is not None else None
        elif cd.property == "inline_value_instance_id":
            node.inline_value_instance_id = _as_uuid(raw) if raw is not None else None
        else:
            raise OigChangeApplyError(f"Unsupported AttributeValue delta property: {cd.property!r}")


def _create_value_node_from_change(
    *, change: AttributeValueChange, type_descriptor: AttributeTypeDescriptor
) -> AttributeValue:
    if change.change.type != ChangeType.create:
        raise OigChangeApplyError(f"_create_value_node_from_change requires CREATE, got {change.change.type}")

    with disable_autobind():
        node = AttributeValue(
            id=change.attribute_value_id,
            type_descriptor=type_descriptor,
            type_descriptor_id=type_descriptor.id,
            child_links=[],
            primitive_value=None,
            enum_option_id=None,
            class_instance_id=None,
            inline_value_instance_id=None,
        )
    _apply_value_node_update_from_change(node=node, change=change)
    return node


def _relationship_key(rel: ClassInstanceRelationship) -> tuple[UUID, UUID, UUID]:
    return (
        rel.class_config_relationship_id,
        rel.source_class_instance_id,
        rel.target_class_instance_id,
    )


def _apply_relationship_changes_bulk(
    *,
    graph: ObjectInstanceGraph,
    changes: Iterable[ClassInstanceRelationshipChange],
) -> None:
    """Apply relationship changes with key-indexed state to avoid repeated full-list scans."""
    rels_by_key: dict[tuple[UUID, UUID, UUID], list[ClassInstanceRelationship]] = {}
    for rel in graph.class_instance_relationships:
        rels_by_key.setdefault(_relationship_key(rel), []).append(rel)

    for change in changes:
        op = change.change.type
        key = (
            change.class_config_relationship_id,
            change.source_class_instance_id,
            change.target_class_instance_id,
        )
        existing = rels_by_key.get(key, [])

        if op == ChangeType.create:
            if existing:
                continue
            with disable_autobind():
                rel = ClassInstanceRelationship(
                    object_instance_graph_id=graph.id,
                    class_config_relationship_id=key[0],
                    source_class_instance_id=key[1],
                    target_class_instance_id=key[2],
                )
            rels_by_key[key] = [rel]
            continue

        if op == ChangeType.delete:
            if not existing:
                raise OigChangeApplyError(f"DELETE relationship missing: {key}")
            rels_by_key[key] = []
            continue

        if op == ChangeType.update:
            raise OigChangeApplyError("UPDATE relationship not supported (v0)")

        raise OigChangeApplyError(f"Unsupported relationship change type: {op}")

    graph.class_instance_relationships = [rel for rels in rels_by_key.values() for rel in rels]


def _delta_value(delta: ChangeDelta) -> JsonValue:
    return delta.payload.get("value")


def _scalar_uuid(change: Change, name: str) -> UUID | None:
    for d in change.change_deltas:
        if d.kind == ChangeDeltaKind.scalar_set and d.property == name:
            raw = _delta_value(d)
            if raw is None:
                return None
            return _as_uuid(raw)
    return None


def _require_scalar_uuid(change: Change, name: str) -> UUID:
    value = _scalar_uuid(change, name)
    if value is None:
        raise OigChangeApplyError(f"Missing required SCALAR_SET delta: {name}")
    return value


def _link_slot_from_change(change: Change) -> tuple[Role, int | None, str | None]:
    role_raw = None
    pos: int | None = None
    ident: str | None = None
    for d in change.change_deltas:
        if d.kind != ChangeDeltaKind.scalar_set:
            continue
        if d.property == "role":
            role_raw = _delta_value(d)
        elif d.property == "position":
            raw = _delta_value(d)
            pos = _as_int(raw) if raw is not None else None
        elif d.property == "identity_key":
            raw = _delta_value(d)
            ident = str(raw) if raw is not None else None
    if role_raw is None:
        raise OigChangeApplyError("AttributeValueLinkChange missing role")
    role = _role_from_value(str(role_raw))
    return role, pos, ident


def _as_int(value: object) -> int:
    if isinstance(value, bool):
        raise OigChangeApplyError("Boolean is not a valid integer slot position")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError as exc:
            raise OigChangeApplyError(f"Expected integer slot position, got {value!r}") from exc
    raise OigChangeApplyError(f"Expected integer slot position, got {type(value).__name__}")


__all__ = [
    "OigDeltaApplyError",
    "apply_object_instance_graph_deltas",
    "OigChangeApplyError",
    "apply_object_instance_graph_changes",
]
