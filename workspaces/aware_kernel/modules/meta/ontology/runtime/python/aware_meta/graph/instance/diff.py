"""Canonical OIG-to-OIG diff via Meta graph support.

The diff engine is Meta graph support (tree diff + reconciliation). For canonical
OIG evolution, the SSOT commit payload is:

Commit → ObjectInstanceGraphChange tree → Change(type) → ChangeDelta[] (delta-only)

This module provides:
- an internal typed delta tree (`ObjectInstanceGraphDelta`) used as an
  implementation detail of the diff protocol
- a conversion helper to produce the canonical Change graph payload for commits
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Final, Literal, TypeAlias, cast
from collections.abc import Mapping
from uuid import UUID

# Kernel Graph Ontology
from aware_code.types import Json, JsonValue
from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_delta import ChangeDelta
from aware_history_ontology.change.change_enums import ChangeType, ChangeDeltaKind
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_change import AttributeChange
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange
from aware_meta_ontology.attribute.attribute_value_link import AttributeValueLink
from aware_meta_ontology.attribute.attribute_value_link_change import (
    AttributeValueLinkChange,
)
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
from aware_meta.graph.instance.member import ObjectInstanceGraphMember
from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind
from aware_meta.graph.instance.topology import ObjectInstanceGraphTopology

# Meta graph support
from aware_meta.graph.support.member import GraphMember, T_Kind
from aware_meta.graph.support.node import GraphNode
from aware_meta.graph.support.protocols.diff.container import TreeContainer
from aware_meta.graph.support.protocols.diff.diff import diff as graph_diff
from aware_meta.graph.support.protocols.diff.protocol import (
    FieldChange,
    GraphChangeProtocol,
    GraphDiffProtocol,
)
from typing_extensions import override


FieldDeltaOp: TypeAlias = Literal["set"]
FieldDeltaValue: TypeAlias = UUID | JsonValue


class DeltaOp:
    """Field delta operation rail (v0: scalar SET only)."""

    SET: Final[FieldDeltaOp] = "set"


CREATE_CHANGE_TYPE = ChangeType("create")
UPDATE_CHANGE_TYPE = ChangeType("update")
DELETE_CHANGE_TYPE = ChangeType("delete")


@dataclass(frozen=True)
class FieldDelta:
    """
    Delta-driven field change.

    This intentionally does not store (old_value, new_value). The new value is
    sufficient to apply the delta given the prior graph state.
    """

    property: str
    op: FieldDeltaOp
    value: FieldDeltaValue


@dataclass
class ObjectInstanceGraphDelta:
    """
    Delta node produced by the canonical OIG diff.

    - `stable_id` is the reconciled identity (maps new ids to old ids when possible).
    - `entity_id` is the id of the member instance contained in this delta (new id for CREATE/UPDATE).
    - `path_key` is the member-local semantic key (useful for debugging & tests).
    """

    kind: ObjectInstanceGraphMemberKind
    stable_id: UUID
    entity_id: UUID
    operation: ChangeType
    path_key: str
    field_deltas: list[FieldDelta]
    child_deltas: dict[ObjectInstanceGraphMemberKind, list["ObjectInstanceGraphDelta"]]


class _OigDiffProtocol(GraphDiffProtocol):
    """
    GraphDiffProtocol for ObjectInstanceGraph.

    We flatten the container so root-level diffs are emitted at the member level
    (ClassInstances / Relationships), not the graph wrapper.
    """

    @override
    def add_graph_specific_children_fn(
        self,
        graph: GraphMember[T_Kind],
        root: TreeContainer[T_Kind],
    ) -> None:
        if not isinstance(graph, ObjectInstanceGraphMember):
            return

        graph_children = cast(list[GraphNode[object, T_Kind]], root.children)
        if not graph_children:
            return

        graph_nodes: list[GraphNode[object, T_Kind]] = []
        for child in graph_children:
            if not isinstance(child.entity, ObjectInstanceGraphMember):
                continue
            graph_nodes.append(child)
        if not graph_nodes:
            return

        graph_node = graph_nodes[0]
        graph_node_children = graph_node.children
        root.children = list(graph_node_children)

    @override
    def get_create_operation(self) -> ChangeType:
        return CREATE_CHANGE_TYPE

    @override
    def get_update_operation(self) -> ChangeType:
        return UPDATE_CHANGE_TYPE

    @override
    def get_delete_operation(self) -> ChangeType:
        return DELETE_CHANGE_TYPE


class _OigDeltaProtocol(
    GraphChangeProtocol[ObjectInstanceGraphMemberKind, ObjectInstanceGraphDelta]
):
    @override
    def build_node_change(
        self,
        member: GraphMember[ObjectInstanceGraphMemberKind],
        stable_id: UUID,
        operation: ChangeType,
        child_changes: Mapping[ObjectInstanceGraphMemberKind, list[object]],
        field_changes: list[FieldChange],
    ) -> ObjectInstanceGraphDelta:
        entity_id = member.get_id()
        if entity_id is None:
            raise ValueError(f"Cannot emit delta for member without id: {member!r}")

        field_deltas = [_field_delta_from_graph_change(fc) for fc in field_changes]

        typed_children: dict[
            ObjectInstanceGraphMemberKind, list[ObjectInstanceGraphDelta]
        ] = {}
        for k, v in child_changes.items():
            deltas = [c for c in v if isinstance(c, ObjectInstanceGraphDelta)]
            if deltas:
                typed_children[k] = deltas

        return ObjectInstanceGraphDelta(
            kind=member.node_kind(),
            stable_id=stable_id,
            entity_id=entity_id,
            operation=operation,
            path_key=member.get_path_key(),
            field_deltas=field_deltas,
            child_deltas=typed_children,
        )


def diff_object_instance_graph(
    old: ObjectInstanceGraph,
    new: ObjectInstanceGraph,
) -> list[ObjectInstanceGraphDelta]:
    """
    Compute canonical deltas between two OIG snapshots.

    This is a structural + content diff driven by the canonical topology:
    - ClassInstances + Attributes + descriptor-driven AttributeValue trees
    - ClassInstanceRelationships as separate members
    """
    old_member = ObjectInstanceGraphMember(object_instance_graph=old)
    new_member = ObjectInstanceGraphMember(object_instance_graph=new)

    topology = ObjectInstanceGraphTopology()
    diff_protocol = _OigDiffProtocol()
    change_protocol = _OigDeltaProtocol()

    return graph_diff(
        old_graph=old_member,
        new_graph=new_member,
        protocol=diff_protocol,
        topology=topology,
        change_protocol=change_protocol,
    )


def diff_object_instance_graph_changes(
    old: ObjectInstanceGraph,
    new: ObjectInstanceGraph,
    *,
    object_instance_graph_identity_id: UUID,
    created_at: datetime | None = None,
) -> list[ObjectInstanceGraphChange]:
    """
    Compute canonical ObjectInstanceGraphChange trees between two OIG snapshots.

    Invariant (v0): both snapshots must refer to the same logical OIG (same `id`).
    """
    if old.id != new.id:
        raise ValueError(
            f"diff_object_instance_graph_changes requires same graph id; old={old.id} new={new.id}"
        )

    deltas = diff_object_instance_graph(old=old, new=new)
    if not deltas:
        return []

    effective_created_at = created_at or datetime.now(timezone.utc)
    builder = _ChangeGraphBuilder(old=old, new=new, created_at=effective_created_at)

    class_instance_changes: list[ClassInstanceChange] = []
    relationship_changes: list[ClassInstanceRelationshipChange] = []

    for d in deltas:
        if d.kind == ObjectInstanceGraphMemberKind.class_instance:
            class_instance_change = builder.class_instance_change_from_delta(d)
            if class_instance_change is not None:
                class_instance_changes.append(class_instance_change)
            continue
        if d.kind == ObjectInstanceGraphMemberKind.relationship_instance:
            relationship_changes.append(builder.relationship_change_from_delta(d))
            continue
        raise ValueError(f"Unsupported root delta kind={d.kind}")

    out: list[ObjectInstanceGraphChange] = []
    if class_instance_changes:
        root_change = _build_change(
            key="root:object_instance:update",
            change_type=UPDATE_CHANGE_TYPE,
            field_deltas=[],
            created_at=effective_created_at,
        )
        out.append(
            ObjectInstanceGraphChange(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=old.id,
                type=ObjectInstanceGraphChangeType.object_instance,
                change=root_change,
                change_id=root_change.id,
                class_instance_changes=class_instance_changes,
                class_instance_relationship_changes=[],
            )
        )
    if relationship_changes:
        root_change = _build_change(
            key="root:object_instance_relationship:update",
            change_type=UPDATE_CHANGE_TYPE,
            field_deltas=[],
            created_at=effective_created_at,
        )
        out.append(
            ObjectInstanceGraphChange(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=old.id,
                type=ObjectInstanceGraphChangeType.object_instance_relationship,
                change=root_change,
                change_id=root_change.id,
                class_instance_changes=[],
                class_instance_relationship_changes=relationship_changes,
            )
        )
    return out


def build_object_instance_graph_seed_changes(
    *,
    new: ObjectInstanceGraph,
    object_instance_graph_identity_id: UUID,
    before: ObjectInstanceGraph | None = None,
    created_at: datetime | None = None,
) -> list[ObjectInstanceGraphChange]:
    """Build deterministic root UPDATE plus CREATE changes for an OIG seed."""
    effective_created_at = created_at or datetime.now(timezone.utc)
    if before is not None:
        return diff_object_instance_graph_changes(
            old=before,
            new=new,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            created_at=effective_created_at,
        )

    before_class_instance_ids = {
        class_instance.id
        for class_instance in (before.class_instances if before is not None else ())
    }

    class_instance_changes: list[ClassInstanceChange] = []
    for class_instance in sorted(
        new.class_instances,
        key=lambda item: (str(item.class_config_id), str(item.id)),
    ):
        class_instance_changes.append(
            _class_instance_seed_change(
                class_instance=class_instance,
                operation=(
                    UPDATE_CHANGE_TYPE
                    if class_instance.id in before_class_instance_ids
                    else CREATE_CHANGE_TYPE
                ),
                created_at=effective_created_at,
            )
        )

    relationship_changes: list[ClassInstanceRelationshipChange] = []
    for relationship in sorted(
        new.class_instance_relationships,
        key=lambda item: (
            str(item.class_config_relationship_id),
            str(item.source_class_instance_id),
            str(item.target_class_instance_id),
        ),
    ):
        relationship_changes.append(
            _relationship_create_change(
                relationship=relationship,
                created_at=effective_created_at,
            )
        )

    out: list[ObjectInstanceGraphChange] = []
    if class_instance_changes:
        root_change = _build_change(
            key="root:object_instance:create",
            change_type=UPDATE_CHANGE_TYPE,
            field_deltas=[],
            created_at=effective_created_at,
        )
        out.append(
            ObjectInstanceGraphChange(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=new.id,
                type=ObjectInstanceGraphChangeType.object_instance,
                change=root_change,
                change_id=root_change.id,
                class_instance_changes=class_instance_changes,
                class_instance_relationship_changes=[],
            )
        )
    if relationship_changes:
        root_change = _build_change(
            key="root:object_instance_relationship:create",
            change_type=UPDATE_CHANGE_TYPE,
            field_deltas=[],
            created_at=effective_created_at,
        )
        out.append(
            ObjectInstanceGraphChange(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=new.id,
                type=ObjectInstanceGraphChangeType.object_instance_relationship,
                change=root_change,
                change_id=root_change.id,
                class_instance_changes=[],
                class_instance_relationship_changes=relationship_changes,
            )
        )
    return out


def _build_change(
    *,
    key: str,
    change_type: ChangeType,
    field_deltas: list[FieldDelta],
    created_at: datetime,
) -> Change:
    change = Change(
        key=key,
        type=change_type,
        change_deltas=[],
        created_at=created_at,
    )
    if not field_deltas:
        return change

    deltas: list[ChangeDelta] = []
    for position, fd in enumerate(field_deltas):
        deltas.append(
            ChangeDelta(
                change_id=change.id,
                position=position,
                property=fd.property,
                kind=ChangeDeltaKind.scalar_set,
                payload=Json({"value": _field_delta_payload_value(fd.value)}),
            )
        )
    change.change_deltas = deltas
    return change


def _field_delta_from_graph_change(field_change: FieldChange) -> FieldDelta:
    new_value = cast(object, field_change.new_value)
    return FieldDelta(
        property=field_change.property,
        op=DeltaOp.SET,
        value=_coerce_field_delta_value(new_value),
    )


def _coerce_field_delta_value(value: object) -> FieldDeltaValue:
    if isinstance(value, UUID):
        return value
    return _coerce_json_value(value)


def _field_delta_payload_value(value: FieldDeltaValue) -> JsonValue:
    if isinstance(value, UUID):
        return str(value)
    return value


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
                raise TypeError(
                    f"Field delta JSON object keys must be strings, got {type(key).__name__}"
                )
            normalized[key] = _coerce_json_value(item)
        return normalized
    raise TypeError(f"Unsupported field delta value type: {type(value).__name__}")


def _class_instance_seed_change(
    *,
    class_instance: ClassInstance,
    operation: ChangeType,
    created_at: datetime,
) -> ClassInstanceChange:
    field_deltas = [
        FieldDelta(
            property="class_config_id",
            op=DeltaOp.SET,
            value=class_instance.class_config_id,
        ),
        FieldDelta(
            property="source_object_id",
            op=DeltaOp.SET,
            value=class_instance.source_object_id,
        ),
    ]
    change = _build_change(
        key=(
            f"class_instance:{class_instance.class_config_id}:"
            f"{class_instance.id}:{operation.value}"
        ),
        change_type=operation,
        field_deltas=field_deltas,
        created_at=created_at,
    )
    class_instance_change = ClassInstanceChange(
        class_instance_id=class_instance.id,
        change=change,
        change_id=change.id,
        attribute_changes=[],
    )
    attributes_by_id: dict[UUID, Attribute] = {}
    for attribute in class_instance.attributes:
        existing = attributes_by_id.get(attribute.id)
        if existing is not None:
            if (
                existing.attribute_config_id != attribute.attribute_config_id
                or existing.value_root_id != attribute.value_root_id
            ):
                raise ValueError(
                    "Conflicting duplicate Attribute in ClassInstance seed: "
                    + f"class_instance_id={class_instance.id} "
                    + f"attribute_id={attribute.id}"
                )
            continue
        attributes_by_id[attribute.id] = attribute
    for attribute in sorted(
        attributes_by_id.values(),
        key=lambda item: (str(item.attribute_config_id), str(item.id)),
    ):
        class_instance_change.attribute_changes.append(
            _attribute_create_change(
                attribute=attribute,
                parent=class_instance_change,
                created_at=created_at,
            )
        )
    return class_instance_change


def _attribute_create_change(
    *,
    attribute: Attribute,
    parent: ClassInstanceChange,
    created_at: datetime,
) -> AttributeChange:
    change = _build_change(
        key=f"attribute:attr:{attribute.attribute_config_id}:create",
        change_type=CREATE_CHANGE_TYPE,
        field_deltas=[
            FieldDelta(
                property="attribute_config_id",
                op=DeltaOp.SET,
                value=attribute.attribute_config_id,
            )
        ],
        created_at=created_at,
    )
    value_root_change = (
        None
        if attribute.value_root is None
        else _attribute_value_create_change(
            value=attribute.value_root,
            created_at=created_at,
        )
    )
    return AttributeChange(
        attribute_id=attribute.id,
        class_instance_change_id=parent.id,
        change=change,
        change_id=change.id,
        value_root_change=value_root_change,
        value_root_change_id=(
            None if value_root_change is None else value_root_change.id
        ),
    )


def _attribute_value_create_change(
    *,
    value: AttributeValue,
    created_at: datetime,
) -> AttributeValueChange:
    field_deltas: list[FieldDelta] = []
    primitive_value = _attribute_value_primitive_payload(value)
    if primitive_value is not None:
        field_deltas.append(
            FieldDelta(
                property="primitive_value",
                op=DeltaOp.SET,
                value=primitive_value,
            )
        )
    if value.enum_option_id is not None:
        field_deltas.append(
            FieldDelta(
                property="enum_option_id",
                op=DeltaOp.SET,
                value=value.enum_option_id,
            )
        )
    if value.inline_value_instance_id is not None:
        field_deltas.append(
            FieldDelta(
                property="inline_value_instance_id",
                op=DeltaOp.SET,
                value=value.inline_value_instance_id,
            )
        )
    elif value.inline_value_instance is not None:
        field_deltas.append(
            FieldDelta(
                property="inline_value_instance_id",
                op=DeltaOp.SET,
                value=value.inline_value_instance.id,
            )
        )
    elif value.class_instance_id is not None:
        field_deltas.append(
            FieldDelta(
                property="class_instance_id",
                op=DeltaOp.SET,
                value=value.class_instance_id,
            )
        )

    change = _build_change(
        key="attribute_value:value:create",
        change_type=CREATE_CHANGE_TYPE,
        field_deltas=field_deltas,
        created_at=created_at,
    )
    value_change = AttributeValueChange(
        attribute_value_id=value.id,
        change=change,
        change_id=change.id,
        attribute_value_link_changes=[],
    )
    for link in sorted(
        value.child_links,
        key=lambda item: (
            item.role.value,
            item.position if item.position is not None else -1,
            item.identity_key or "",
            str(item.id),
        ),
    ):
        value_change.attribute_value_link_changes.append(
            _attribute_value_link_create_change(
                link=link,
                parent=value_change,
                created_at=created_at,
            )
        )
    return value_change


def _attribute_value_link_create_change(
    *,
    link: AttributeValueLink,
    parent: AttributeValueChange,
    created_at: datetime,
) -> AttributeValueLinkChange:
    field_deltas = [
        FieldDelta(
            property="role",
            op=DeltaOp.SET,
            value=link.role.value,
        )
    ]
    if link.position is not None:
        field_deltas.append(
            FieldDelta(
                property="position",
                op=DeltaOp.SET,
                value=link.position,
            )
        )
    if link.identity_key is not None:
        field_deltas.append(
            FieldDelta(
                property="identity_key",
                op=DeltaOp.SET,
                value=link.identity_key,
            )
        )
    change = _build_change(
        key=f"attribute_value_link:{_attribute_value_link_path_key(link)}:create",
        change_type=CREATE_CHANGE_TYPE,
        field_deltas=field_deltas,
        created_at=created_at,
    )
    child_change = (
        None
        if link.child is None
        else _attribute_value_create_change(
            value=link.child,
            created_at=created_at,
        )
    )
    return AttributeValueLinkChange(
        attribute_value_change_id=parent.id,
        attribute_value_link_id=link.id,
        change=change,
        change_id=change.id,
        child_attribute_value_change=child_change,
        child_attribute_value_change_id=(
            None if child_change is None else child_change.id
        ),
    )


def _relationship_create_change(
    *,
    relationship: ClassInstanceRelationship,
    created_at: datetime,
) -> ClassInstanceRelationshipChange:
    change = _build_change(
        key=(
            "relationship:"
            f"{relationship.source_class_instance_id}->{relationship.target_class_instance_id}:"
            f"{relationship.class_config_relationship_id}:create"
        ),
        change_type=CREATE_CHANGE_TYPE,
        field_deltas=[],
        created_at=created_at,
    )
    return ClassInstanceRelationshipChange(
        change=change,
        change_id=change.id,
        class_config_relationship_id=relationship.class_config_relationship_id,
        source_class_instance_id=relationship.source_class_instance_id,
        target_class_instance_id=relationship.target_class_instance_id,
    )


def _attribute_value_primitive_payload(value: AttributeValue) -> JsonValue | None:
    raw = value.primitive_value
    if isinstance(raw, dict) and set(raw.keys()) == {"value"}:
        return _coerce_json_value(raw.get("value"))
    return _coerce_json_value(raw)


def _attribute_value_link_path_key(link: AttributeValueLink) -> str:
    role = link.role.value
    if link.identity_key is not None:
        return f"link:{role}:{link.identity_key}"
    if link.position is not None:
        return f"link:{role}:{link.position}"
    return f"link:{role}"


@dataclass(slots=True)
class _ChangeGraphBuilder:
    old: ObjectInstanceGraph
    new: ObjectInstanceGraph
    created_at: datetime
    _old_class_instances_by_id: dict[UUID, ClassInstance] = field(
        init=False, default_factory=dict
    )
    _new_class_instances_by_id: dict[UUID, ClassInstance] = field(
        init=False, default_factory=dict
    )
    _old_attributes_by_id: dict[UUID, Attribute] = field(
        init=False, default_factory=dict
    )
    _new_attributes_by_id: dict[UUID, Attribute] = field(
        init=False, default_factory=dict
    )
    _old_rels_by_id: dict[UUID, ClassInstanceRelationship] = field(
        init=False, default_factory=dict
    )
    _new_rels_by_id: dict[UUID, ClassInstanceRelationship] = field(
        init=False, default_factory=dict
    )

    def __post_init__(self) -> None:
        self._old_class_instances_by_id = {ci.id: ci for ci in self.old.class_instances}
        self._new_class_instances_by_id = {ci.id: ci for ci in self.new.class_instances}

        self._old_attributes_by_id = {
            attribute.id: attribute
            for class_instance in self.old.class_instances
            for attribute in class_instance.attributes
        }
        self._new_attributes_by_id = {
            attribute.id: attribute
            for class_instance in self.new.class_instances
            for attribute in class_instance.attributes
        }

        self._old_rels_by_id = {
            relationship.id: relationship
            for relationship in self.old.class_instance_relationships
        }
        self._new_rels_by_id = {
            relationship.id: relationship
            for relationship in self.new.class_instance_relationships
        }

    def class_instance_change_from_delta(
        self, delta: ObjectInstanceGraphDelta
    ) -> ClassInstanceChange | None:
        if delta.kind != ObjectInstanceGraphMemberKind.class_instance:
            raise ValueError(f"Expected class_instance delta, got {delta.kind}")

        field_deltas = list(delta.field_deltas)
        if (
            delta.operation == ChangeType.update
            and not field_deltas
            and not any(delta.child_deltas.values())
        ):
            return None
        if delta.operation == ChangeType.create:
            ci = self._resolve_class_instance(delta=delta)
            field_deltas = _merge_field_deltas(
                field_deltas,
                [
                    FieldDelta(
                        property="class_config_id",
                        op=DeltaOp.SET,
                        value=ci.class_config_id,
                    )
                ],
            )
            field_deltas = _merge_field_deltas(
                field_deltas,
                [
                    FieldDelta(
                        property="source_object_id",
                        op=DeltaOp.SET,
                        value=ci.source_object_id,
                    )
                ],
            )
        change = _build_change(
            key=f"class_instance:{delta.path_key}:{delta.operation.value}",
            change_type=delta.operation,
            field_deltas=field_deltas,
            created_at=self.created_at,
        )
        ci_change = ClassInstanceChange(
            class_instance_id=delta.stable_id,
            change=change,
            change_id=change.id,
            attribute_changes=[],
        )

        if delta.operation == ChangeType.delete:
            return ci_change

        for attr_delta in delta.child_deltas.get(
            ObjectInstanceGraphMemberKind.attribute, []
        ):
            ci_change.attribute_changes.append(
                self.attribute_change_from_delta(attr_delta, parent=ci_change)
            )

        return ci_change

    def attribute_change_from_delta(
        self, delta: ObjectInstanceGraphDelta, *, parent: ClassInstanceChange
    ) -> AttributeChange:
        if delta.kind != ObjectInstanceGraphMemberKind.attribute:
            raise ValueError(f"Expected attribute delta, got {delta.kind}")

        field_deltas = list(delta.field_deltas)
        if delta.operation in (ChangeType.create, ChangeType.update):
            attr = self._resolve_attribute(delta=delta)
            field_deltas = _merge_field_deltas(
                field_deltas,
                [
                    FieldDelta(
                        property="attribute_config_id",
                        op=DeltaOp.SET,
                        value=attr.attribute_config_id,
                    )
                ],
            )

        change = _build_change(
            key=f"attribute:{delta.path_key}:{delta.operation.value}",
            change_type=delta.operation,
            field_deltas=field_deltas,
            created_at=self.created_at,
        )
        attr_change = AttributeChange(
            attribute_id=delta.stable_id,
            class_instance_change_id=parent.id,
            change=change,
            change_id=change.id,
            value_root_change=None,
            value_root_change_id=None,
        )

        if delta.operation == ChangeType.delete:
            return attr_change

        value_deltas = delta.child_deltas.get(
            ObjectInstanceGraphMemberKind.attribute_value, []
        )
        if len(value_deltas) > 1:
            raise ValueError(
                f"Attribute delta {delta.path_key} has {len(value_deltas)} value roots; expected <= 1"
            )
        if value_deltas:
            root_change = self.attribute_value_change_from_delta(value_deltas[0])
            attr_change.value_root_change = root_change
            attr_change.value_root_change_id = root_change.id
        return attr_change

    def attribute_value_change_from_delta(
        self, delta: ObjectInstanceGraphDelta
    ) -> AttributeValueChange:
        if delta.kind != ObjectInstanceGraphMemberKind.attribute_value:
            raise ValueError(f"Expected attribute_value delta, got {delta.kind}")

        change = _build_change(
            key=f"attribute_value:{delta.path_key}:{delta.operation.value}",
            change_type=delta.operation,
            field_deltas=delta.field_deltas,
            created_at=self.created_at,
        )
        value_change = AttributeValueChange(
            attribute_value_id=delta.stable_id,
            change=change,
            change_id=change.id,
            attribute_value_link_changes=[],
        )

        if delta.operation == ChangeType.delete:
            return value_change

        for link_delta in delta.child_deltas.get(
            ObjectInstanceGraphMemberKind.attribute_value_link, []
        ):
            value_change.attribute_value_link_changes.append(
                self.attribute_value_link_change_from_delta(
                    link_delta, parent=value_change
                )
            )
        return value_change

    def attribute_value_link_change_from_delta(
        self, delta: ObjectInstanceGraphDelta, *, parent: AttributeValueChange
    ) -> AttributeValueLinkChange:
        if delta.kind != ObjectInstanceGraphMemberKind.attribute_value_link:
            raise ValueError(f"Expected attribute_value_link delta, got {delta.kind}")

        change = _build_change(
            key=f"attribute_value_link:{delta.path_key}:{delta.operation.value}",
            change_type=delta.operation,
            field_deltas=delta.field_deltas,
            created_at=self.created_at,
        )
        link_change = AttributeValueLinkChange(
            attribute_value_change_id=parent.id,
            attribute_value_link_id=delta.stable_id,
            change=change,
            change_id=change.id,
            child_attribute_value_change=None,
            child_attribute_value_change_id=None,
        )

        if delta.operation == ChangeType.delete:
            return link_change

        child_deltas = delta.child_deltas.get(
            ObjectInstanceGraphMemberKind.attribute_value, []
        )
        if len(child_deltas) != 1:
            raise ValueError(
                f"AttributeValueLink delta {delta.path_key} expected 1 child value delta, got {len(child_deltas)}"
            )
        child_change = self.attribute_value_change_from_delta(child_deltas[0])
        link_change.child_attribute_value_change = child_change
        link_change.child_attribute_value_change_id = child_change.id
        return link_change

    def relationship_change_from_delta(
        self, delta: ObjectInstanceGraphDelta
    ) -> ClassInstanceRelationshipChange:
        if delta.kind != ObjectInstanceGraphMemberKind.relationship_instance:
            raise ValueError(f"Expected relationship_instance delta, got {delta.kind}")

        # v0: relationship changes are structural; no scalar deltas.
        change = _build_change(
            key=f"relationship:{delta.path_key}:{delta.operation.value}",
            change_type=delta.operation,
            field_deltas=[],
            created_at=self.created_at,
        )

        rel = self._resolve_relationship(delta=delta)
        return ClassInstanceRelationshipChange(
            change=change,
            change_id=change.id,
            class_config_relationship_id=rel.class_config_relationship_id,
            source_class_instance_id=rel.source_class_instance_id,
            target_class_instance_id=rel.target_class_instance_id,
        )

    def _resolve_relationship(self, *, delta: ObjectInstanceGraphDelta):
        rel: ClassInstanceRelationship | None
        rel_id = delta.stable_id
        if delta.operation == ChangeType.create:
            rel = self._new_rels_by_id.get(rel_id)
        else:
            rel = self._old_rels_by_id.get(rel_id)
        if rel is None:
            raise ValueError(
                f"Relationship not found for op={delta.operation} id={rel_id} path={delta.path_key}"
            )
        return rel

    def _resolve_class_instance(
        self, *, delta: ObjectInstanceGraphDelta
    ) -> ClassInstance:
        ci: ClassInstance | None
        ci_id = delta.stable_id
        if delta.operation == ChangeType.create:
            ci = self._new_class_instances_by_id.get(
                ci_id
            ) or self._old_class_instances_by_id.get(ci_id)
        else:
            ci = self._old_class_instances_by_id.get(
                ci_id
            ) or self._new_class_instances_by_id.get(ci_id)
        if ci is None:
            raise ValueError(
                f"ClassInstance not found for op={delta.operation} id={ci_id} path={delta.path_key}"
            )
        return ci

    def _resolve_attribute(self, *, delta: ObjectInstanceGraphDelta) -> Attribute:
        attr: Attribute | None
        attr_id = delta.stable_id
        if delta.operation == ChangeType.create:
            attr = self._new_attributes_by_id.get(
                attr_id
            ) or self._old_attributes_by_id.get(attr_id)
        else:
            attr = self._old_attributes_by_id.get(
                attr_id
            ) or self._new_attributes_by_id.get(attr_id)
        if attr is None:
            raise ValueError(
                f"Attribute not found for op={delta.operation} id={attr_id} path={delta.path_key}"
            )
        return attr


def _merge_field_deltas(
    field_deltas: list[FieldDelta], required: list[FieldDelta]
) -> list[FieldDelta]:
    existing_props = {fd.property for fd in field_deltas}
    out = list(field_deltas)
    for fd in required:
        if fd.property in existing_props:
            continue
        out.append(fd)
    return out


__all__ = [
    "DeltaOp",
    "FieldDelta",
    "ObjectInstanceGraphDelta",
    "build_object_instance_graph_seed_changes",
    "diff_object_instance_graph",
    "diff_object_instance_graph_changes",
]
