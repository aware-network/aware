from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum


def mapping_or_none(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    mapped = mapping_value(value)
    return mapped if mapped else None


def mapping_value(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def tuple_mappings(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(
        mapping_value(item) for item in value if isinstance(item, Mapping)
    )


def optional_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        value = value.value
    text = str(value).strip()
    return text or None


def string_value(value: object) -> str:
    text = optional_text(value)
    return text if text is not None else ""


def tuple_text(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(
            text
            for item in value
            for text in (optional_text(item),)
            if text is not None
        )
    text = optional_text(value)
    return (text,) if text is not None else ()


def int_value(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    text = optional_text(value)
    if text is None:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def int_mapping_value(value: object) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): int_value(item) for key, item in value.items()}


__all__ = [
    "int_mapping_value",
    "int_value",
    "mapping_or_none",
    "mapping_value",
    "optional_text",
    "string_value",
    "tuple_mappings",
    "tuple_text",
]
