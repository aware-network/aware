from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, FrozenSet
from uuid import UUID


@dataclass(frozen=True)
class SQLRuntimeMetadata:
    """Runtime SQL metadata derived from kernel-lite bindings."""

    class_config_id: UUID
    table_schema: str
    table_name: str
    column_by_attribute: Mapping[str, str]
    persisted_attributes: FrozenSet[str]
    fk_owner_by_attribute: Mapping[str, str | None]
    fk_columns_by_attribute: Mapping[str, tuple[dict, ...]]
    join_chain_by_attribute: Mapping[str, tuple[dict, ...]]

    @property
    def table_key(self) -> str:
        return f"{self.table_schema}.{self.table_name}".lower()


_metadata_by_table: dict[str, SQLRuntimeMetadata] = {}
_metadata_by_class: dict[str, SQLRuntimeMetadata] = {}


def register_sql_metadata(metadata: SQLRuntimeMetadata, *, class_fqn: str | None = None) -> None:
    """Register metadata so other components can derive descriptors."""
    key = metadata.table_key
    if key:
        _metadata_by_table[key] = metadata
    if class_fqn:
        _metadata_by_class[class_fqn] = metadata


def clear_sql_metadata_registry() -> None:
    _metadata_by_table.clear()
    _metadata_by_class.clear()


def get_sql_metadata_for_table(table_key: str) -> SQLRuntimeMetadata | None:
    return _metadata_by_table.get(table_key.lower())


def iter_sql_metadata() -> Iterable[tuple[str, SQLRuntimeMetadata]]:
    return _metadata_by_table.items()


def get_sql_metadata_for_class(class_fqn: str) -> SQLRuntimeMetadata | None:
    return _metadata_by_class.get(class_fqn)
