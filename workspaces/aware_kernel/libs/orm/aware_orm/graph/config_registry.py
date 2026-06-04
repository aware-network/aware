"""Registry providing read-only access to ClassConfig table metadata for GraphSQL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import UUID


@dataclass(frozen=True)
class TableDescriptor:
    """Minimal table metadata consumed by the Graph plan pipeline."""

    class_config_id: UUID
    table_schema: str
    table_name: str
    attributes: tuple[str, ...] = ()

    @property
    def table_key(self) -> str:
        return f"{self.table_schema}.{self.table_name}"


class GraphConfigRegistry:
    """In-memory registry of table descriptors keyed by schema.table."""

    def __init__(self, descriptors: Iterable[TableDescriptor] | None = None) -> None:
        self._by_key: dict[str, TableDescriptor] = {}
        self._by_class_config_id: dict[UUID, TableDescriptor] = {}
        if descriptors:
            for descriptor in descriptors:
                self.register(descriptor)

    def register(self, descriptor: TableDescriptor) -> None:
        key = descriptor.table_key
        self._by_key[key] = descriptor
        self._by_class_config_id[descriptor.class_config_id] = descriptor

    def get(self, table_key: str) -> TableDescriptor | None:
        return self._by_key.get(table_key)

    def get_by_class_config_id(self, class_config_id: UUID) -> TableDescriptor | None:
        return self._by_class_config_id.get(class_config_id)

    def require(self, table_key: str) -> TableDescriptor:
        descriptor = self.get(table_key)
        if descriptor is None:
            raise KeyError(f"Table descriptor missing for {table_key}")
        return descriptor

    def all(self) -> Iterable[TableDescriptor]:
        return self._by_key.values()
