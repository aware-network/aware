"""Meta-owned plan-driven OIG -> SQL projection row staging.

Contract (canonical-only):
- OIG commits remain SSOT; SQL tables are rebuildable projections for retrieval.
- This module is **emit-only**: it does not infer schema from ORM classes.
- All writes are scoped by `(branch_id, projection_hash)` (lane scope).

This is the Python/Postgres mirror of the Interface (Dart/SQLite) projector:
- Input: OIG(pre), OIG(post), and the change set (for delete detection).
- Plan: ProjectionPlan (compiled from SQL-lowered OCG + OPG membership).
- Output: deterministic SQL upserts/deletes staged into a Session.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any
from uuid import UUID

# History Ontology
from aware_history_ontology.change.change_enums import ChangeType

# Meta Ontology
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)

# Orm
from aware_orm.session.session import Session

from aware_orm.projection.plan import (
    ProjectionAssociationPlan,
    ProjectionColumnPlan,
    ProjectionDialect,
    ProjectionPlan,
    ProjectionTablePlan,
)

__all__ = [
    "LaneProjectionProjectorError",
    "LaneProjectionWritePlan",
    "stage_lane_projection_writes",
]


class LaneProjectionProjectorError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LaneProjectionWritePlan:
    """Debug payload describing what was staged into the Session."""

    create_count: int
    update_count: int
    delete_count: int
    deferred_fk_instance_count: int
    association_insert_count: int = 0
    association_delete_count: int = 0


def _quote_ident(name: str) -> str:
    if not name:
        raise LaneProjectionProjectorError("Empty identifier is not allowed")
    return '"' + name.replace('"', '""') + '"'


def _parse_table_key(table_key: str) -> tuple[str, str]:
    raw = (table_key or "").strip()
    if not raw or "." not in raw:
        raise LaneProjectionProjectorError(f"Invalid table_key (expected <schema>.<table>): {table_key!r}")
    schema, table = raw.split(".", 1)
    schema = schema.strip()
    table = table.strip()
    if not schema or not table:
        raise LaneProjectionProjectorError(f"Invalid table_key (expected <schema>.<table>): {table_key!r}")
    return schema, table


def _resolve_runtime_table_key(table_key: str) -> tuple[str, str]:
    schema, table = _parse_table_key(table_key)
    if schema.strip().lower() != "default":
        return schema, table

    try:
        from aware_orm.runtime.sql_metadata import iter_sql_metadata

        normalized_table = table.strip().lower()
        matches = [
            metadata
            for _key, metadata in iter_sql_metadata()
            if metadata.table_name.strip().lower() == normalized_table
        ]
    except Exception:
        return schema, table

    if len(matches) == 1:
        metadata = matches[0]
        return metadata.table_schema, metadata.table_name
    if len(matches) > 1:
        table_keys = ", ".join(sorted(metadata.table_key for metadata in matches))
        raise LaneProjectionProjectorError(
            f"Ambiguous SQL metadata for projection table {table_key!r}; matches: {table_keys}"
        )
    return schema, table


def _table_fqn(table_key: str) -> str:
    schema, table = _resolve_runtime_table_key(table_key)
    return f"{_quote_ident(schema)}.{_quote_ident(table)}"


def _stable_instance_key(instance: ClassInstance) -> tuple[str, str]:
    return str(instance.class_config_id), str(instance.id)


def _stable_id_key(instance_id: UUID, *, class_config_by_instance_id: Mapping[UUID, UUID]) -> tuple[str, str]:
    cc_id = class_config_by_instance_id.get(instance_id)
    return str(cc_id) if cc_id is not None else "", str(instance_id)


def _toposort(
    nodes: set[UUID],
    deps_by_node: Mapping[UUID, set[UUID]],
    *,
    class_config_by_instance_id: Mapping[UUID, UUID],
) -> list[UUID]:
    import heapq

    in_degree: dict[UUID, int] = {n: 0 for n in nodes}
    dependents_by_parent: dict[UUID, set[UUID]] = {n: set() for n in nodes}
    for node, deps in deps_by_node.items():
        if node not in nodes:
            continue
        for dep in deps:
            if dep not in nodes:
                continue
            in_degree[node] += 1
            dependents_by_parent[dep].add(node)

    heap: list[tuple[tuple[str, str], UUID]] = [
        (_stable_id_key(n, class_config_by_instance_id=class_config_by_instance_id), n)
        for n, d in in_degree.items()
        if d == 0
    ]
    heapq.heapify(heap)
    out: list[UUID] = []

    while heap:
        _, node = heapq.heappop(heap)
        out.append(node)
        for dependent in dependents_by_parent[node]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                heapq.heappush(
                    heap,
                    (
                        _stable_id_key(
                            dependent,
                            class_config_by_instance_id=class_config_by_instance_id,
                        ),
                        dependent,
                    ),
                )

    if len(out) != len(nodes):
        remaining = sorted(
            (n for n, d in in_degree.items() if d > 0),
            key=lambda n: _stable_id_key(n, class_config_by_instance_id=class_config_by_instance_id),
        )
        details = {str(n): sorted((str(d) for d in deps_by_node.get(n, set())), key=str) for n in remaining}
        raise LaneProjectionProjectorError(f"FK dependency cycle detected while projecting lane snapshot: {details}")
    return out


def _index_relationships(
    oig: ObjectInstanceGraph,
) -> dict[UUID, list[ClassInstanceRelationship]]:
    rels_by_id: dict[UUID, list[ClassInstanceRelationship]] = {}
    for rel in oig.class_instance_relationships:
        rel_id = rel.class_config_relationship_id
        if not isinstance(rel_id, UUID):
            continue
        rels_by_id.setdefault(rel_id, []).append(rel)
    for rel_id, edges in rels_by_id.items():
        edges.sort(key=lambda r: str(r.id))
    return rels_by_id


def _index_instances(
    oig: ObjectInstanceGraph,
) -> tuple[dict[UUID, ClassInstance], dict[UUID, UUID]]:
    by_id: dict[UUID, ClassInstance] = {}
    class_config_by_id: dict[UUID, UUID] = {}
    for ci in oig.class_instances:
        ci_id = ci.id
        cc_id = ci.class_config_id
        if not isinstance(ci_id, UUID) or not isinstance(cc_id, UUID):
            continue
        by_id[ci_id] = ci
        class_config_by_id[ci_id] = cc_id
    return by_id, class_config_by_id


def _iter_changed_instance_ids(
    changes: Sequence[ObjectInstanceGraphChange],
) -> tuple[set[UUID], set[UUID], set[UUID], set[UUID]]:
    created: set[UUID] = set()
    updated: set[UUID] = set()
    deleted: set[UUID] = set()
    rel_endpoints: set[UUID] = set()

    for root in changes:
        for ci_change in root.class_instance_changes:
            ch = ci_change.change
            iid = ci_change.class_instance_id
            if ch is None or not isinstance(iid, UUID):
                continue
            if ch.type == ChangeType.delete:
                deleted.add(iid)
            elif ch.type == ChangeType.create:
                created.add(iid)
            else:
                updated.add(iid)

        for rel_change in root.class_instance_relationship_changes:
            src = rel_change.source_class_instance_id
            tgt = rel_change.target_class_instance_id
            if isinstance(src, UUID):
                rel_endpoints.add(src)
            if isinstance(tgt, UUID):
                rel_endpoints.add(tgt)

    return created, updated, deleted, rel_endpoints


def _parse_iso_datetime(value: str) -> datetime:
    raw = value.strip()
    # Python's `fromisoformat` historically does not accept 'Z' directly.
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except Exception as exc:  # pragma: no cover
        raise LaneProjectionProjectorError(f"Invalid ISO datetime string for projection: {value!r}") from exc
    if dt.tzinfo is None:
        # Treat timezone-naive timestamps as UTC. The SSOT commit rail does not carry
        # local time assumptions; projection must be deterministic across hosts.
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _primitive_base_type(root: AttributeValue) -> str | None:
    """Best-effort resolve primitive base_type string from the value's type_descriptor."""
    try:
        td = root.type_descriptor
        if td is None:
            return None
        pc = td.primitive_config
        if pc is None:
            return None
        # Enum-like: prefer `.value` when present.
        value = pc.primitive_type.base_type.value
        return str(value)
    except Exception:  # pragma: no cover
        return None


def _decode_value_root(
    root: AttributeValue,
    *,
    enum_option_value_by_id: Mapping[UUID, str],
    dialect: ProjectionDialect,
) -> Any:  # noqa: ANN401
    type_descriptor = root.type_descriptor
    if type_descriptor is None:
        return None
    kind = type_descriptor.kind

    if kind == AttributeTypeDescriptorKind.enum:
        opt_id = root.enum_option_id
        if opt_id is None:
            return None
        value = enum_option_value_by_id.get(opt_id)
        if value is None:
            raise LaneProjectionProjectorError(f"Missing enum option value mapping for enum_option_id={opt_id}")
        return value

    if kind == AttributeTypeDescriptorKind.primitive:
        raw = root.primitive_value
        if isinstance(raw, dict) and "value" in raw:
            raw = raw["value"]
        # Postgres projection expects native Python types for certain columns (e.g. TIMESTAMPTZ).
        if dialect == "postgres":
            base_type = _primitive_base_type(root)
            if base_type == "datetime" and isinstance(raw, str):
                return _parse_iso_datetime(raw)
        return raw

    if kind == AttributeTypeDescriptorKind.union:
        members = [link for link in (root.child_links or []) if link.role == AttributeTypeDescriptorRole.member]
        if not members:
            return None
        if len(members) != 1:
            raise LaneProjectionProjectorError(f"Invalid UNION value: expected 1 selected member, got {len(members)}")
        return _decode_value_root(
            members[0].child,
            enum_option_value_by_id=enum_option_value_by_id,
            dialect=dialect,
        )

    if kind == AttributeTypeDescriptorKind.collection:
        links = list(root.child_links or [])
        elements = [
            link
            for link in links
            if link.role in {AttributeTypeDescriptorRole.element, AttributeTypeDescriptorRole.member}
        ]
        elements.sort(key=lambda link: (link.position or 0))
        return [
            _decode_value_root(
                link.child,
                enum_option_value_by_id=enum_option_value_by_id,
                dialect=dialect,
            )
            for link in elements
        ]

    if kind == AttributeTypeDescriptorKind.mapping:
        links = list(root.child_links or [])
        keys = [link for link in links if link.role == AttributeTypeDescriptorRole.key]
        values = [link for link in links if link.role == AttributeTypeDescriptorRole.value_]
        keys.sort(key=lambda link: (link.position or 0))
        values.sort(key=lambda link: (link.position or 0))
        if len(keys) != len(values):
            raise LaneProjectionProjectorError(f"Invalid MAPPING value: keys={len(keys)} values={len(values)}")
        return {
            _decode_value_root(
                k.child,
                enum_option_value_by_id=enum_option_value_by_id,
                dialect=dialect,
            ): _decode_value_root(
                v.child,
                enum_option_value_by_id=enum_option_value_by_id,
                dialect=dialect,
            )
            for k, v in zip(keys, values, strict=True)
        }

    if kind == AttributeTypeDescriptorKind.tuple:
        elements = [link for link in (root.child_links or []) if link.role == AttributeTypeDescriptorRole.element]
        elements.sort(key=lambda link: (link.position or 0))
        return tuple(
            _decode_value_root(
                link.child,
                enum_option_value_by_id=enum_option_value_by_id,
                dialect=dialect,
            )
            for link in elements
        )

    if kind == AttributeTypeDescriptorKind.class_:
        # Class references are stored as UUIDs in SQL FK columns.
        return root.class_instance_id

    raise LaneProjectionProjectorError(f"Unsupported attribute value kind for projection decoding: {kind}")


def _resolve_fk_value(
    *,
    ci_id: UUID,
    relationship_id: UUID,
    direction: str,
    rels_by_id: Mapping[UUID, list[ClassInstanceRelationship]],
) -> UUID | None:
    edges = rels_by_id.get(relationship_id)
    if not edges:
        return None

    if direction == "forward":
        found: UUID | None = None
        for rel in edges:
            if rel.source_class_instance_id == ci_id:
                if found is not None and found != rel.target_class_instance_id:
                    raise LaneProjectionProjectorError(
                        "Multiple FK candidates for forward relationship projection: "
                        f"relationship_id={relationship_id} owner_id={ci_id}"
                    )
                found = rel.target_class_instance_id
        return found

    if direction == "reverse":
        found = None
        for rel in edges:
            if rel.target_class_instance_id == ci_id:
                if found is not None and found != rel.source_class_instance_id:
                    raise LaneProjectionProjectorError(
                        "Multiple FK candidates for reverse relationship projection: "
                        f"relationship_id={relationship_id} owner_id={ci_id}"
                    )
                found = rel.source_class_instance_id
        return found

    raise LaneProjectionProjectorError(f"Invalid relationship direction: {direction!r}")


def _resolve_fk_value_with_attribute_fallback(
    *,
    ci: ClassInstance,
    column: ProjectionColumnPlan,
    rels_by_id: Mapping[UUID, list[ClassInstanceRelationship]],
    enum_option_value_by_id: Mapping[UUID, str],
    dialect: ProjectionDialect,
) -> UUID | Any | None:
    """Resolve FK value from relationship edges, then fallback to scalar FK attribute.

    This mirrors row projection behavior for cases where relationship edges are absent
    in the current lane but the FK scalar value is still present.
    """
    rel_id = column.relationship_id
    direction = column.direction
    if rel_id is not None and direction is not None:
        fk_value = _resolve_fk_value(
            ci_id=ci.id,
            relationship_id=rel_id,
            direction=direction,
            rels_by_id=rels_by_id,
        )
        if fk_value is not None:
            return _parse_uuid_fallback(fk_value)

    attr_cfg_id = column.attribute_config_id
    if attr_cfg_id is None:
        return None

    attrs_by_cfg_id: dict[UUID, Attribute] = {}
    for attr in ci.attributes or []:
        if isinstance(attr.attribute_config_id, UUID):
            attrs_by_cfg_id[attr.attribute_config_id] = attr

    fk_attr = attrs_by_cfg_id.get(attr_cfg_id)
    if fk_attr is None or fk_attr.value_root is None:
        return None

    # Preserve existing canonical behavior when required scalar metadata is unavailable.
    if isinstance(fk_attr.value_root, UUID):
        return _parse_uuid_fallback(fk_attr.value_root)

    fk_value = _decode_value_root(
        fk_attr.value_root,
        enum_option_value_by_id=enum_option_value_by_id,
        dialect=dialect,
    )
    return _parse_uuid_fallback(fk_value)


def _parse_uuid_fallback(value: Any) -> UUID | Any:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        try:
            return UUID(value)
        except ValueError:
            return value
    return value


def _build_upsert_sql(table: ProjectionTablePlan) -> str:
    col_names = [c.column_name for c in table.columns]
    if not col_names:
        raise LaneProjectionProjectorError(f"Projection table has no columns: {table.table_key}")

    pk_cols = list(table.primary_key or ("id",))
    placeholders = ", ".join(f"${i}" for i in range(1, len(col_names) + 1))

    update_cols = [c for c in col_names if c not in pk_cols]
    if update_cols:
        update_clause = " DO UPDATE SET " + ", ".join(
            f"{_quote_ident(c)} = EXCLUDED.{_quote_ident(c)}" for c in update_cols
        )
    else:
        update_clause = " DO NOTHING"

    columns_sql = ", ".join(_quote_ident(c) for c in col_names)
    pk_sql = ", ".join(_quote_ident(c) for c in pk_cols)
    return (
        f"INSERT INTO {_table_fqn(table.table_key)} ({columns_sql}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT ({pk_sql}){update_clause}"
    )


def _build_delete_sql(table: ProjectionTablePlan) -> str:
    pk_cols = list(table.primary_key or ("id",))
    where = " AND ".join(f"{_quote_ident(c)} = ${i}" for i, c in enumerate(pk_cols, start=1))
    return f"DELETE FROM {_table_fqn(table.table_key)} WHERE {where}"


def _build_assoc_upsert_sql(assoc: ProjectionAssociationPlan) -> str:
    cols = (
        "branch_id",
        "projection_hash",
        "id",
        assoc.source_fk_column,
        assoc.target_fk_column,
    )
    placeholders = ", ".join(f"${i}" for i in range(1, len(cols) + 1))
    columns_sql = ", ".join(_quote_ident(c) for c in cols)
    pk_sql = ", ".join(_quote_ident(c) for c in ("branch_id", "projection_hash", "id"))

    src = assoc.source_fk_column
    tgt = assoc.target_fk_column
    update_clause = (
        " DO UPDATE SET "
        f"{_quote_ident(src)} = EXCLUDED.{_quote_ident(src)}, "
        f"{_quote_ident(tgt)} = EXCLUDED.{_quote_ident(tgt)}"
    )
    return (
        f"INSERT INTO {_table_fqn(assoc.association_table_key)} ({columns_sql}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT ({pk_sql}){update_clause}"
    )


def _build_assoc_delete_sql(assoc: ProjectionAssociationPlan) -> str:
    where = " AND ".join(
        (
            f'{_quote_ident("branch_id")} = $1',
            f'{_quote_ident("projection_hash")} = $2',
            f'{_quote_ident("id")} = $3',
        )
    )
    return f"DELETE FROM {_table_fqn(assoc.association_table_key)} WHERE {where}"


def _project_row_values(
    *,
    ci: ClassInstance,
    table: ProjectionTablePlan,
    rels_by_id: Mapping[UUID, list[ClassInstanceRelationship]],
    branch_id: UUID,
    projection_hash: str,
    enum_option_value_by_id: Mapping[UUID, str],
    dialect: ProjectionDialect,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None = None,
    override_by_column: Mapping[str, object] | None = None,
) -> tuple[Any, ...]:
    attrs_by_cfg_id: dict[UUID, Attribute] = {}
    for attr in ci.attributes or []:
        cfg_id = attr.attribute_config_id
        if isinstance(cfg_id, UUID):
            attrs_by_cfg_id[cfg_id] = attr

    values: list[Any] = []
    overrides = override_by_column or {}
    for col in table.columns:

        def _emit(value: Any) -> None:
            # asyncpg expects Python types compatible with the target SQL column type.
            # Some bundles store structured payloads (mapping/collection) into TEXT columns
            # for portability; encode them deterministically as JSON strings.
            if col.sql_type_hint == "TEXT" and isinstance(value, (dict, list)):
                value = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
            values.append(value)

        if col.column_name in overrides:
            _emit(overrides[col.column_name])
            continue

        if col.source == "branch_id":
            _emit(branch_id)
            continue
        if col.source == "projection_hash":
            _emit(projection_hash)
            continue
        if col.source == "id":
            _emit(ci.id)
            continue

        if col.source == "attribute":
            attr_cfg_id = col.attribute_config_id
            if attr_cfg_id is None:
                _emit(None)
                continue
            attr = attrs_by_cfg_id.get(attr_cfg_id)
            if attr is None:
                if col.nullable:
                    _emit(None)
                    continue
                cfg = attribute_configs_by_id.get(attr_cfg_id) if attribute_configs_by_id else None
                if cfg is not None and cfg.type_descriptor is not None:
                    kind = cfg.type_descriptor.kind
                    if kind in (
                        AttributeTypeDescriptorKind.collection,
                        AttributeTypeDescriptorKind.tuple,
                    ):
                        _emit([])
                        continue
                    if kind == AttributeTypeDescriptorKind.mapping:
                        _emit({})
                        continue
                raise LaneProjectionProjectorError(
                    "Missing required attribute while projecting row: "
                    f"instance_id={ci.id} column={col.column_name} attribute_config_id={attr_cfg_id}"
                )
                continue
            root = attr.value_root
            if root is None:
                if col.nullable:
                    _emit(None)
                    continue
                cfg = attribute_configs_by_id.get(attr_cfg_id) if attribute_configs_by_id else None
                if cfg is not None and cfg.type_descriptor is not None:
                    kind = cfg.type_descriptor.kind
                    if kind in (
                        AttributeTypeDescriptorKind.collection,
                        AttributeTypeDescriptorKind.tuple,
                    ):
                        _emit([])
                        continue
                    if kind == AttributeTypeDescriptorKind.mapping:
                        _emit({})
                        continue
                raise LaneProjectionProjectorError(
                    "Missing required attribute value_root while projecting row: "
                    f"instance_id={ci.id} column={col.column_name} attribute_config_id={attr_cfg_id}"
                )
                continue
            _emit(
                _decode_value_root(
                    root,
                    enum_option_value_by_id=enum_option_value_by_id,
                    dialect=dialect,
                )
            )
            continue

        if col.source == "fk_attribute":
            rel_id = col.relationship_id
            direction = col.direction
            fk_value = None
            if rel_id is not None and direction is not None:
                fk_value = _resolve_fk_value(
                    ci_id=ci.id,
                    relationship_id=rel_id,
                    direction=direction,
                    rels_by_id=rels_by_id,
                )

            # Canonical fallback: when relationship edges are not present in this lane
            # (e.g. cross-projection references), use the FK scalar attribute value.
            if fk_value is None and col.attribute_config_id is not None:
                fk_attr = attrs_by_cfg_id.get(col.attribute_config_id)
                if fk_attr is not None and fk_attr.value_root is not None:
                    fk_value = _decode_value_root(
                        fk_attr.value_root,
                        enum_option_value_by_id=enum_option_value_by_id,
                        dialect=dialect,
                    )

            if fk_value is None and not col.nullable:
                raise LaneProjectionProjectorError(
                    "Missing required FK while projecting row: "
                    f"instance_id={ci.id} column={col.column_name} relationship_id={rel_id} "
                    f"attribute_config_id={col.attribute_config_id}"
                )

            _emit(fk_value)
            continue

        raise LaneProjectionProjectorError(f"Unsupported ProjectionColumn source: {col.source!r}")

    return tuple(values)


def _delete_params(
    *,
    table: ProjectionTablePlan,
    instance_id: UUID,
    instance: ClassInstance,
    rels_by_id: Mapping[UUID, list[ClassInstanceRelationship]],
    branch_id: UUID,
    projection_hash: str,
    enum_option_value_by_id: Mapping[UUID, str],
    dialect: ProjectionDialect,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None = None,
) -> tuple[Any, ...]:
    projected_row = _project_row_values(
        ci=instance,
        table=table,
        rels_by_id=rels_by_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        enum_option_value_by_id=enum_option_value_by_id,
        dialect=dialect,
        attribute_configs_by_id=attribute_configs_by_id,
    )
    row_by_column = {
        col.column_name: value
        for col, value in zip(table.columns, projected_row, strict=False)
    }

    params: list[Any] = []
    for col in table.primary_key or ("id",):
        if col == "branch_id":
            params.append(branch_id)
        elif col == "projection_hash":
            params.append(projection_hash)
        elif col == "id":
            params.append(instance_id)
        elif col in row_by_column:
            params.append(row_by_column[col])
        else:
            raise LaneProjectionProjectorError(
                "Unsupported primary key column for projection delete; "
                f"column={col!r} pk={table.primary_key!r} table={table.table_key}"
            )
    return tuple(params)


def stage_lane_projection_writes(
    *,
    session: Session,
    plan: ProjectionPlan,
    branch_id: UUID,
    projection_hash: str,
    before_oig: ObjectInstanceGraph,
    after_oig: ObjectInstanceGraph,
    changes: Sequence[ObjectInstanceGraphChange],
    enum_option_value_by_id: Mapping[UUID, str],
    attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None = None,
) -> LaneProjectionWritePlan:
    """Stage deterministic Postgres projection writes into the provided Session.

    Notes
    -----
    - This function performs **no DB reads**.
    - It stages SQL into the Session; caller commits/rolls back.
    """

    if session.skip_db:
        return LaneProjectionWritePlan(create_count=0, update_count=0, delete_count=0, deferred_fk_instance_count=0)

    if plan.dialect != "postgres":
        raise LaneProjectionProjectorError(f"Postgres projector requires plan.dialect='postgres', got {plan.dialect!r}")

    after_instances_by_id, after_cc_by_iid = _index_instances(after_oig)
    before_instances_by_id, before_cc_by_iid = _index_instances(before_oig)
    after_rels_by_id = _index_relationships(after_oig)
    before_rels_by_id = _index_relationships(before_oig)

    # Association plans are keyed by relationship_id; pre-build SQL for deterministic staging.
    assoc_plans = sorted(
        plan.associations,
        key=lambda a: (a.association_table_key, str(a.relationship_id)),
    )
    assoc_upsert_sql_by_rel_id: dict[UUID, str] = {a.relationship_id: _build_assoc_upsert_sql(a) for a in assoc_plans}
    assoc_delete_sql_by_rel_id: dict[UUID, str] = {a.relationship_id: _build_assoc_delete_sql(a) for a in assoc_plans}

    # Index projection tables by class_config_id for quick routing.
    table_by_cc_id: dict[UUID, ProjectionTablePlan] = {}
    for table in plan.tables:
        cc_id = table.class_config_id
        if cc_id is None:
            continue
        table_by_cc_id[cc_id] = table

    created_ids, updated_ids, deleted_ids, rel_endpoints = _iter_changed_instance_ids(changes)
    upsert_ids = (created_ids | updated_ids | rel_endpoints) - deleted_ids

    # Filter ids to those in-scope for this projection plan.
    def in_scope(iid: UUID) -> bool:
        cc_id = after_cc_by_iid.get(iid)
        if cc_id is None:
            return False
        return cc_id in table_by_cc_id

    upsert_ids = {iid for iid in upsert_ids if in_scope(iid)}
    created_ids = {iid for iid in created_ids if iid in upsert_ids}

    delete_ids = {iid for iid in deleted_ids if before_cc_by_iid.get(iid) in table_by_cc_id}

    # Build deterministic SQL per table.
    upsert_sql_by_cc_id: dict[UUID, str] = {}
    delete_sql_by_cc_id: dict[UUID, str] = {}
    fk_columns_by_cc_id: dict[UUID, tuple[ProjectionColumnPlan, ...]] = {}
    for cc_id, table in table_by_cc_id.items():
        upsert_sql_by_cc_id[cc_id] = _build_upsert_sql(table)
        delete_sql_by_cc_id[cc_id] = _build_delete_sql(table)
        fk_columns_by_cc_id[cc_id] = tuple(c for c in table.columns if c.source == "fk_attribute")

    # ------------------------------------------------------------------
    # Phase A: CREATE + UPDATE (upserts)
    # ------------------------------------------------------------------

    # Determine required FK dependencies among instances being upserted, and identify optional
    # FK fields that must be deferred to avoid cycles (e.g. identity ↔ actor ↔ human).
    #
    # Catch-up replay can upsert a parent that already existed in the committed OIG base as an
    # "update" while inserting child rows created by the same commit into an empty DB. Treating
    # required FK targets across all upsert ids as dependencies preserves the commit-derived
    # projection without requiring DB reads or direct row seeding.
    upsert_deps: dict[UUID, set[UUID]] = {}
    deferred_fk_values: dict[UUID, dict[str, UUID]] = {}

    for iid in sorted(
        upsert_ids,
        key=lambda x: _stable_id_key(x, class_config_by_instance_id=after_cc_by_iid),
    ):
        ci = after_instances_by_id.get(iid)
        if ci is None:
            continue
        cc_id = after_cc_by_iid.get(iid)
        if cc_id is None:
            continue
        fk_cols = fk_columns_by_cc_id.get(cc_id, ())
        if not fk_cols:
            continue

        for col in fk_cols:
            target_id = _resolve_fk_value_with_attribute_fallback(
                ci=ci,
                column=col,
                rels_by_id=after_rels_by_id,
                enum_option_value_by_id=enum_option_value_by_id,
                dialect=plan.dialect,
            )
            if target_id is None:
                if not col.nullable:
                    raise LaneProjectionProjectorError(
                        "Missing required FK relationship while projecting created instance: "
                        f"instance_id={iid} class_config_id={cc_id} column={col.column_name} "
                        f"relationship_id={col.relationship_id}"
                    )
                continue

            if target_id == iid:
                continue

            # When an optional FK points at another newly-created object, clear it for the initial
            # insert. We'll restore it after all creates are staged.
            if col.nullable and target_id in created_ids:
                deferred_fk_values.setdefault(iid, {})[col.column_name] = target_id
                continue

            # Required FK references in the same projection batch must be staged first.
            if not col.nullable and target_id in upsert_ids:
                upsert_deps.setdefault(iid, set()).add(target_id)

    upsert_order = _toposort(upsert_ids, upsert_deps, class_config_by_instance_id=after_cc_by_iid)

    # Stage upserts in topo order with deferred optional FK values nulled out for creates.
    for iid in upsert_order:
        ci = after_instances_by_id.get(iid)
        if ci is None:
            continue
        cc_id = after_cc_by_iid.get(iid)
        if cc_id is None:
            continue
        table = table_by_cc_id.get(cc_id)
        if table is None:
            continue

        overrides: dict[str, object] = {k: None for k in deferred_fk_values.get(iid, {}).keys()}
        params = _project_row_values(
            ci=ci,
            table=table,
            rels_by_id=after_rels_by_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            enum_option_value_by_id=enum_option_value_by_id,
            dialect=plan.dialect,
            attribute_configs_by_id=attribute_configs_by_id,
            override_by_column=overrides or None,
        )
        session.add_insert(upsert_sql_by_cc_id[cc_id], params)

    update_ids = upsert_ids - created_ids

    # Phase B: restore deferred optional FK values.
    deferred_ids = sorted(
        deferred_fk_values.keys(),
        key=lambda x: _stable_id_key(x, class_config_by_instance_id=after_cc_by_iid),
    )
    for iid in deferred_ids:
        ci = after_instances_by_id.get(iid)
        if ci is None:
            continue
        cc_id = after_cc_by_iid.get(iid)
        if cc_id is None:
            continue
        table = table_by_cc_id.get(cc_id)
        if table is None:
            continue
        params = _project_row_values(
            ci=ci,
            table=table,
            rels_by_id=after_rels_by_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            enum_option_value_by_id=enum_option_value_by_id,
            dialect=plan.dialect,
            attribute_configs_by_id=attribute_configs_by_id,
        )
        session.add_insert(upsert_sql_by_cc_id[cc_id], params)

    # ------------------------------------------------------------------
    # Phase C: ASSOCIATIONS (join tables derived from relationship edges)
    # ------------------------------------------------------------------

    def edge_map(
        edges: Sequence[ClassInstanceRelationship],
    ) -> dict[UUID, tuple[UUID, UUID]]:
        out: dict[UUID, tuple[UUID, UUID]] = {}
        for edge in edges:
            edge_id = edge.id
            src = edge.source_class_instance_id
            tgt = edge.target_class_instance_id
            if not isinstance(edge_id, UUID) or not isinstance(src, UUID) or not isinstance(tgt, UUID):
                continue
            out[edge_id] = (src, tgt)
        return out

    assoc_insert_count = 0
    assoc_delete_count = 0
    for assoc in assoc_plans:
        rel_id = assoc.relationship_id
        before_edges = edge_map(before_rels_by_id.get(rel_id, ()))
        after_edges = edge_map(after_rels_by_id.get(rel_id, ()))

        removed = sorted(set(before_edges.keys()) - set(after_edges.keys()), key=str)
        for edge_id in removed:
            session.add_delete(
                assoc_delete_sql_by_rel_id[rel_id],
                (branch_id, projection_hash, edge_id),
            )
            assoc_delete_count += 1

        changed = [edge_id for edge_id, payload in after_edges.items() if before_edges.get(edge_id) != payload]
        changed.sort(key=str)
        for edge_id in changed:
            src_id, tgt_id = after_edges[edge_id]
            session.add_insert(
                assoc_upsert_sql_by_rel_id[rel_id],
                (branch_id, projection_hash, edge_id, src_id, tgt_id),
            )
            assoc_insert_count += 1

    # ------------------------------------------------------------------
    # Phase D: DELETE
    # ------------------------------------------------------------------

    delete_deps: dict[UUID, set[UUID]] = {}
    for iid in sorted(
        delete_ids,
        key=lambda x: _stable_id_key(x, class_config_by_instance_id=before_cc_by_iid),
    ):
        cc_id = before_cc_by_iid.get(iid)
        if cc_id is None:
            continue
        fk_cols = fk_columns_by_cc_id.get(cc_id, ())
        if not fk_cols:
            continue

        for col in fk_cols:
            instance = before_instances_by_id.get(iid)
            if instance is None:
                continue
            target_id = _resolve_fk_value_with_attribute_fallback(
                ci=instance,
                column=col,
                rels_by_id=before_rels_by_id,
                enum_option_value_by_id=enum_option_value_by_id,
                dialect=plan.dialect,
            )
            if target_id is None or target_id == iid:
                continue
            if target_id in delete_ids:
                delete_deps.setdefault(iid, set()).add(target_id)

    delete_topo = _toposort(delete_ids, delete_deps, class_config_by_instance_id=before_cc_by_iid)
    delete_order = list(reversed(delete_topo))

    for iid in delete_order:
        cc_id = before_cc_by_iid.get(iid)
        if cc_id is None:
            continue
        table = table_by_cc_id.get(cc_id)
        if table is None:
            continue
        instance = before_instances_by_id.get(iid)
        if instance is None:
            continue
        params = _delete_params(
            table=table,
            instance_id=iid,
            instance=instance,
            rels_by_id=before_rels_by_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            enum_option_value_by_id=enum_option_value_by_id,
            dialect=plan.dialect,
            attribute_configs_by_id=attribute_configs_by_id,
        )
        session.add_delete(delete_sql_by_cc_id[cc_id], params)

    return LaneProjectionWritePlan(
        create_count=len(created_ids),
        update_count=len(update_ids),
        delete_count=len(delete_order),
        deferred_fk_instance_count=len(deferred_fk_values),
        association_insert_count=assoc_insert_count,
        association_delete_count=assoc_delete_count,
    )
