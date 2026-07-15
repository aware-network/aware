from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
import json
import re
from typing import Any
from uuid import UUID

from aware_orm.filters import (
    EqFilter,
    GtFilter,
    GteFilter,
    InFilter,
    IsNullFilter,
    LikeFilter,
    LtFilter,
    LteFilter,
    NeqFilter,
    RelationPathFilter,
    SortOrder,
)
from aware_orm.query_spec import Predicate, PredicateGroup, QuerySpec
from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata
from aware_orm.session.backends import PersistenceBackendProtocol, QueryResult
from aware_orm.session.session import Session

from .projector import ServiceOntologyProjectionStore


def build_service_ontology_replica_orm_session(
    *,
    projection_store: ServiceOntologyProjectionStore,
    branch_id: UUID | None = None,
) -> Session:
    backend = ServiceOntologyReplicaReadOnlyBackend(
        projection_store=projection_store,
        session_branch_id=branch_id,
    )
    session = ServiceOntologyReplicaOrmSession(
        branch_id=branch_id,
        skip_db=False,
        backend=backend,
    )
    return session


class ServiceOntologyReplicaOrmSession(Session):
    """Session variant that hydrates replica rows without constructor autobind."""

    def _deserialize_to_model(self, model_class, row_data):
        from aware_orm.session.autobind import disable_autobind

        with disable_autobind():
            instance = super()._deserialize_to_model(model_class, row_data)
        self._bind_instance_branch(instance)
        return instance

    def imap_add(self, instance) -> None:
        self._bind_instance_branch(instance)
        super().imap_add(instance)

    def _bind_instance_branch(self, instance) -> None:
        set_branch_id = getattr(instance, "set_branch_id", None)
        if callable(set_branch_id):
            set_branch_id(self.branch_id)
        try:
            object.__setattr__(instance, "_branch_id", self.branch_id)
        except Exception:
            pass


@dataclass(slots=True)
class ServiceOntologyReplicaReadOnlyBackend(PersistenceBackendProtocol):
    """Read-only ORM backend over the Service-owned ontology replica projection."""

    projection_store: ServiceOntologyProjectionStore
    session_branch_id: UUID | None = None
    name: str = "service_ontology_replica"

    def enqueue_insert(self, sql: str, params: tuple[Any, ...]) -> None:
        raise _read_only_error()

    def enqueue_update(self, sql: str, params: tuple[Any, ...]) -> None:
        raise _read_only_error()

    def enqueue_delete(self, sql: str, params: tuple[Any, ...]) -> None:
        raise _read_only_error()

    def has_pending_operations(self) -> bool:
        return False

    def get_pending_counts(self) -> dict[str, int]:
        return {"inserts": 0, "updates": 0, "deletes": 0}

    def clear_pending(self) -> None:
        return None

    async def execute_query_spec(
        self,
        *,
        sql_metadata: SQLRuntimeMetadata,
        query_spec: QuerySpec,
        source_class_fqn: str | None,
        count: bool = False,
    ) -> QueryResult:
        _ = source_class_fqn
        rows = _projection_rows_for_metadata(
            projection_store=self.projection_store,
            metadata=sql_metadata,
        )
        rows = tuple(
            row
            for row in rows
            if _query_predicate_matches(
                row=row,
                metadata=sql_metadata,
                predicate=query_spec.where,
                session_branch_id=self.session_branch_id,
            )
        )
        if count:
            return [{"count": len(rows)}]
        rows = _order_query_spec_rows(
            rows=rows,
            metadata=sql_metadata,
            order_by=query_spec.order_by,
        )
        if query_spec.page is not None:
            rows = rows[query_spec.page.offset or 0 :]
            if query_spec.page.limit is not None:
                rows = rows[: query_spec.page.limit]
        return [dict(row.payload) for row in rows]

    async def execute_read(self, sql: str, params: tuple[Any, ...]) -> QueryResult:
        _ = sql, params
        raise RuntimeError(
            "Service ontology replica ORM sessions do not execute SQL reads. "
            "Use QuerySpec-backed generated-model reads such as by_id(...), "
            "one(...), where(...), many(...), or Model.query().where(...)."
        )

    async def commit(self) -> None:
        raise _read_only_error()

    async def rollback(self) -> None:
        return None


def _projection_rows_for_metadata(
    *,
    projection_store: ServiceOntologyProjectionStore,
    metadata: SQLRuntimeMetadata,
) -> tuple["_ProjectionModelRow", ...]:
    return tuple(
        _ProjectionModelRow.from_projection_row(
            row=row,
            metadata=metadata,
        )
        for row in projection_store.list_class_instances(
            class_config_id=metadata.class_config_id,
            include_deleted=False,
        )
    )


@dataclass(frozen=True, slots=True)
class _Condition:
    column: str
    operator: str
    value: object = None
    values: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class _ProjectionModelRow:
    branch_id: str
    projection_hash: str
    payload: Mapping[str, object]

    @classmethod
    def from_projection_row(
        cls,
        *,
        row: Mapping[str, Any],
        metadata: SQLRuntimeMetadata,
    ) -> "_ProjectionModelRow":
        attributes = _json_object(row.get("attributes_json"))
        class_instance_id = _required_text(row.get("class_instance_id"))
        source_object_id = _optional_text(attributes.get("source_object_id"))
        payload: dict[str, object] = {
            "id": source_object_id or class_instance_id,
            "class_instance_id": class_instance_id,
            "branch_id": _required_text(row.get("branch_id")),
            "projection_hash": _required_text(row.get("projection_hash")),
        }
        for attribute in sorted(set(metadata.persisted_attributes or ())):
            if attribute == "id":
                continue
            if attribute == "branch_id":
                payload[attribute] = payload["branch_id"]
                continue
            if attribute == "projection_hash":
                payload[attribute] = payload["projection_hash"]
                continue
            if attribute in attributes:
                payload[attribute] = attributes[attribute]
        for key, value in attributes.items():
            payload.setdefault(str(key), value)
        return cls(
            branch_id=str(payload["branch_id"]),
            projection_hash=str(payload["projection_hash"]),
            payload=payload,
        )

    def value_for_column(
        self,
        *,
        column: str,
        metadata: SQLRuntimeMetadata,
    ) -> object:
        attribute = _attribute_for_column(column=column, metadata=metadata)
        if attribute == "id":
            return self.payload.get("id")
        if attribute == "branch_id":
            return self.branch_id
        if attribute == "projection_hash":
            return self.projection_hash
        return self.payload.get(attribute)


def _query_predicate_matches(
    *,
    row: _ProjectionModelRow,
    metadata: SQLRuntimeMetadata,
    predicate: Predicate | None,
    session_branch_id: UUID | None,
) -> bool:
    if not _row_matches_session_branch(row=row, session_branch_id=session_branch_id):
        return False
    if predicate is None:
        return True
    return _query_predicate_condition_matches(
        row=row,
        metadata=metadata,
        predicate=predicate,
    )


def _query_predicate_condition_matches(
    *,
    row: _ProjectionModelRow,
    metadata: SQLRuntimeMetadata,
    predicate: Predicate,
) -> bool:
    if isinstance(predicate, PredicateGroup):
        predicates = tuple(predicate.predicates)
        if predicate.op == "and":
            return all(
                _query_predicate_condition_matches(
                    row=row,
                    metadata=metadata,
                    predicate=child,
                )
                for child in predicates
            )
        if predicate.op == "or":
            return any(
                _query_predicate_condition_matches(
                    row=row,
                    metadata=metadata,
                    predicate=child,
                )
                for child in predicates
            )
        raise RuntimeError(
            "Service ontology replica ORM QuerySpec predicate group has "
            f"unsupported op: {predicate.op!r}."
        )

    condition = _condition_from_query_predicate(predicate)
    value = row.value_for_column(column=condition.column, metadata=metadata)
    return _condition_matches(condition=condition, value=value)


def _condition_from_query_predicate(predicate: Predicate) -> _Condition:
    if isinstance(predicate, RelationPathFilter):
        raise RuntimeError(
            "Service ontology replica ORM QuerySpec does not support relation-path "
            "predicates yet. Query relationship foreign-key fields directly, or "
            "use a backend with GraphSQL relationship support."
        )
    if isinstance(predicate, EqFilter):
        return _Condition(column=predicate.column, operator="=", value=predicate.value)
    if isinstance(predicate, NeqFilter):
        return _Condition(column=predicate.column, operator="!=", value=predicate.value)
    if isinstance(predicate, GtFilter):
        return _Condition(column=predicate.column, operator=">", value=predicate.value)
    if isinstance(predicate, GteFilter):
        return _Condition(column=predicate.column, operator=">=", value=predicate.value)
    if isinstance(predicate, LtFilter):
        return _Condition(column=predicate.column, operator="<", value=predicate.value)
    if isinstance(predicate, LteFilter):
        return _Condition(column=predicate.column, operator="<=", value=predicate.value)
    if isinstance(predicate, InFilter):
        return _Condition(
            column=predicate.column,
            operator="IN",
            values=tuple(predicate.values),
        )
    if isinstance(predicate, LikeFilter):
        return _Condition(
            column=predicate.column,
            operator="LIKE",
            value=predicate.pattern,
        )
    if isinstance(predicate, IsNullFilter):
        return _Condition(
            column=predicate.column,
            operator="IS NULL" if predicate.is_null else "IS NOT NULL",
        )
    raise TypeError(
        "Service ontology replica ORM QuerySpec received unsupported predicate "
        f"type: {type(predicate).__name__}."
    )


def _condition_matches(*, condition: _Condition, value: object) -> bool:
    operator = condition.operator
    if operator == "=":
        return _normalized(value) == _normalized(condition.value)
    if operator in {"!=", "<>"}:
        return _normalized(value) != _normalized(condition.value)
    if operator == "IN":
        normalized_value = _normalized(value)
        return any(normalized_value == _normalized(item) for item in condition.values)
    if operator == "LIKE":
        return _like_matches(value=value, pattern=condition.value)
    if operator == "IS NULL":
        return value is None
    if operator == "IS NOT NULL":
        return value is not None
    if operator in {">", ">=", "<", "<="}:
        return _compare(value=value, operator=operator, expected=condition.value)
    raise RuntimeError(
        "Service ontology replica ORM backend does not support operator: "
        f"{operator!r}"
    )


def _row_matches_session_branch(
    *,
    row: _ProjectionModelRow,
    session_branch_id: UUID | None,
) -> bool:
    return session_branch_id is None or _normalized(row.branch_id) == _normalized(
        session_branch_id
    )


def _order_query_spec_rows(
    *,
    rows: tuple[_ProjectionModelRow, ...],
    metadata: SQLRuntimeMetadata,
    order_by: tuple[object, ...],
) -> tuple[_ProjectionModelRow, ...]:
    ordered = rows
    for order in reversed(tuple(order_by or ())):
        column = getattr(order, "column", None)
        if not isinstance(column, str) or not column.strip():
            raise RuntimeError(
                "Service ontology replica ORM QuerySpec order requires a "
                "non-empty column."
            )
        direction = getattr(order, "direction", SortOrder.ASC)
        ordered = tuple(
            sorted(
                ordered,
                key=lambda row: _sort_value(
                    row.value_for_column(column=column, metadata=metadata)
                ),
                reverse=_is_descending_order(direction),
            )
        )
    return ordered


def _is_descending_order(direction: object) -> bool:
    value = getattr(direction, "value", direction)
    return str(value or "").strip().lower() == SortOrder.DESC.value


def _attribute_for_column(
    *,
    column: str,
    metadata: SQLRuntimeMetadata,
) -> str:
    column_token = column.strip().strip('"')
    if column_token in {"id", "branch_id", "projection_hash"}:
        return column_token
    inverse = {
        column_name: attribute
        for attribute, column_name in (metadata.column_by_attribute or {}).items()
    }
    return inverse.get(column_token, column_token)


def _like_matches(*, value: object, pattern: object) -> bool:
    if value is None:
        return False
    text = str(value)
    regex = re.escape(str(pattern))
    regex = regex.replace("%", ".*").replace("_", ".")
    return re.fullmatch(regex, text) is not None


def _compare(*, value: object, operator: str, expected: object) -> bool:
    if value is None or expected is None:
        return False
    left = _comparable(value)
    right = _comparable(expected)
    if operator == ">":
        return left > right
    if operator == ">=":
        return left >= right
    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    raise RuntimeError(f"Unsupported comparison operator: {operator!r}")


def _comparable(value: object) -> object:
    if isinstance(value, int | float):
        return value
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return str(value)


def _normalized(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    return value


def _sort_value(value: object) -> tuple[int, object]:
    if value is None:
        return (1, "")
    return (0, _comparable(value))


def _json_object(value: object) -> dict[str, object]:
    if not isinstance(value, str) or not value.strip():
        return {}
    decoded = json.loads(value)
    return dict(decoded) if isinstance(decoded, Mapping) else {}


def _required_text(value: object) -> str:
    token = str(value or "").strip()
    if not token:
        raise RuntimeError("Service ontology replica projection row is missing text.")
    return token


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    return token or None


def _read_only_error() -> PermissionError:
    return PermissionError(
        "Service ontology replica ORM sessions are read-only. Mutations must "
        "flow through Ontology/Environment commits and then fan out into the "
        "Service replica projection."
    )


__all__ = [
    "ServiceOntologyReplicaReadOnlyBackend",
    "ServiceOntologyReplicaOrmSession",
    "build_service_ontology_replica_orm_session",
]
