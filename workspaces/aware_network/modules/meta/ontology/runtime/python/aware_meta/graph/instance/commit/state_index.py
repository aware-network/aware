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
from aware_meta.graph.instance.commit.body_codec import OigCommitBodyDraft


CommitStateRowKind = Literal["NODE", "ATTR", "EDGE"]


@dataclass(frozen=True, slots=True, order=True)
class CommitStateRow:
    kind: CommitStateRowKind
    key: str
    value: str


@dataclass(frozen=True, slots=True)
class CommitStateRowMaps:
    class_config_ids_by_class_instance_id: Mapping[UUID, UUID]
    class_state_rows_by_id: Mapping[UUID, tuple[CommitStateRow, ...]]
    class_state_rows_by_raw_id: Mapping[str, tuple[CommitStateRow, ...]]
    relationship_keys: frozenset[tuple[UUID, UUID, UUID]]


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

    def row_maps(
        self,
        *,
        include_relationship_keys: bool = True,
    ) -> CommitStateRowMaps:
        class_config_ids_by_raw_id: dict[str, UUID] = {}
        class_state_row_lists_by_raw_id: dict[str, list[CommitStateRow]] = {}
        relationship_keys: set[tuple[UUID, UUID, UUID]] = set()

        for row in self.rows:
            if row.kind == "NODE":
                class_config_id = UUID(row.key)
                class_instance_id = UUID(row.value)
                raw_class_instance_id = str(class_instance_id)
                previous_class_config_id = class_config_ids_by_raw_id.get(
                    raw_class_instance_id,
                )
                if (
                    previous_class_config_id is not None
                    and previous_class_config_id != class_config_id
                ):
                    raise ValueError(
                        "CommitStateIndex rows contain conflicting NODE rows for "
                        f"ClassInstance {class_instance_id}"
                    )
                class_config_ids_by_raw_id[raw_class_instance_id] = class_config_id
                class_state_row_lists_by_raw_id.setdefault(
                    raw_class_instance_id,
                    [],
                ).append(row)
                continue
            if row.kind == "ATTR":
                class_state_row_lists_by_raw_id.setdefault(row.key, []).append(row)
                continue
            if row.kind == "EDGE":
                if not include_relationship_keys:
                    continue
                raw_source_id, separator, raw_target_id = row.value.partition("->")
                if not separator:
                    raise ValueError(f"Malformed relationship state row: {row.value!r}")
                relationship_keys.add(
                    (UUID(row.key), UUID(raw_source_id), UUID(raw_target_id)),
                )
                continue
            raise ValueError(f"Unsupported CommitStateRow kind: {row.kind!r}")

        class_state_rows_by_raw_id = {
            class_instance_id: tuple(rows)
            for class_instance_id, rows in class_state_row_lists_by_raw_id.items()
        }
        return CommitStateRowMaps(
            class_config_ids_by_class_instance_id={
                UUID(class_instance_id): class_config_id
                for class_instance_id, class_config_id in (
                    class_config_ids_by_raw_id.items()
                )
            },
            class_state_rows_by_id={
                UUID(class_instance_id): rows
                for class_instance_id, rows in class_state_rows_by_raw_id.items()
            },
            class_state_rows_by_raw_id=class_state_rows_by_raw_id,
            relationship_keys=frozenset(relationship_keys),
        )


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


def build_class_instance_state_rows(
    class_instance: ClassInstance,
) -> tuple[CommitStateRow, ...]:
    """Build canonical NODE/ATTR rows for one ClassInstance.

    This is the object-shaped compatibility adapter. Delta-first callers should
    produce equivalent rows directly and feed `apply_commit_state_index_row_changes`.
    """
    return _class_instance_state_rows(class_instance)


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

    return apply_commit_state_index_row_changes(
        pre_state_index=pre_state_index,
        changes=changes,
        post_class_state_rows_by_id={
            class_instance_id: _class_instance_state_rows(class_instance)
            for class_instance_id, class_instance in post_class_instances_by_id.items()
        },
    )


def apply_commit_state_index_row_changes(
    *,
    pre_state_index: CommitStateIndex,
    changes: Iterable[ObjectInstanceGraphChange],
    post_class_state_rows_by_id: Mapping[UUID, Iterable[CommitStateRow]],
) -> CommitStateIndex:
    """Apply OIG changes to compact state rows using caller-supplied post rows.

    This is the delta-first primitive. It does not require post-state
    ClassInstance objects; callers can emit canonical NODE/ATTR rows from a
    semantic operation, state witness, or package-specific source row contract.
    """

    change_trees = tuple(changes)
    return _apply_commit_state_index_effects(
        pre_state_index=pre_state_index,
        class_effects=(
            (class_change.class_instance_id, _change_type(class_change.change.type))
            for change_tree in change_trees
            for class_change in change_tree.class_instance_changes
        ),
        relationship_effects=(
            (
                relationship_change.class_config_relationship_id,
                relationship_change.source_class_instance_id,
                relationship_change.target_class_instance_id,
                _change_type(relationship_change.change.type),
            )
            for change_tree in change_trees
            for relationship_change in change_tree.class_instance_relationship_changes
        ),
        post_class_state_rows_by_id=post_class_state_rows_by_id,
    )


def apply_commit_state_index_body_draft(
    *,
    pre_state_index: CommitStateIndex,
    body_draft: OigCommitBodyDraft,
    post_class_state_rows_by_id: Mapping[UUID, Iterable[CommitStateRow]],
) -> CommitStateIndex:
    """Apply typed commit-body effects to compact state rows."""

    if not body_draft.roots:
        raise ValueError("Commit body draft state apply requires at least one root")
    return _apply_commit_state_index_effects(
        pre_state_index=pre_state_index,
        class_effects=(
            (class_change.class_instance_id, _change_type(class_change.change.type))
            for root in body_draft.roots
            for class_change in root.class_instance_changes
        ),
        relationship_effects=(
            (
                relationship_change.class_config_relationship_id,
                relationship_change.source_class_instance_id,
                relationship_change.target_class_instance_id,
                _change_type(relationship_change.change.type),
            )
            for root in body_draft.roots
            for relationship_change in root.class_instance_relationship_changes
        ),
        post_class_state_rows_by_id=post_class_state_rows_by_id,
    )


def _apply_commit_state_index_effects(
    *,
    pre_state_index: CommitStateIndex,
    class_effects: Iterable[tuple[UUID, ChangeType]],
    relationship_effects: Iterable[tuple[UUID, UUID, UUID, ChangeType]],
    post_class_state_rows_by_id: Mapping[UUID, Iterable[CommitStateRow]],
) -> CommitStateIndex:
    class_instance_ids_to_delete: set[str] = set()
    class_instance_ids_to_replace: set[UUID] = set()

    class_effect_tuple = tuple(class_effects)
    relationship_effect_tuple = tuple(relationship_effects)
    for class_instance_id, operation in class_effect_tuple:
        if operation == ChangeType.delete:
            class_instance_ids_to_delete.add(str(class_instance_id))
            continue
        if operation in (ChangeType.create, ChangeType.update):
            class_instance_ids_to_replace.add(class_instance_id)
            continue
        raise ValueError(
            "Unsupported ClassInstance change type for state index row apply: "
            f"{operation}"
        )

    replacement_rows: set[CommitStateRow] = set()
    for class_instance_id in sorted(class_instance_ids_to_replace, key=str):
        post_rows = tuple(post_class_state_rows_by_id.get(class_instance_id, ()))
        if not post_rows:
            raise ValueError(
                "Post-state ClassInstance rows missing for state index row apply: "
                f"{class_instance_id}"
            )
        _validate_class_instance_state_rows(
            class_instance_id=class_instance_id,
            rows=post_rows,
        )
        replacement_rows.update(post_rows)

    relationship_operations: dict[CommitStateRow, ChangeType] = {}
    for relationship_id, source_id, target_id, operation in relationship_effect_tuple:
        row = _relationship_state_row(
            relationship_id=relationship_id,
            source_id=source_id,
            target_id=target_id,
        )
        if operation not in (ChangeType.create, ChangeType.delete):
            raise ValueError(
                "Unsupported ClassInstanceRelationship change type for state "
                f"index apply: {operation}"
            )
        relationship_operations[row] = operation

    affected_class_instance_ids = class_instance_ids_to_delete | {
        str(class_instance_id) for class_instance_id in class_instance_ids_to_replace
    }
    rows: set[CommitStateRow] = set()
    for row in pre_state_index.rows:
        if row.kind == "NODE":
            if row.value in affected_class_instance_ids:
                continue
        elif row.kind == "ATTR":
            if row.key in affected_class_instance_ids:
                continue
        elif row.kind == "EDGE":
            if row in relationship_operations:
                continue
            raw_source_id, separator, raw_target_id = row.value.partition("->")
            if separator and (
                raw_source_id in class_instance_ids_to_delete
                or raw_target_id in class_instance_ids_to_delete
            ):
                continue
        rows.add(row)

    rows.update(replacement_rows)
    rows.update(
        row
        for row, operation in relationship_operations.items()
        if operation == ChangeType.create
    )

    return _canonical_commit_state_index(rows)


def _validate_class_instance_state_rows(
    *,
    class_instance_id: UUID,
    rows: Iterable[CommitStateRow],
) -> None:
    class_instance_id_text = str(class_instance_id)
    has_node = False
    for row in rows:
        if row.kind == "NODE" and row.value == class_instance_id_text:
            has_node = True
            continue
        if row.kind == "ATTR" and row.key == class_instance_id_text:
            continue
        raise ValueError(
            "Post-state ClassInstance rows target unexpected state member: "
            f"class_instance_id={class_instance_id} row={row}"
        )
    if not has_node:
        raise ValueError(
            "Post-state ClassInstance rows missing NODE row for " f"{class_instance_id}"
        )


__all__ = [
    "apply_commit_state_index_body_draft",
    "apply_commit_state_index_row_changes",
    "CommitStateIndex",
    "CommitStateRow",
    "CommitStateRowMaps",
    "CommitStateRowKind",
    "apply_commit_state_index_changes",
    "build_class_instance_state_rows",
    "build_commit_state_index",
    "compute_commit_state_rows_hash",
]
