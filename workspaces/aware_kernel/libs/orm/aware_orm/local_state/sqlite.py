from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
import json
import sqlite3
from typing import Generic, Literal, Protocol, TypeVar, cast
from urllib.parse import quote
from uuid import UUID

from aware_orm.models.orm_model import ORMModel


ModelT = TypeVar("ModelT", bound=ORMModel)
SQLiteOrmOrderDirection = Literal["ASC", "DESC"]
SQLiteOrmPredicateOperator = Literal["="]
SQLiteOrmTableHealthStatus = Literal["missing", "ok", "schema_drift"]
SQLiteOrmSchemaHealthStatus = Literal["ok", "schema_drift"]
SQLiteOrmStorageIndex = tuple[bool, tuple[str, ...]]


class SQLiteOrmModelStoreError(ValueError):
    """Raised when a SQLite ORM model-store descriptor is invalid."""


class SQLiteOrmSchemaDriftError(RuntimeError):
    """Raised when SQLite schema installation or drift repair fails."""


class SQLiteOrmSchemaTable(Protocol):
    @property
    def table(self) -> str: ...

    @property
    def columns(self) -> tuple[str, ...]: ...

    def table_columns(
        self, connection: sqlite3.Connection
    ) -> tuple[str, ...] | None: ...


@dataclass(frozen=True, slots=True)
class SQLiteOrmPredicate:
    column: str
    value: object
    operator: SQLiteOrmPredicateOperator = "="


@dataclass(frozen=True, slots=True)
class SQLiteOrmOrder:
    column: str
    direction: SQLiteOrmOrderDirection = "ASC"


@dataclass(frozen=True, slots=True)
class SQLiteOrmIndex:
    name: str
    unique: bool
    columns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SQLiteOrmTableHealth:
    table_name: str
    status: SQLiteOrmTableHealthStatus
    expected_columns: tuple[str, ...]
    actual_columns: tuple[str, ...] | None
    missing_columns: tuple[str, ...]
    extra_columns: tuple[str, ...]
    expected_indexes: tuple[SQLiteOrmStorageIndex, ...]
    actual_indexes: tuple[SQLiteOrmStorageIndex, ...]
    missing_indexes: tuple[SQLiteOrmStorageIndex, ...]


@dataclass(frozen=True, slots=True)
class SQLiteOrmSchemaHealth:
    schema_contract: str
    schema_version: int
    status: SQLiteOrmSchemaHealthStatus
    table_count: int
    healthy_table_count: int
    storage_index_coverage: bool
    tables: tuple[SQLiteOrmTableHealth, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SQLiteOrmSchemaTableDescriptor:
    table: str
    columns: tuple[str, ...]
    json_columns: frozenset[str] = frozenset()
    storage_indexes: tuple[SQLiteOrmStorageIndex, ...] = ()

    def __post_init__(self) -> None:
        _validate_sql_identifier(self.table, "table")
        if not self.columns:
            raise SQLiteOrmModelStoreError(f"{self.table}: columns must be non-empty")
        duplicate_columns = _duplicates(self.columns)
        if duplicate_columns:
            raise SQLiteOrmModelStoreError(
                f"{self.table}: duplicate columns: {', '.join(duplicate_columns)}"
            )
        for column in self.columns:
            _validate_sql_identifier(column, f"{self.table} column")
        undeclared_json_columns = sorted(set(self.json_columns) - set(self.columns))
        if undeclared_json_columns:
            raise SQLiteOrmModelStoreError(
                f"{self.table}: json columns are not table columns: "
                + ", ".join(undeclared_json_columns)
            )
        for _unique, columns in self.storage_indexes:
            if not columns:
                raise SQLiteOrmModelStoreError(
                    f"{self.table}: storage index has no columns"
                )
            unknown_columns = sorted(set(columns) - set(self.columns))
            if unknown_columns:
                raise SQLiteOrmModelStoreError(
                    f"{self.table}: storage index columns are not table columns: "
                    + ", ".join(unknown_columns)
                )

    def table_columns(self, connection: sqlite3.Connection) -> tuple[str, ...] | None:
        return sqlite_table_columns(connection, self.table)

    def model_table(self, model_type: type[ModelT]) -> "SQLiteOrmModelTable[ModelT]":
        return SQLiteOrmModelTable(
            table=self.table,
            columns=self.columns,
            model_type=model_type,
            json_columns=self.json_columns,
        )


@dataclass(frozen=True, slots=True)
class SQLiteOrmSchemaContractDescriptor:
    schema_contract: str
    schema_version: int
    tables: tuple[SQLiteOrmSchemaTableDescriptor, ...]
    payload_schema: str = ""
    source_path: Path | None = None

    def __post_init__(self) -> None:
        if not self.schema_contract.strip():
            raise SQLiteOrmModelStoreError("schema_contract must be non-empty")
        if self.schema_version < 1:
            raise SQLiteOrmModelStoreError("schema_version must be positive")
        if not self.tables:
            raise SQLiteOrmModelStoreError("schema contract tables must be non-empty")
        duplicate_tables = _duplicates(tuple(table.table for table in self.tables))
        if duplicate_tables:
            raise SQLiteOrmModelStoreError(
                "duplicate schema contract tables: " + ", ".join(duplicate_tables)
            )

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
        *,
        source_path: Path | None = None,
    ) -> "SQLiteOrmSchemaContractDescriptor":
        tables_payload = payload.get("tables")
        if not isinstance(tables_payload, (list, tuple)):
            raise SQLiteOrmModelStoreError("schema contract payload requires tables")
        return cls(
            payload_schema=_optional_text(payload.get("schema")) or "",
            schema_contract=_required_text(payload, "schema_contract"),
            schema_version=_required_positive_int(payload, "schema_version"),
            tables=tuple(
                _schema_table_descriptor_from_payload(table_payload)
                for table_payload in tables_payload
            ),
            source_path=source_path,
        )

    @classmethod
    def from_json_path(
        cls,
        path: Path,
    ) -> "SQLiteOrmSchemaContractDescriptor":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise SQLiteOrmModelStoreError("schema contract JSON must be an object")
        return cls.from_payload(cast(Mapping[str, object], payload), source_path=path)

    @property
    def expected_storage_indexes(
        self,
    ) -> Mapping[str, tuple[SQLiteOrmStorageIndex, ...]]:
        return {table.table: table.storage_indexes for table in self.tables}

    def model_tables(
        self,
        model_types_by_table: Mapping[str, type[ORMModel]],
    ) -> tuple["SQLiteOrmModelTable[ORMModel]", ...]:
        tables: list[SQLiteOrmModelTable[ORMModel]] = []
        for table in self.tables:
            model_type = model_types_by_table.get(table.table)
            if model_type is None:
                raise SQLiteOrmModelStoreError(
                    f"{table.table}: schema contract has no model type binding"
                )
            tables.append(table.model_table(model_type))
        return tuple(tables)

    def bind_schema_contract(
        self,
        *,
        schema_path: Path,
        model_types_by_table: Mapping[str, type[ORMModel]],
    ) -> "SQLiteOrmSchemaContract":
        return SQLiteOrmSchemaContract(
            schema_contract=self.schema_contract,
            schema_version=self.schema_version,
            schema=SQLiteOrmSchema(
                schema_path=schema_path,
                tables=self.model_tables(model_types_by_table),
            ),
            expected_storage_indexes=self.expected_storage_indexes,
        )


@dataclass(frozen=True, slots=True)
class SQLiteOrmModelTable(Generic[ModelT]):
    table: str
    columns: tuple[str, ...]
    model_type: type[ModelT]
    json_columns: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        _validate_sql_identifier(self.table, "table")
        if not self.columns:
            raise SQLiteOrmModelStoreError(f"{self.table}: columns must be non-empty")
        duplicate_columns = _duplicates(self.columns)
        if duplicate_columns:
            raise SQLiteOrmModelStoreError(
                f"{self.table}: duplicate columns: {', '.join(duplicate_columns)}"
            )
        for column in self.columns:
            _validate_sql_identifier(column, f"{self.table} column")
        undeclared_json_columns = sorted(set(self.json_columns) - set(self.columns))
        if undeclared_json_columns:
            raise SQLiteOrmModelStoreError(
                f"{self.table}: json columns are not table columns: "
                + (", ".join(undeclared_json_columns))
            )
        model_fields = set(getattr(self.model_type, "model_fields", ()))
        missing_model_fields = sorted(set(self.columns) - model_fields)
        if missing_model_fields:
            raise SQLiteOrmModelStoreError(
                f"{self.table}: columns missing from {self.model_type.__name__}: "
                + ", ".join(missing_model_fields)
            )

    def replace(self, connection: sqlite3.Connection, model: ModelT) -> None:
        _ = connection.execute(
            f"""
            INSERT OR REPLACE INTO {self.table} (
                {", ".join(self.columns)}
            ) VALUES ({", ".join("?" for _ in self.columns)})
            """,
            tuple(
                sqlite_value_for_model(cast(object, getattr(model, column)))
                for column in self.columns
            ),
        )

    def delete_where(
        self,
        connection: sqlite3.Connection,
        *,
        predicates: Sequence[SQLiteOrmPredicate],
    ) -> int:
        where_sql, params = self._where_clause(predicates)
        cursor = connection.execute(
            f"DELETE FROM {self.table} WHERE {where_sql}",
            params,
        )
        return int(cursor.rowcount)

    def select_one(
        self,
        connection: sqlite3.Connection,
        *,
        predicates: Sequence[SQLiteOrmPredicate],
        order_by: Sequence[SQLiteOrmOrder] = (),
    ) -> ModelT | None:
        rows = self.select_many(
            connection,
            predicates=predicates,
            order_by=order_by,
            limit=1,
        )
        return rows[0] if rows else None

    def select_many(
        self,
        connection: sqlite3.Connection,
        *,
        predicates: Sequence[SQLiteOrmPredicate],
        order_by: Sequence[SQLiteOrmOrder] = (),
        limit: int | None = None,
    ) -> list[ModelT]:
        where_sql, params = self._where_clause(predicates)
        query = f"""
            SELECT {", ".join(self.columns)}
            FROM {self.table}
            WHERE {where_sql}
        """
        if order_by:
            query += f"\nORDER BY {self._order_clause(order_by)}"
        if limit is not None:
            if limit < 1:
                raise SQLiteOrmModelStoreError("limit must be positive")
            query += f"\nLIMIT {limit}"
        rows = cast(list[sqlite3.Row], connection.execute(query, params).fetchall())
        return [self.model_from_row(row) for row in rows]

    def model_from_row(self, row: sqlite3.Row) -> ModelT:
        payload = {column: cast(object, row[column]) for column in self.columns}
        for column in self.json_columns:
            payload[column] = json_payload(payload.get(column))
        return self.model_type.model_validate(payload)

    def table_columns(self, connection: sqlite3.Connection) -> tuple[str, ...] | None:
        return sqlite_table_columns(connection, self.table)

    def _where_clause(
        self,
        predicates: Sequence[SQLiteOrmPredicate],
    ) -> tuple[str, tuple[object, ...]]:
        if not predicates:
            raise SQLiteOrmModelStoreError(
                f"{self.table}: predicates must be non-empty"
            )
        clauses: list[str] = []
        params: list[object] = []
        for predicate in predicates:
            self._validate_column(predicate.column)
            if predicate.operator != "=":
                raise SQLiteOrmModelStoreError(
                    f"{self.table}: unsupported predicate operator {predicate.operator!r}"
                )
            clauses.append(f"{predicate.column} = ?")
            params.append(sqlite_value_for_model(predicate.value))
        return " AND ".join(clauses), tuple(params)

    def _order_clause(self, order_by: Sequence[SQLiteOrmOrder]) -> str:
        clauses: list[str] = []
        for order in order_by:
            self._validate_column(order.column)
            if order.direction not in ("ASC", "DESC"):
                raise SQLiteOrmModelStoreError(
                    f"{self.table}: unsupported order direction {order.direction!r}"
                )
            clauses.append(f"{order.column} {order.direction}")
        return ", ".join(clauses)

    def _validate_column(self, column: str) -> None:
        if column not in self.columns:
            raise SQLiteOrmModelStoreError(
                f"{self.table}: unknown table column {column!r}"
            )


@dataclass(frozen=True, slots=True)
class SQLiteOrmSchema:
    schema_path: Path
    tables: tuple[SQLiteOrmSchemaTable, ...]

    def ensure_installed(self, connection: sqlite3.Connection) -> None:
        schema_paths_by_table = {
            schema_path.stem: schema_path for schema_path in self.schema_paths()
        }
        for table in self.tables:
            schema_path = schema_paths_by_table.get(table.table)
            if schema_path is None:
                raise SQLiteOrmSchemaDriftError(
                    f"{table.table}: generated SQLite schema file is missing"
                )
            actual_columns = table.table_columns(connection)
            if actual_columns is not None and actual_columns == table.columns:
                continue
            if actual_columns is not None:
                _recreate_table(
                    connection,
                    table=table,
                    schema_path=schema_path,
                    actual_columns=actual_columns,
                )
                continue
            _ = connection.executescript(schema_path.read_text(encoding="utf-8"))
        connection.commit()

    def schema_paths(self) -> tuple[Path, ...]:
        schema_dir = (
            self.schema_path.parent if self.schema_path.is_file() else self.schema_path
        )
        return tuple(sorted(schema_dir.glob("*.sql")))


@dataclass(frozen=True, slots=True)
class SQLiteOrmSchemaContract:
    """Materialized SQLite schema contract consumed by SDK/service state stores."""

    schema_contract: str
    schema_version: int
    schema: SQLiteOrmSchema
    expected_storage_indexes: Mapping[str, tuple[SQLiteOrmStorageIndex, ...]] = field(
        default_factory=dict
    )

    def ensure_installed(self, connection: sqlite3.Connection) -> None:
        self.schema.ensure_installed(connection)
        self._ensure_storage_indexes(connection)

    def inspect_health(self, connection: sqlite3.Connection) -> SQLiteOrmSchemaHealth:
        return inspect_sqlite_orm_schema_health(connection=connection, contract=self)

    def _ensure_storage_indexes(self, connection: sqlite3.Connection) -> None:
        schema_paths_by_table = {
            schema_path.stem: schema_path for schema_path in self.schema.schema_paths()
        }
        for table in self.schema.tables:
            expected_indexes = self.expected_storage_indexes.get(table.table, ())
            if not expected_indexes:
                continue
            health = _sqlite_orm_table_health(
                connection=connection,
                table=table,
                expected_indexes=expected_indexes,
            )
            if (
                health.actual_columns is None
                or health.missing_columns
                or health.extra_columns
                or not health.missing_indexes
            ):
                continue
            schema_path = schema_paths_by_table.get(table.table)
            if schema_path is None:
                raise SQLiteOrmSchemaDriftError(
                    f"{table.table}: generated SQLite schema file is missing"
                )
            _recreate_table(
                connection,
                table=table,
                schema_path=schema_path,
                actual_columns=health.actual_columns,
            )
        connection.commit()


def open_sqlite_orm_connection(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def open_sqlite_orm_readonly_connection(database_path: Path) -> sqlite3.Connection:
    quoted_path = quote(str(database_path.expanduser().resolve()), safe="/:")
    connection = sqlite3.connect(f"file:{quoted_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def open_sqlite_orm_memory_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    return connection


def sqlite_value_for_model(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Enum):
        return cast(object, value.value)
    if isinstance(value, Mapping):
        return json_text(dict(value))
    if isinstance(value, list):
        return json_text(value)
    if isinstance(value, tuple):
        return json_text(list(cast(tuple[object, ...], value)))
    if isinstance(value, set):
        return json_text(cast(set[object], value))
    return value


def json_text(value: object) -> str:
    return json.dumps(value, default=str, separators=(",", ":"), sort_keys=True)


def json_payload(value: object) -> object:
    if isinstance(value, str):
        try:
            return cast(object, json.loads(value))
        except json.JSONDecodeError:
            return None
    return value


def sqlite_table_columns(
    connection: sqlite3.Connection,
    table: str,
) -> tuple[str, ...] | None:
    _validate_sql_identifier(table, "table")
    rows = cast(
        list[sqlite3.Row], connection.execute(f"PRAGMA table_info({table})").fetchall()
    )
    if not rows:
        return None
    return tuple(str(cast(object, row["name"])) for row in rows)


def sqlite_table_indexes(
    connection: sqlite3.Connection,
    table: str,
) -> tuple[SQLiteOrmIndex, ...]:
    _validate_sql_identifier(table, "table")
    rows = cast(
        list[sqlite3.Row], connection.execute(f"PRAGMA index_list({table})").fetchall()
    )
    indexes: list[SQLiteOrmIndex] = []
    for row in rows:
        index_name = str(cast(object, row["name"]))
        _validate_sql_identifier(index_name, "index")
        columns = tuple(
            str(cast(object, info_row["name"]))
            for info_row in cast(
                list[sqlite3.Row],
                connection.execute(f"PRAGMA index_info({index_name})").fetchall(),
            )
        )
        indexes.append(
            SQLiteOrmIndex(
                name=index_name,
                unique=bool(cast(object, row["unique"])),
                columns=columns,
            )
        )
    return tuple(sorted(indexes, key=lambda index: index.name))


def inspect_sqlite_orm_schema_health(
    *,
    connection: sqlite3.Connection,
    contract: SQLiteOrmSchemaContract,
) -> SQLiteOrmSchemaHealth:
    tables = tuple(
        _sqlite_orm_table_health(
            connection=connection,
            table=table,
            expected_indexes=contract.expected_storage_indexes.get(table.table, ()),
        )
        for table in contract.schema.tables
    )
    issues: list[str] = []
    for table in tables:
        if table.status == "ok":
            continue
        issues.append(f"{table.table_name}:{table.status}")
        if table.missing_columns:
            issues.append(
                f"{table.table_name}:missing_columns:{','.join(table.missing_columns)}"
            )
        if table.extra_columns:
            issues.append(
                f"{table.table_name}:extra_columns:{','.join(table.extra_columns)}"
            )
        if table.missing_indexes:
            issues.append(f"{table.table_name}:missing_storage_indexes")

    healthy_table_count = sum(1 for table in tables if table.status == "ok")
    return SQLiteOrmSchemaHealth(
        schema_contract=contract.schema_contract,
        schema_version=contract.schema_version,
        status="ok" if not issues else "schema_drift",
        table_count=len(tables),
        healthy_table_count=healthy_table_count,
        storage_index_coverage=not any(table.missing_indexes for table in tables),
        tables=tables,
        issues=tuple(issues),
    )


def load_sqlite_orm_schema_contract_descriptor(
    path: Path,
) -> SQLiteOrmSchemaContractDescriptor:
    return SQLiteOrmSchemaContractDescriptor.from_json_path(path)


def _sqlite_orm_table_health(
    *,
    connection: sqlite3.Connection,
    table: SQLiteOrmSchemaTable,
    expected_indexes: tuple[SQLiteOrmStorageIndex, ...],
) -> SQLiteOrmTableHealth:
    expected_columns = table.columns
    actual_columns = sqlite_table_columns(connection, table.table)
    missing_columns: tuple[str, ...]
    extra_columns: tuple[str, ...]
    if actual_columns is None:
        missing_columns = expected_columns
        extra_columns = ()
        actual_indexes: tuple[SQLiteOrmStorageIndex, ...] = ()
    else:
        actual_column_set = set(actual_columns)
        expected_column_set = set(expected_columns)
        missing_columns = tuple(
            column for column in expected_columns if column not in actual_column_set
        )
        extra_columns = tuple(
            column for column in actual_columns if column not in expected_column_set
        )
        actual_indexes = tuple(
            (index.unique, index.columns)
            for index in sqlite_table_indexes(connection, table.table)
        )
    actual_index_set = set(actual_indexes)
    missing_indexes = tuple(
        index for index in expected_indexes if index not in actual_index_set
    )
    if actual_columns is None:
        table_status: SQLiteOrmTableHealthStatus = "missing"
    elif missing_columns or extra_columns or missing_indexes:
        table_status = "schema_drift"
    else:
        table_status = "ok"
    return SQLiteOrmTableHealth(
        table_name=table.table,
        status=table_status,
        expected_columns=expected_columns,
        actual_columns=actual_columns,
        missing_columns=missing_columns,
        extra_columns=extra_columns,
        expected_indexes=expected_indexes,
        actual_indexes=actual_indexes,
        missing_indexes=missing_indexes,
    )


def _recreate_table(
    connection: sqlite3.Connection,
    *,
    table: SQLiteOrmSchemaTable,
    schema_path: Path,
    actual_columns: tuple[str, ...],
) -> None:
    old_table = f"__aware_old_{table.table}"
    _ = connection.execute(f"DROP TABLE IF EXISTS {old_table}")
    _drop_explicit_indexes(connection, table=table.table)
    _ = connection.execute(f"ALTER TABLE {table.table} RENAME TO {old_table}")
    _ = connection.executescript(schema_path.read_text(encoding="utf-8"))
    common_columns = tuple(
        column for column in table.columns if column in actual_columns
    )
    if common_columns:
        joined_columns = ", ".join(common_columns)
        try:
            _ = connection.execute(
                f"""
                INSERT OR IGNORE INTO {table.table} ({joined_columns})
                SELECT {joined_columns}
                FROM {old_table}
                """
            )
        except sqlite3.Error as exc:
            raise SQLiteOrmSchemaDriftError(
                f"{table.table}: failed to migrate common columns during schema repair"
            ) from exc
    _ = connection.execute(f"DROP TABLE {old_table}")


def _drop_explicit_indexes(connection: sqlite3.Connection, *, table: str) -> None:
    _validate_sql_identifier(table, "table")
    rows = cast(
        list[sqlite3.Row], connection.execute(f"PRAGMA index_list({table})").fetchall()
    )
    for row in rows:
        index_name = str(cast(object, row["name"]))
        if index_name.startswith("sqlite_autoindex_"):
            continue
        _validate_sql_identifier(index_name, "index")
        _ = connection.execute(f"DROP INDEX IF EXISTS {index_name}")


def _validate_sql_identifier(value: str, label: str) -> None:
    if not value or not all(part.isidentifier() for part in value.split(".")):
        raise SQLiteOrmModelStoreError(f"invalid SQLite {label} identifier: {value!r}")


def _duplicates(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicated: list[str] = []
    for value in values:
        if value in seen and value not in duplicated:
            duplicated.append(value)
        seen.add(value)
    return tuple(duplicated)


def _schema_table_descriptor_from_payload(
    payload: object,
) -> SQLiteOrmSchemaTableDescriptor:
    if not isinstance(payload, Mapping):
        raise SQLiteOrmModelStoreError("schema contract table entry must be an object")
    table_payload = cast(Mapping[str, object], payload)
    return SQLiteOrmSchemaTableDescriptor(
        table=_required_text(table_payload, "table"),
        columns=_required_string_tuple(table_payload, "columns"),
        json_columns=frozenset(_optional_string_tuple(table_payload, "json_columns")),
        storage_indexes=tuple(
            _storage_index_from_payload(index_payload)
            for index_payload in _optional_object_tuple(
                table_payload,
                "storage_indexes",
            )
        ),
    )


def _storage_index_from_payload(payload: object) -> SQLiteOrmStorageIndex:
    if not isinstance(payload, Mapping):
        raise SQLiteOrmModelStoreError(
            "schema contract storage index must be an object"
        )
    index_payload = cast(Mapping[str, object], payload)
    raw_unique = index_payload.get("unique")
    if not isinstance(raw_unique, bool):
        raise SQLiteOrmModelStoreError(
            "schema contract storage index requires bool unique"
        )
    return raw_unique, _required_string_tuple(index_payload, "columns")


def _required_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise SQLiteOrmModelStoreError(f"schema contract requires text field {key!r}")


def _optional_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _required_positive_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SQLiteOrmModelStoreError(
            f"schema contract requires positive int field {key!r}"
        )
    return value


def _required_string_tuple(payload: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, (list, tuple)):
        raise SQLiteOrmModelStoreError(
            f"schema contract requires string list field {key!r}"
        )
    result = tuple(str(item).strip() for item in value if str(item).strip())
    if len(result) != len(value):
        raise SQLiteOrmModelStoreError(
            f"schema contract field {key!r} contains blank values"
        )
    return result


def _optional_string_tuple(payload: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise SQLiteOrmModelStoreError(
            f"schema contract field {key!r} must be a string list"
        )
    result = tuple(str(item).strip() for item in value if str(item).strip())
    if len(result) != len(value):
        raise SQLiteOrmModelStoreError(
            f"schema contract field {key!r} contains blank values"
        )
    return result


def _optional_object_tuple(
    payload: Mapping[str, object], key: str
) -> tuple[object, ...]:
    value = payload.get(key)
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise SQLiteOrmModelStoreError(f"schema contract field {key!r} must be a list")
    return tuple(value)


__all__ = [
    "SQLiteOrmIndex",
    "SQLiteOrmModelStoreError",
    "SQLiteOrmModelTable",
    "SQLiteOrmOrder",
    "SQLiteOrmPredicate",
    "SQLiteOrmSchema",
    "SQLiteOrmSchemaContract",
    "SQLiteOrmSchemaContractDescriptor",
    "SQLiteOrmSchemaDriftError",
    "SQLiteOrmSchemaHealth",
    "SQLiteOrmSchemaTable",
    "SQLiteOrmSchemaTableDescriptor",
    "SQLiteOrmStorageIndex",
    "SQLiteOrmTableHealth",
    "inspect_sqlite_orm_schema_health",
    "json_payload",
    "json_text",
    "open_sqlite_orm_connection",
    "open_sqlite_orm_memory_connection",
    "open_sqlite_orm_readonly_connection",
    "load_sqlite_orm_schema_contract_descriptor",
    "sqlite_table_columns",
    "sqlite_table_indexes",
    "sqlite_value_for_model",
]
