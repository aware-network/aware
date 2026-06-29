"""Meta-owned value resolver helpers for graph attribute materialization."""

from __future__ import annotations

import json
from enum import Enum as PyEnum
from typing import Any
from uuid import UUID

from aware_meta.attribute.instance.value.builder import (
    ClassInstanceResolver,
    EnumOptionResolver,
)
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.enum.enum_option import EnumOption
from aware_orm.models.orm_model import ORMModel


def _unwrap_json_envelope(value: Any) -> Any:
    if isinstance(value, dict) and set(value.keys()) == {"value"}:
        return value["value"]
    return value


def default_meta_enum_option_resolver(
    type_descriptor: AttributeTypeDescriptor,
    value: Any,
) -> UUID:
    """Resolve enum option identifiers from JSON-friendly values."""

    resolved_value = _unwrap_json_envelope(value)

    if isinstance(resolved_value, UUID):
        return resolved_value
    if isinstance(resolved_value, EnumOption):
        return resolved_value.id
    if isinstance(resolved_value, PyEnum):
        resolved_value = resolved_value.value

    enum_config = type_descriptor.enum_config
    if enum_config is None:
        raise ValueError("AttributeTypeDescriptor missing enum_config")

    if isinstance(resolved_value, str):
        normalized = resolved_value.casefold()
        try:
            return UUID(resolved_value)
        except ValueError:
            pass
        for option in enum_config.enum_options:
            if option.value == resolved_value or option.label == resolved_value:
                return option.id
            if isinstance(option.value, str) and option.value.casefold() == normalized:
                return option.id
            if isinstance(option.label, str) and option.label.casefold() == normalized:
                return option.id

    if isinstance(resolved_value, int):
        for option in enum_config.enum_options:
            if option.position == resolved_value:
                return option.id

    raise ValueError(f"Unable to resolve EnumOption id for value={resolved_value!r}")


def default_meta_class_instance_resolver(
    type_descriptor: AttributeTypeDescriptor,
    value: Any,
) -> UUID:
    """Resolve class instance identifiers from JSON-friendly values."""

    _ = type_descriptor
    resolved_value = _unwrap_json_envelope(value)

    if isinstance(resolved_value, UUID):
        return resolved_value
    if isinstance(resolved_value, ClassInstance | ORMModel):
        return resolved_value.id
    if isinstance(resolved_value, str):
        try:
            return UUID(resolved_value)
        except ValueError as exc:
            raise ValueError(
                f"Unable to parse ClassInstance id from string: {resolved_value!r}"
            ) from exc
    if isinstance(resolved_value, dict):
        raw_id = resolved_value.get("id")
        if isinstance(raw_id, str):
            try:
                return UUID(raw_id)
            except ValueError as exc:
                raise ValueError(
                    f"Unable to parse ClassInstance id from dict: {resolved_value!r}"
                ) from exc

    raise ValueError(
        f"Unable to resolve ClassInstance id for value={resolved_value!r}"
    )


def parse_meta_default_value(default_value: str) -> object:
    """Parse canonical AttributeConfig.default_value JSON payloads."""

    try:
        return json.loads(default_value)
    except ValueError as exc:
        raise ValueError(f"Invalid default_value JSON: {default_value!r}") from exc


__all__ = [
    "ClassInstanceResolver",
    "EnumOptionResolver",
    "default_meta_class_instance_resolver",
    "default_meta_enum_option_resolver",
    "parse_meta_default_value",
]
