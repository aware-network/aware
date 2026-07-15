from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Mapping, Protocol, runtime_checkable
from uuid import UUID


if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig


@runtime_checkable
class ModelIntrospection(Protocol):
    """
    Canonical introspection contract for building OIGs from runtime instances.

    Goals:
    - Avoid duck-typed getattr() in meta builders (prevents accidental lazy loads via __getattr__).
    - Distinguish missing/unset vs explicit None (via `(found, value)` tuples).
    - Keep the interface implementable by BaseORMModel and external adapters.
    """

    id: UUID

    def field_is_declared(self, name: str) -> bool: ...
    def field_is_set(self, name: str) -> bool: ...

    def try_field_value(self, name: str, *, include_unset: bool = False) -> tuple[bool, object]: ...

    def try_virtual_value(self, attribute_config: "AttributeConfig") -> tuple[bool, object]: ...
    def try_attribute_value(self, attribute_config: "AttributeConfig") -> tuple[bool, object]: ...

    def try_class_config_id(self) -> UUID | None: ...


@dataclass(frozen=True)
class MappingModelSource(ModelIntrospection):
    """
    Adapter for building OIGs from a mapping payload.

    This is explicitly not "canonical ORM", but it implements the same introspection contract
    so meta builders can remain fully typed and consistent.
    """

    id: UUID
    values: Mapping[str, object]
    virtual_values: Mapping[str, object] = field(default_factory=dict)
    class_config_id: UUID | None = None

    def field_is_declared(self, name: str) -> bool:
        return name in self.values or name in self.virtual_values

    def field_is_set(self, name: str) -> bool:
        return self.field_is_declared(name)

    def try_field_value(self, name: str, *, include_unset: bool = False) -> tuple[bool, object]:
        if name in self.values:
            return True, self.values[name]
        return False, None

    def try_virtual_value(self, attribute_config: "AttributeConfig") -> tuple[bool, object]:
        if not attribute_config.is_virtual:
            return False, None
        if attribute_config.name in self.virtual_values:
            return True, self.virtual_values[attribute_config.name]
        return False, None

    def try_attribute_value(self, attribute_config: "AttributeConfig") -> tuple[bool, object]:
        if attribute_config.is_virtual:
            return self.try_virtual_value(attribute_config)
        return self.try_field_value(attribute_config.name, include_unset=False)

    def try_class_config_id(self) -> UUID | None:
        return self.class_config_id


__all__ = [
    "MappingModelSource",
    "ModelIntrospection",
]
