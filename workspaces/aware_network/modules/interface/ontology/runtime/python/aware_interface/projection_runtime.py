from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from aware_interface.commit_materialization import InterfaceMaterializedLane
from aware_interface.lane_stores import InterfaceLaneStores, LocalProjectionCursorRecord
from aware_interface.local_db import InterfaceLocalDb
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_orm.projection.plan import ProjectionPlan, ProjectionPlanCache


_SQLITE_PROJECTOR_ID = "aware_meta.sqlite_projection_plan.v0"


class _ProjectionWriteSession(Protocol):
    def add_delete(self, sql: str, params: tuple[object, ...]) -> None: ...

    def add_insert(self, sql: str, params: tuple[object, ...]) -> None: ...


@dataclass(frozen=True, slots=True)
class InterfaceProjectionPlanBundle:
    manifest_path: Path
    plan_cache: ProjectionPlanCache
    enum_option_value_by_id: dict[str, str]

    def resolve_plan(self, *, projection_hash: str) -> ProjectionPlan | None:
        return self.plan_cache.get(dialect="sqlite", projection_hash=projection_hash)


@dataclass(frozen=True, slots=True)
class InterfaceProjectionRuntimeResult:
    projector_id: str
    projection_hash: str
    head_commit_id: str
    cursor_id: str
    projected: bool
    class_row_count: int = 0
    association_row_count: int = 0


class InterfaceProjectionRuntime:
    _db: InterfaceLocalDb
    _stores: InterfaceLaneStores
    _bundles_by_projection_hash: dict[str, InterfaceProjectionPlanBundle]
    _last_projected_head_by_cursor_id: dict[str, str]

    def __init__(self, *, db: InterfaceLocalDb, stores: InterfaceLaneStores) -> None:
        self._db = db
        self._stores = stores
        self._bundles_by_projection_hash = {}
        self._last_projected_head_by_cursor_id = {}

    def register_bundle(self, bundle: InterfaceProjectionPlanBundle) -> None:
        for plan in bundle.plan_cache.all():
            self._bundles_by_projection_hash[plan.projection_hash] = bundle

    def resolve_bundle(
        self, *, projection_hash: str
    ) -> InterfaceProjectionPlanBundle | None:
        return self._bundles_by_projection_hash.get(projection_hash)

    def resolve_plan(
        self, *, projection_hash: str
    ) -> tuple[ProjectionPlan, InterfaceProjectionPlanBundle] | None:
        bundle = self.resolve_bundle(projection_hash=projection_hash)
        if bundle is None:
            return None
        plan = bundle.resolve_plan(projection_hash=projection_hash)
        if plan is None:
            return None
        return plan, bundle

    async def project_materialized_lane(
        self,
        *,
        branch_id: str,
        materialized_lane: InterfaceMaterializedLane,
        strict: bool = True,
    ) -> InterfaceProjectionRuntimeResult:
        resolved = self.resolve_plan(projection_hash=materialized_lane.projection_hash)
        if resolved is None:
            if strict:
                raise ValueError(
                    "Interface projection runtime missing compiled sqlite plan: "
                    + f"projection_hash={materialized_lane.projection_hash}"
                )
            return InterfaceProjectionRuntimeResult(
                projector_id=_SQLITE_PROJECTOR_ID,
                projection_hash=materialized_lane.projection_hash,
                head_commit_id=materialized_lane.target_commit_id,
                cursor_id=_projection_cursor_id(
                    branch_id=branch_id,
                    projection_hash=materialized_lane.projection_hash,
                    projector_id=_SQLITE_PROJECTOR_ID,
                ),
                projected=False,
            )

        plan, bundle = resolved
        cursor_id = _projection_cursor_id(
            branch_id=branch_id,
            projection_hash=materialized_lane.projection_hash,
            projector_id=_SQLITE_PROJECTOR_ID,
        )
        head_commit_id = materialized_lane.target_commit_id
        cached_head = self._last_projected_head_by_cursor_id.get(cursor_id)
        if cached_head == head_commit_id:
            return InterfaceProjectionRuntimeResult(
                projector_id=_SQLITE_PROJECTOR_ID,
                projection_hash=materialized_lane.projection_hash,
                head_commit_id=head_commit_id,
                cursor_id=cursor_id,
                projected=False,
            )

        persisted_cursor = await self._stores.load_projection_cursor(
            branch_id=branch_id,
            cursor_id=cursor_id,
            projection_hash=materialized_lane.projection_hash,
        )
        if (
            persisted_cursor is not None
            and persisted_cursor.head_commit_id == head_commit_id
        ):
            self._last_projected_head_by_cursor_id[cursor_id] = head_commit_id
            return InterfaceProjectionRuntimeResult(
                projector_id=_SQLITE_PROJECTOR_ID,
                projection_hash=materialized_lane.projection_hash,
                head_commit_id=head_commit_id,
                cursor_id=cursor_id,
                projected=False,
            )

        session = self._db.new_session()
        try:
            class_row_count, association_row_count = _stage_sqlite_projection_rewrite(
                session=session,
                plan=plan,
                branch_id=branch_id,
                materialized_lane=materialized_lane,
                enum_option_value_by_id=bundle.enum_option_value_by_id,
            )
            await session.commit()
        finally:
            self._db.close_session(session)

        await self._stores.save_projection_cursor(
            LocalProjectionCursorRecord(
                id=cursor_id,
                branch_id=branch_id,
                projection_hash=materialized_lane.projection_hash,
                head_commit_id=head_commit_id,
                projector_id=_SQLITE_PROJECTOR_ID,
                graph_hash_post=str(materialized_lane.graph.hash or ""),
                v=1,
            )
        )
        self._last_projected_head_by_cursor_id[cursor_id] = head_commit_id

        return InterfaceProjectionRuntimeResult(
            projector_id=_SQLITE_PROJECTOR_ID,
            projection_hash=materialized_lane.projection_hash,
            head_commit_id=head_commit_id,
            cursor_id=cursor_id,
            projected=True,
            class_row_count=class_row_count,
            association_row_count=association_row_count,
        )


def _projection_cursor_id(
    *, branch_id: str, projection_hash: str, projector_id: str
) -> str:
    return f"{branch_id}:{projection_hash}:{projector_id}"


def _stage_sqlite_projection_rewrite(
    *,
    session: object,
    plan: ProjectionPlan,
    branch_id: str,
    materialized_lane: InterfaceMaterializedLane,
    enum_option_value_by_id: dict[str, str],
) -> tuple[int, int]:
    if plan.dialect != "sqlite":
        raise ValueError(
            f"Interface projection runtime requires sqlite plan dialect, got {plan.dialect!r}"
        )

    graph = materialized_lane.graph
    projection_hash = materialized_lane.projection_hash
    rels_by_id = _relationships_by_id(graph.class_instance_relationships)
    instances_by_class_id = _instances_by_class_id(graph.class_instances)

    assoc_table_names = sorted(
        {_sqlite_table_name(assoc.association_table_key) for assoc in plan.associations}
    )
    for table_name in assoc_table_names:
        _session_add_delete(
            session,
            f"DELETE FROM {table_name} WHERE branch_id = $1 AND projection_hash = $2",
            (branch_id, projection_hash),
        )

    class_table_names = sorted(
        {_sqlite_table_name(table.table_key) for table in plan.tables}
    )
    for table_name in class_table_names:
        _session_add_delete(
            session,
            f"DELETE FROM {table_name} WHERE branch_id = $1 AND projection_hash = $2",
            (branch_id, projection_hash),
        )

    class_row_count = 0
    for table in sorted(
        plan.tables, key=lambda item: (item.table_key, str(item.class_config_id or ""))
    ):
        class_config_id = table.class_config_id
        if class_config_id is None:
            continue
        table_name = _sqlite_table_name(table.table_key)
        column_names = [column.column_name for column in table.columns]
        if not column_names:
            continue
        sql = _build_sqlite_upsert_sql(
            table_name=table_name,
            column_names=tuple(column_names),
            primary_key=table.primary_key or ("id",),
        )
        instances = sorted(
            instances_by_class_id.get(str(class_config_id), ()),
            key=lambda class_instance: str(class_instance.id),
        )
        for class_instance in instances:
            values = tuple(
                _project_column_value(
                    class_instance=class_instance,
                    column_source=column.source,
                    column_name=column.column_name,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    attribute_config_id=(
                        str(column.attribute_config_id)
                        if column.attribute_config_id is not None
                        else None
                    ),
                    relationship_id=(
                        str(column.relationship_id)
                        if column.relationship_id is not None
                        else None
                    ),
                    direction=column.direction,
                    rels_by_id=rels_by_id,
                    enum_option_value_by_id=enum_option_value_by_id,
                )
                for column in table.columns
            )
            _session_add_insert(session, sql, values)
            class_row_count += 1

    association_row_count = 0
    for assoc in sorted(
        plan.associations,
        key=lambda item: (item.association_table_key, str(item.relationship_id)),
    ):
        table_name = _sqlite_table_name(assoc.association_table_key)
        sql = (
            f"INSERT INTO {table_name} (branch_id, projection_hash, id, {assoc.source_fk_column}, {assoc.target_fk_column}) "
            + "VALUES($1, $2, $3, $4, $5) "
            + "ON CONFLICT(branch_id, projection_hash, id) DO UPDATE SET "
            + f"{assoc.source_fk_column} = excluded.{assoc.source_fk_column}, "
            + f"{assoc.target_fk_column} = excluded.{assoc.target_fk_column}"
        )
        edges = sorted(
            rels_by_id.get(str(assoc.relationship_id), ()),
            key=lambda relationship: str(relationship.id),
        )
        for relationship in edges:
            _session_add_insert(
                session,
                sql,
                (
                    branch_id,
                    projection_hash,
                    str(relationship.id),
                    str(relationship.source_class_instance_id),
                    str(relationship.target_class_instance_id),
                ),
            )
            association_row_count += 1

    return class_row_count, association_row_count


def _build_sqlite_upsert_sql(
    *,
    table_name: str,
    column_names: tuple[str, ...],
    primary_key: tuple[str, ...],
) -> str:
    placeholders = ", ".join(f"${index}" for index in range(1, len(column_names) + 1))
    update_columns = [column for column in column_names if column not in primary_key]
    if update_columns:
        update_clause = " DO UPDATE SET " + ", ".join(
            f"{column} = excluded.{column}" for column in update_columns
        )
    else:
        update_clause = " DO NOTHING"
    return (
        f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES({placeholders}) "
        + f"ON CONFLICT({', '.join(primary_key)}){update_clause}"
    )


def _project_column_value(
    *,
    class_instance: ClassInstance,
    column_source: str,
    column_name: str,
    branch_id: str,
    projection_hash: str,
    attribute_config_id: str | None,
    relationship_id: str | None,
    direction: str | None,
    rels_by_id: dict[str, list[ClassInstanceRelationship]],
    enum_option_value_by_id: dict[str, str],
) -> object | None:
    if column_source == "id":
        return str(class_instance.id)
    if column_source == "branch_id":
        return branch_id
    if column_source == "projection_hash":
        return projection_hash
    if column_source == "attribute":
        return _decode_attribute_value(
            class_instance=class_instance,
            attribute_config_id=attribute_config_id,
            enum_option_value_by_id=enum_option_value_by_id,
        )
    if column_source == "fk_attribute":
        return _resolve_fk_value(
            class_instance=class_instance,
            relationship_id=relationship_id,
            direction=direction,
            rels_by_id=rels_by_id,
        )
    raise ValueError(
        f"Unsupported sqlite projection column source {column_source!r} for column {column_name!r}"
    )


def _decode_attribute_value(
    *,
    class_instance: ClassInstance,
    attribute_config_id: str | None,
    enum_option_value_by_id: dict[str, str],
) -> object | None:
    if attribute_config_id is None or not attribute_config_id.strip():
        return None

    attrs_by_id: dict[str, Attribute] = {
        str(attribute.attribute_config_id): attribute
        for attribute in (class_instance.attributes or [])
    }
    attribute = attrs_by_id.get(attribute_config_id)
    if attribute is None:
        return None

    root: AttributeValue = attribute.value_root

    enum_option_id = root.enum_option_id
    if enum_option_id is not None:
        key = str(enum_option_id)
        return enum_option_value_by_id.get(key, key)

    primitive_value = root.primitive_value
    if primitive_value is not None:
        payload: object = primitive_value.get("value", primitive_value)
        if isinstance(payload, bool):
            return 1 if payload else 0
        if isinstance(payload, (int, float, str)):
            return payload
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    return json.dumps(
        root.model_dump(mode="json", exclude_none=True),
        sort_keys=True,
        separators=(",", ":"),
    )


def _resolve_fk_value(
    *,
    class_instance: ClassInstance,
    relationship_id: str | None,
    direction: str | None,
    rels_by_id: dict[str, list[ClassInstanceRelationship]],
) -> str | None:
    if relationship_id is None or not relationship_id.strip():
        return None
    edges = rels_by_id.get(relationship_id)
    if not edges:
        return None

    normalized_direction = (direction or "").strip().lower()
    class_instance_id = class_instance.id
    if normalized_direction == "forward":
        for relationship in edges:
            if relationship.source_class_instance_id == class_instance_id:
                return str(relationship.target_class_instance_id)
        return None
    if normalized_direction == "reverse":
        for relationship in edges:
            if relationship.target_class_instance_id == class_instance_id:
                return str(relationship.source_class_instance_id)
        return None
    return None


def _relationships_by_id(
    relationships: list[ClassInstanceRelationship],
) -> dict[str, list[ClassInstanceRelationship]]:
    rels_by_id: dict[str, list[ClassInstanceRelationship]] = {}
    for relationship in relationships:
        rels_by_id.setdefault(
            str(relationship.class_config_relationship_id), []
        ).append(relationship)
    return rels_by_id


def _instances_by_class_id(
    class_instances: list[ClassInstance],
) -> dict[str, list[ClassInstance]]:
    out: dict[str, list[ClassInstance]] = {}
    for class_instance in class_instances:
        out.setdefault(str(class_instance.class_config_id), []).append(class_instance)
    return out


def _sqlite_table_name(table_key: str) -> str:
    token = (table_key or "").strip()
    if "." not in token:
        return token
    return token.rsplit(".", 1)[-1]


def _session_add_delete(session: object, sql: str, params: tuple[object, ...]) -> None:
    cast(_ProjectionWriteSession, session).add_delete(sql, params)


def _session_add_insert(session: object, sql: str, params: tuple[object, ...]) -> None:
    cast(_ProjectionWriteSession, session).add_insert(sql, params)


__all__ = [
    "InterfaceProjectionPlanBundle",
    "InterfaceProjectionRuntime",
    "InterfaceProjectionRuntimeResult",
]
