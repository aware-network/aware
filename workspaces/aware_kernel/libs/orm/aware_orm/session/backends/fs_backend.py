"""
Filesystem-backed persistence backend for ORM sessions.
"""

# @doc-ref: ../../../docs/session/runtime.md
# @test-ref: ../../../tests/session/test_backends.py

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from uuid import UUID

from aware_orm._support import find_aware_root, logger

from .protocol import PersistenceBackendProtocol, QueryResult, SessionBackendState


INSERT_PATTERN = re.compile(
    r"INSERT\s+INTO\s+(?P<schema>\w+)\.(?P<table>\w+)\s*\((?P<columns>[^)]+)\)\s*VALUES\s*\((?P<values>[^)]+)\)",
    re.IGNORECASE,
)
UPDATE_PATTERN = re.compile(
    r"UPDATE\s+(?P<schema>\w+)\.(?P<table>\w+)\s+SET\s+(?P<set>.+?)\s+WHERE\s+(?P<where>.+)",
    re.IGNORECASE | re.DOTALL,
)
DELETE_PATTERN = re.compile(
    r"DELETE\s+FROM\s+(?P<schema>\w+)\.(?P<table>\w+)\s+WHERE\s+(?P<where>.+)",
    re.IGNORECASE,
)
SELECT_PATTERN = re.compile(
    r"SELECT\s+\*\s+FROM\s+(?P<schema>\w+)\.(?P<table>\w+)(?P<rest>.*)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class FsOperation:
    op_type: str  # "insert" | "update" | "delete"
    schema: str
    table: str
    row_id: str | None
    data: Dict[str, Any] | None = None


class FsPersistenceBackend(PersistenceBackendProtocol):
    """Filesystem persistence backend for sessions."""

    def __init__(self, session: SessionBackendState):
        self._session = session
        self._operations: List[FsOperation] = []
        self._aware_root = find_aware_root()
        self._base_path = self._aware_root / ".aware" / "runtime" / "orm"
        self._base_path.mkdir(parents=True, exist_ok=True)

    # ---------- Queue management ----------

    def enqueue_insert(self, sql: str, params: Tuple[Any, ...]) -> None:
        parsed = self._parse_insert(sql, params)
        if parsed is None:
            raise ValueError(f"Unsupported INSERT statement for filesystem backend: {sql}")
        schema, table, data = parsed

        self._session._pending_inserts.append((sql, params))
        self._operations.append(FsOperation("insert", schema, table, data.get("id"), data))
        logger.debug("Queued FS INSERT for %s.%s (%s)", schema, table, data.get("id"))

    def enqueue_update(self, sql: str, params: Tuple[Any, ...]) -> None:
        parsed = self._parse_update(sql, params)
        if parsed is None:
            raise ValueError(f"Unsupported UPDATE statement for filesystem backend: {sql}")
        schema, table, row_id, data = parsed

        self._session._pending_updates.append((sql, params))
        self._operations.append(FsOperation("update", schema, table, row_id, data))
        logger.debug("Queued FS UPDATE for %s.%s (%s)", schema, table, row_id)

    def enqueue_delete(self, sql: str, params: Tuple[Any, ...]) -> None:
        parsed = self._parse_delete(sql, params)
        if parsed is None:
            raise ValueError(f"Unsupported DELETE statement for filesystem backend: {sql}")
        schema, table, row_id = parsed

        self._session._pending_deletes.append((sql, params))
        self._operations.append(FsOperation("delete", schema, table, row_id))
        logger.debug("Queued FS DELETE for %s.%s (%s)", schema, table, row_id)

    def has_pending_operations(self) -> bool:
        return bool(self._operations)

    def get_pending_counts(self) -> dict[str, int]:
        inserts = sum(1 for op in self._operations if op.op_type == "insert")
        updates = sum(1 for op in self._operations if op.op_type == "update")
        deletes = sum(1 for op in self._operations if op.op_type == "delete")
        return {"inserts": inserts, "updates": updates, "deletes": deletes}

    def clear_pending(self) -> None:
        self._operations.clear()
        self._session._pending_inserts.clear()
        self._session._pending_updates.clear()
        self._session._pending_deletes.clear()

    # ---------- Read operations ----------

    async def execute_read(self, sql: str, params: Tuple[Any, ...]) -> QueryResult:
        parsed = self._parse_select(sql)
        if parsed is None:
            raise ValueError(f"Unsupported SELECT statement for filesystem backend: {sql}")

        schema, table, clauses = parsed
        branch_path = self._branch_path(schema, table)

        if not branch_path.exists():
            return []

        filters = clauses["filters"]
        limit_placeholder = clauses.get("limit_placeholder")
        offset_placeholder = clauses.get("offset_placeholder")

        limit = None
        if limit_placeholder is not None:
            limit = int(self._resolve_param(params, limit_placeholder))
        offset = 0
        if offset_placeholder is not None:
            offset = int(self._resolve_param(params, offset_placeholder))

        # Short-circuit when filtering by primary key
        id_filter = next((f for f in filters if f["column"] == "id" and f["op"] == "eq"), None)
        if id_filter:
            row_id = self._resolve_param(params, id_filter["placeholder"])
            record = self._load_record(branch_path, row_id)
            if record is None:
                return []
            if self._record_matches(record, filters, params):
                return [record]
            return []

        # Otherwise scan branch directory
        results: List[Dict[str, Any]] = []
        for file_path in sorted(branch_path.glob("*.json")):
            record = self._load_record_from_path(file_path)
            if record is None:
                continue
            if self._record_matches(record, filters, params):
                results.append(record)

        # Apply offset/limit
        if offset:
            results = results[offset:]
        if limit is not None:
            results = results[:limit]

        return results

    # ---------- Transaction handling ----------

    async def commit(self) -> None:
        if not self._operations:
            logger.debug("FS backend: no pending operations to commit")
            return

        operations = list(self._operations)
        for op in operations:
            if op.op_type == "insert":
                self._apply_insert(op)
            elif op.op_type == "update":
                self._apply_update(op)
            elif op.op_type == "delete":
                self._apply_delete(op)
            else:
                raise ValueError(f"Unknown FS operation type: {op.op_type}")

        self.clear_pending()
        logger.debug("FS backend commit completed (%d operations)", len(operations))

    async def rollback(self) -> None:
        self.clear_pending()
        logger.debug("FS backend rollback completed")

    # ---------- Internal helpers ----------

    def _branch_path(self, schema: str, table: str) -> Path:
        branch_id = str(self._session.branch_id)
        path = self._base_path / schema / table / branch_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _object_path(self, schema: str, table: str, object_id: str) -> Path:
        return self._branch_path(schema, table) / f"{object_id}.json"

    def _apply_insert(self, op: FsOperation) -> None:
        if op.data is None or op.row_id is None:
            raise ValueError("Insert operation missing data or row_id")

        path = self._object_path(op.schema, op.table, op.row_id)
        payload = self._normalize_record(op.data)
        self._write_json(path, payload)

    def _apply_update(self, op: FsOperation) -> None:
        if op.data is None or op.row_id is None:
            raise ValueError("Update operation missing data or row_id")

        path = self._object_path(op.schema, op.table, op.row_id)
        current = self._load_record_from_path(path) or {}
        current.update(self._normalize_record(op.data))
        self._write_json(path, current)

    def _apply_delete(self, op: FsOperation) -> None:
        if op.row_id is None:
            raise ValueError("Delete operation missing row_id")
        path = self._object_path(op.schema, op.table, op.row_id)
        if path.exists():
            path.unlink()

    @staticmethod
    def _write_json(path: Path, payload: Dict[str, Any]) -> None:
        tmp_path = path.with_suffix(".json.tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(
                payload,
                fh,
                ensure_ascii=False,
                default=FsPersistenceBackend._json_default,
            )
        tmp_path.replace(path)

    @staticmethod
    def _json_default(value: Any) -> Any:
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.isoformat()
        if hasattr(value, "value"):
            try:
                return value.value
            except Exception:
                pass
        return str(value)

    def _load_record(self, branch_path: Path, row_id: str) -> Dict[str, Any] | None:
        path = branch_path / f"{row_id}.json"
        return self._load_record_from_path(path)

    @staticmethod
    def _load_record_from_path(path: Path) -> Dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:
            logger.error("Failed to load FS record %s: %s", path, exc)
            return None

    @staticmethod
    def _normalize_record(data: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                normalized[key] = str(value)
            elif isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=timezone.utc)
                normalized[key] = value.isoformat()
            elif hasattr(value, "value"):
                try:
                    normalized[key] = value.value  # Enum
                except Exception:
                    normalized[key] = str(value)
            else:
                normalized[key] = value
        return normalized

    @staticmethod
    def _resolve_param(params: Tuple[Any, ...], placeholder: int) -> Any:
        index = placeholder - 1
        if index < 0 or index >= len(params):
            raise IndexError(f"Parameter index out of range for placeholder ${placeholder}")
        return params[index]

    def _record_matches(
        self,
        record: Dict[str, Any],
        filters: List[Dict[str, Any]],
        params: Tuple[Any, ...],
    ) -> bool:
        for filt in filters:
            column = filt["column"]
            op = filt["op"]
            if op == "eq":
                value = self._resolve_param(params, filt["placeholder"])
                if str(record.get(column)) != str(value):
                    return False
            elif op == "is_null":
                expected_null = filt.get("is_null", True)
                is_null = record.get(column) is None
                if is_null != expected_null:
                    return False
            elif op == "in":
                placeholders: List[int] = filt["placeholders"]
                values = {str(self._resolve_param(params, idx)) for idx in placeholders}
                if str(record.get(column)) not in values:
                    return False
            else:
                raise NotImplementedError(f"FS backend does not support operator {op}")
        return True

    # ---------- SQL parsing helpers ----------

    @staticmethod
    def _normalize_identifier_quotes(sql: str) -> str:
        """Normalize quoted SQL identifiers (`\"name\"`) to bare names (`name`)."""
        return re.sub(r'"([A-Za-z_][A-Za-z0-9_]*)"', r"\1", sql)

    @staticmethod
    def _canonical_identifier(value: str) -> str:
        return value.strip().lower()

    @staticmethod
    def _parse_insert(sql: str, params: Tuple[Any, ...]) -> Tuple[str, str, Dict[str, Any]] | None:
        normalized_sql = FsPersistenceBackend._normalize_identifier_quotes(sql).strip()
        match = INSERT_PATTERN.match(normalized_sql)
        if not match:
            return None
        schema = FsPersistenceBackend._canonical_identifier(match.group("schema"))
        table = FsPersistenceBackend._canonical_identifier(match.group("table"))
        columns = [col.strip() for col in match.group("columns").split(",")]
        if len(columns) != len(params):
            raise ValueError("Column/value count mismatch for FS insert")
        data = {col: params[idx] for idx, col in enumerate(columns)}
        if "id" not in data:
            raise ValueError("Filesystem backend requires 'id' column in inserts")
        return schema, table, data

    @staticmethod
    def _parse_update(sql: str, params: Tuple[Any, ...]) -> Tuple[str, str, str, Dict[str, Any]] | None:
        normalized_sql = FsPersistenceBackend._normalize_identifier_quotes(sql).strip()
        match = UPDATE_PATTERN.match(normalized_sql)
        if not match:
            return None
        schema = FsPersistenceBackend._canonical_identifier(match.group("schema"))
        table = FsPersistenceBackend._canonical_identifier(match.group("table"))
        set_clause = match.group("set").strip()
        where_clause = match.group("where").strip()

        assignments = [segment.strip() for segment in set_clause.split(",")]
        data: Dict[str, Any] = {}
        placeholder_idx = 0
        for assignment in assignments:
            col_match = re.match(r"(\w+)\s*=\s*\$(\d+)", assignment)
            if not col_match:
                raise ValueError(f"Unsupported assignment in FS update: {assignment}")
            column = col_match.group(1)
            placeholder = int(col_match.group(2)) - 1
            if placeholder < 0 or placeholder >= len(params):
                raise IndexError("Update placeholder index out of range")
            data[column] = params[placeholder]
            placeholder_idx = max(placeholder_idx, placeholder)

        where_match = re.match(r"id\s*=\s*\$(\d+)", where_clause, re.IGNORECASE)
        if not where_match:
            raise ValueError("Filesystem backend only supports WHERE id = $N for updates")
        pk_placeholder = int(where_match.group(1)) - 1
        if pk_placeholder < 0 or pk_placeholder >= len(params):
            raise IndexError("Update primary key placeholder out of range")
        row_id = params[pk_placeholder]
        return schema, table, str(row_id), data

    @staticmethod
    def _parse_delete(sql: str, params: Tuple[Any, ...]) -> Tuple[str, str, str] | None:
        normalized_sql = FsPersistenceBackend._normalize_identifier_quotes(sql).strip()
        match = DELETE_PATTERN.match(normalized_sql)
        if not match:
            return None
        schema = FsPersistenceBackend._canonical_identifier(match.group("schema"))
        table = FsPersistenceBackend._canonical_identifier(match.group("table"))
        where_clause = match.group("where").strip()
        id_placeholder = FsPersistenceBackend._extract_id_placeholder(where_clause)
        if id_placeholder is None:
            raise ValueError("Filesystem backend delete requires an `id = $N` predicate")
        placeholder = id_placeholder - 1
        if placeholder < 0 or placeholder >= len(params):
            raise IndexError("Delete primary key placeholder out of range")
        row_id = params[placeholder]
        return schema, table, str(row_id)

    @staticmethod
    def _parse_select(sql: str) -> Tuple[str, str, Dict[str, Any]] | None:
        normalized_sql = FsPersistenceBackend._normalize_identifier_quotes(sql).strip()
        match = SELECT_PATTERN.match(normalized_sql)
        if not match:
            return None
        schema = FsPersistenceBackend._canonical_identifier(match.group("schema"))
        table = FsPersistenceBackend._canonical_identifier(match.group("table"))
        rest = match.group("rest") or ""

        filters: List[Dict[str, Any]] = []
        limit_placeholder: int | None = None
        offset_placeholder: int | None = None

        where_match = re.search(
            r"\bWHERE\b(?P<where>.+?)(\bORDER\b|\bLIMIT\b|\bOFFSET\b|$)",
            rest,
            re.IGNORECASE | re.DOTALL,
        )
        if where_match:
            where_clause = where_match.group("where")
            filters = FsPersistenceBackend._parse_where_clause(where_clause)

        limit_match = re.search(r"\bLIMIT\s+\$(\d+)", rest, re.IGNORECASE)
        if limit_match:
            limit_placeholder = int(limit_match.group(1))

        offset_match = re.search(r"\bOFFSET\s+\$(\d+)", rest, re.IGNORECASE)
        if offset_match:
            offset_placeholder = int(offset_match.group(1))

        clauses: Dict[str, Any] = {"filters": filters}
        if limit_placeholder:
            clauses["limit_placeholder"] = limit_placeholder
        if offset_placeholder:
            clauses["offset_placeholder"] = offset_placeholder

        return schema, table, clauses

    @staticmethod
    def _parse_where_clause(where_clause: str) -> List[Dict[str, Any]]:
        conditions = [segment.strip() for segment in re.split(r"\bAND\b", where_clause, flags=re.IGNORECASE)]
        results: List[Dict[str, Any]] = []
        for cond in conditions:
            cond = cond.strip().strip("()").strip()
            eq_match = re.match(
                r"(\w+)\s*=\s*\$(\d+)(?:::[A-Za-z_][A-Za-z0-9_\[\]]*)?",
                cond,
                re.IGNORECASE,
            )
            if eq_match:
                results.append(
                    {
                        "column": eq_match.group(1),
                        "op": "eq",
                        "placeholder": int(eq_match.group(2)),
                    }
                )
                continue

            in_match = re.match(r"(\w+)\s+IN\s+\(([^)]+)\)", cond, re.IGNORECASE)
            if in_match:
                placeholders = [
                    int(num.strip()[1:].split("::", 1)[0])
                    for num in in_match.group(2).split(",")
                    if num.strip().startswith("$")
                ]
                results.append(
                    {
                        "column": in_match.group(1),
                        "op": "in",
                        "placeholders": placeholders,
                    }
                )
                continue

            is_null_match = re.match(r"(\w+)\s+IS\s+(NOT\s+)?NULL", cond, re.IGNORECASE)
            if is_null_match:
                results.append(
                    {
                        "column": is_null_match.group(1),
                        "op": "is_null",
                        "is_null": not bool(is_null_match.group(2)),
                    }
                )
                continue

            raise NotImplementedError(f"Filesystem backend cannot parse WHERE condition: {cond}")

        return results

    @staticmethod
    def _extract_id_placeholder(where_clause: str) -> int | None:
        filters = FsPersistenceBackend._parse_where_clause(where_clause)
        id_filters = [filt for filt in filters if filt.get("op") == "eq" and str(filt.get("column")) == "id"]
        if not id_filters:
            return None
        return int(id_filters[0]["placeholder"])
