"""Bundle rail: install SQL runtime metadata.

This module is intentionally separate from:
- ORM graph binding (see `graph_binding.py`)
- bundle binding adapter (see `bundle_binding.py`)

Contract:
- reads SQL mapping payloads from `bundle.bindings` (JSON), under each binding entry:
  - `class_fqn: str`
  - `canonical_entity_id` or `canonical_class_config_id`: str (UUID)
  - `sql_mapping: list[dict]`
- computes and registers `SQLRuntimeMetadata` via `sql_metadata.register_sql_metadata`

This keeps SQL concerns out of binding SSOT while leaving room for future
SQL/GraphSQL artifacts to evolve independently.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable
from uuid import UUID

from .errors import BundleInstallError
from .sql_metadata import SQLRuntimeMetadata, register_sql_metadata


def _dict_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


@dataclass(slots=True)
class SQLMappingEntry:
    attribute_name: str | None
    persisted: bool
    table_schema: str | None
    table_name: str | None
    column_name: str | None = None
    fk_owner: str | None = None
    fk_columns: list[dict[str, Any]] = field(default_factory=list)
    join_chain: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class SQLMetadataInstallResult:
    installed: int
    missing_classes: list[str]


def install_sql_metadata_from_bindings_payload(
    bindings: bytes | None,
    *,
    strict: bool = False,
) -> SQLMetadataInstallResult:
    """Install SQL runtime metadata based on a bindings manifest payload."""

    if not bindings:
        if strict:
            raise BundleInstallError("Environment bundle missing bindings manifest (for SQL metadata install)")
        return SQLMetadataInstallResult(installed=0, missing_classes=[])

    try:
        payload = json.loads(bindings.decode("utf-8"))
    except Exception as exc:
        if strict:
            raise BundleInstallError(f"Bindings manifest is not valid JSON: {exc}") from exc
        return SQLMetadataInstallResult(installed=0, missing_classes=[])
    if not isinstance(payload, dict):
        if strict:
            raise BundleInstallError("Bindings manifest root must be an object")
        return SQLMetadataInstallResult(installed=0, missing_classes=[])

    installed = 0
    missing_classes: list[str] = []

    for entry in _dict_items(payload.get("bindings")):
        class_fqn = entry.get("class_fqn")
        if not class_fqn:
            continue
        class_fqn = str(class_fqn)
        canonical_entity_id = entry.get("canonical_entity_id") or entry.get(
            "canonical_class_config_id"
        )
        if not canonical_entity_id:
            if strict:
                missing_classes.append(class_fqn)
            continue
        try:
            class_config_id = UUID(str(canonical_entity_id))
        except Exception:
            if strict:
                missing_classes.append(class_fqn)
            continue

        sql_mapping = _dict_items(entry.get("sql_mapping"))
        if not sql_mapping:
            if strict:
                missing_classes.append(class_fqn)
            continue

        parsed: list[SQLMappingEntry] = []
        for item in sql_mapping:
            fk_payload = _dict_items(item.get("fk_columns"))
            join_payload = _dict_items(item.get("join_chain"))
            parsed.append(
                SQLMappingEntry(
                    attribute_name=(
                        str(item["attribute_name"]) if item.get("attribute_name") is not None else None
                    ),
                    table_schema=str(item["table_schema"]) if item.get("table_schema") is not None else None,
                    table_name=str(item["table_name"]) if item.get("table_name") is not None else None,
                    column_name=str(item["column_name"]) if item.get("column_name") is not None else None,
                    persisted=bool(item.get("persisted")),
                    fk_owner=str(item["fk_owner"]) if item.get("fk_owner") is not None else None,
                    fk_columns=fk_payload,
                    join_chain=join_payload,
                )
            )

        metadata = _build_sql_runtime_metadata(class_config_id, parsed)
        if metadata is None or not metadata.table_schema or not metadata.table_name:
            if strict:
                missing_classes.append(class_fqn)
            continue
        register_sql_metadata(metadata, class_fqn=class_fqn)
        installed += 1

    if strict and missing_classes:
        raise BundleInstallError(f"Missing SQL metadata for bound classes: {sorted(set(missing_classes))}")

    return SQLMetadataInstallResult(installed=installed, missing_classes=missing_classes)


def install_sql_metadata_from_bundle(bundle: Any, *, strict: bool = False) -> SQLMetadataInstallResult:
    """Compatibility wrapper for Structure EnvironmentBundle-like objects."""

    return install_sql_metadata_from_bindings_payload(
        getattr(bundle, "bindings", None),
        strict=strict,
    )


def _build_sql_runtime_metadata(class_config_id: UUID, entries: Iterable[SQLMappingEntry]) -> SQLRuntimeMetadata:
    entries = list(entries)
    if not entries:
        raise ValueError("No SQL mapping entries provided")

    table_schema = next((entry.table_schema for entry in entries), None)
    if not table_schema:
        raise ValueError("No table schema found in SQL mapping entries")
    table_name = next((entry.table_name for entry in entries), None)
    if not table_name:
        raise ValueError("No table name found in SQL mapping entries")
    column_by_attribute: dict[str, str] = {}
    persisted_attributes: set[str] = set()
    fk_owner_by_attribute: dict[str, str | None] = {}
    fk_columns_by_attribute: dict[str, tuple[dict[str, Any], ...]] = {}
    join_chain_by_attribute: dict[str, tuple[dict[str, Any], ...]] = {}

    for entry in entries:
        attr = entry.attribute_name
        if not attr:
            continue
        if entry.column_name:
            column_by_attribute[attr] = entry.column_name
        if entry.persisted or entry.fk_columns:
            persisted_attributes.add(attr)
        if entry.fk_owner:
            fk_owner_by_attribute[attr] = entry.fk_owner
        if entry.fk_columns:
            fk_columns_by_attribute[attr] = tuple(entry.fk_columns)
            if attr not in column_by_attribute:
                source_fk = next((fk for fk in entry.fk_columns if fk.get("owner") == "source"), None)
                if source_fk and source_fk.get("column_name"):
                    column_by_attribute[attr] = source_fk["column_name"]
        if entry.join_chain:
            join_chain_by_attribute[attr] = tuple(entry.join_chain)

    return SQLRuntimeMetadata(
        class_config_id=class_config_id,
        table_schema=table_schema,
        table_name=table_name,
        column_by_attribute=column_by_attribute,
        persisted_attributes=frozenset(persisted_attributes),
        fk_owner_by_attribute=fk_owner_by_attribute,
        fk_columns_by_attribute=fk_columns_by_attribute,
        join_chain_by_attribute=join_chain_by_attribute,
    )
