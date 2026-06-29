from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import hashlib
from typing import Literal
from uuid import UUID

from aware_history_ontology.change.change_enums import ChangeType
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)

from aware_meta.attribute.instance.value.builder import fingerprint_attribute_value


CommitStateRowKind = Literal["NODE", "ATTR", "EDGE"]


@dataclass(frozen=True, slots=True, order=True)
class CommitStateRow:
    kind: CommitStateRowKind
    key: str
    value: str


@dataclass(frozen=True, slots=True)
class CommitStateIndex:
    rows: tuple[CommitStateRow, ...]

    @property
    def node_count(self) -> int:
        return sum(1 for row in self.rows if row.kind == "NODE")

    @property
    def attribute_count(self) -> int:
        return sum(1 for row in self.rows if row.kind == "ATTR")

    @property
    def edge_count(self) -> int:
        return sum(1 for row in self.rows if row.kind == "EDGE")

    def compute_hash(self) -> str:
        return compute_commit_state_rows_hash(self.rows)


def compute_commit_state_rows_hash(rows: Iterable[CommitStateRow]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(row.kind.encode("utf-8"))
        digest.update(b"|")
        digest.update(row.key.encode("utf-8"))
        digest.update(b"|")
        digest.update(row.value.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _class_instance_state_rows(
    class_instance: ClassInstance,
) -> tuple[CommitStateRow, ...]:
    if class_instance.class_config_id is None or class_instance.id is None:
        return ()

    rows: list[CommitStateRow] = [
        CommitStateRow(
            kind="NODE",
            key=str(class_instance.class_config_id),
            value=str(class_instance.id),
        )
    ]
    attribute_rows: set[tuple[str, str]] = set()
    for attribute in class_instance.attributes:
        if attribute is None or attribute.attribute_config_id is None:
            continue
        root = attribute.value_root
        value_fingerprint = (
            fingerprint_attribute_value(root) if root is not None else "missing"
        )
        attribute_rows.add((str(attribute.attribute_config_id), value_fingerprint))

    for attribute_config_id, value_fingerprint in sorted(attribute_rows):
        rows.append(
            CommitStateRow(
                kind="ATTR",
                key=str(class_instance.id),
                value=f"{attribute_config_id}:{value_fingerprint}",
            )
        )
    return tuple(rows)


def _relationship_state_row(
    *,
    relationship_id: UUID,
    source_id: UUID,
    target_id: UUID,
) -> CommitStateRow:
    return CommitStateRow(
        kind="EDGE",
        key=str(relationship_id),
        value=f"{source_id}->{target_id}",
    )


def _canonical_commit_state_index(
    rows: Iterable[CommitStateRow],
) -> CommitStateIndex:
    row_set = set(rows)
    node_rows = sorted(
        (row for row in row_set if row.kind == "NODE"),
        key=lambda row: (row.key, row.value),
    )
    attrs_by_class_instance_id: dict[str, list[CommitStateRow]] = {}
    for row in row_set:
        if row.kind != "ATTR":
            continue
        attrs_by_class_instance_id.setdefault(row.key, []).append(row)
    edge_rows = sorted(
        (row for row in row_set if row.kind == "EDGE"),
        key=lambda row: (row.key, row.value),
    )

    ordered_rows: list[CommitStateRow] = []
    seen_node_ids: set[str] = set()
    for node_row in node_rows:
        ordered_rows.append(node_row)
        seen_node_ids.add(node_row.value)
        ordered_rows.extend(
            sorted(
                attrs_by_class_instance_id.pop(node_row.value, []),
                key=lambda row: row.value,
            )
        )

    # Keep malformed/orphan rows deterministic without making them valid.
    for class_instance_id in sorted(attrs_by_class_instance_id):
        if class_instance_id in seen_node_ids:
            continue
        ordered_rows.extend(
            sorted(
                attrs_by_class_instance_id[class_instance_id],
                key=lambda row: row.value,
            )
        )
    ordered_rows.extend(edge_rows)
    return CommitStateIndex(rows=tuple(ordered_rows))


def build_commit_state_index(graph: ObjectInstanceGraph) -> CommitStateIndex:
    rows: list[CommitStateRow] = []

    class_instances = [
        ci
        for ci in graph.class_instances
        if ci is not None and ci.class_config_id is not None and ci.id is not None
    ]
    class_instances.sort(key=lambda ci: (str(ci.class_config_id), str(ci.id)))

    for class_instance in class_instances:
        rows.extend(_class_instance_state_rows(class_instance))

    relationship_rows: set[tuple[str, str, str]] = set()
    for relationship in graph.class_instance_relationships:
        if relationship is None or relationship.class_config_relationship_id is None:
            continue
        if (
            relationship.source_class_instance_id is None
            or relationship.target_class_instance_id is None
        ):
            continue
        relationship_rows.add(
            (
                str(relationship.class_config_relationship_id),
                str(relationship.source_class_instance_id),
                str(relationship.target_class_instance_id),
            )
        )

    for relationship_id, source_id, target_id in sorted(relationship_rows):
        rows.append(
            _relationship_state_row(
                relationship_id=UUID(relationship_id),
                source_id=UUID(source_id),
                target_id=UUID(target_id),
            )
        )

    return CommitStateIndex(rows=tuple(rows))


def _change_type(value: object) -> ChangeType:
    return value if isinstance(value, ChangeType) else ChangeType(str(value))


def apply_commit_state_index_changes(
    *,
    pre_state_index: CommitStateIndex,
    changes: Iterable[ObjectInstanceGraphChange],
    post_class_instances_by_id: Mapping[UUID, ClassInstance],
) -> CommitStateIndex:
    """Apply OIG changes to compact state rows without materializing a full OIG.

    Class-instance changes replace the affected instance's NODE/ATTR rows from
    the caller-provided post-state class instance. This is intentionally broader
    than trying to patch individual attribute rows: the hash rows do not carry
    Attribute IDs, so row replacement is the minimal honest primitive for
    attribute updates.
    """

    rows = set(pre_state_index.rows)

    class_instance_ids_to_delete: set[str] = set()
    class_instance_ids_to_replace: set[UUID] = set()

    for change_tree in changes:
        for class_change in change_tree.class_instance_changes:
            operation = _change_type(class_change.change.type)
            class_instance_id = class_change.class_instance_id
            if operation == ChangeType.delete:
                class_instance_ids_to_delete.add(str(class_instance_id))
                continue
            if operation in (ChangeType.create, ChangeType.update):
                class_instance_ids_to_replace.add(class_instance_id)
                continue
            raise ValueError(
                "Unsupported ClassInstance change type for state index apply: "
                f"{operation}"
            )

    for class_instance_id in class_instance_ids_to_delete:
        rows = {
            row
            for row in rows
            if not (
                (row.kind == "NODE" and row.value == class_instance_id)
                or (row.kind == "ATTR" and row.key == class_instance_id)
                or (
                    row.kind == "EDGE"
                    and (
                        row.value.startswith(f"{class_instance_id}->")
                        or row.value.endswith(f"->{class_instance_id}")
                    )
                )
            )
        }

    for class_instance_id in sorted(class_instance_ids_to_replace, key=str):
        class_instance_id_text = str(class_instance_id)
        class_instance = post_class_instances_by_id.get(class_instance_id)
        if class_instance is None:
            raise ValueError(
                "Post-state ClassInstance missing for state index apply: "
                f"{class_instance_id}"
            )
        rows = {
            row
            for row in rows
            if not (
                (row.kind == "NODE" and row.value == class_instance_id_text)
                or (row.kind == "ATTR" and row.key == class_instance_id_text)
            )
        }
        rows.update(_class_instance_state_rows(class_instance))

    for change_tree in changes:
        for relationship_change in change_tree.class_instance_relationship_changes:
            operation = _change_type(relationship_change.change.type)
            row = _relationship_state_row(
                relationship_id=relationship_change.class_config_relationship_id,
                source_id=relationship_change.source_class_instance_id,
                target_id=relationship_change.target_class_instance_id,
            )
            if operation == ChangeType.create:
                rows.add(row)
                continue
            if operation == ChangeType.delete:
                rows.discard(row)
                continue
            raise ValueError(
                "Unsupported ClassInstanceRelationship change type for state "
                f"index apply: {operation}"
            )

    return _canonical_commit_state_index(rows)


__all__ = [
    "CommitStateIndex",
    "CommitStateRow",
    "CommitStateRowKind",
    "apply_commit_state_index_changes",
    "build_commit_state_index",
    "compute_commit_state_rows_hash",
]
