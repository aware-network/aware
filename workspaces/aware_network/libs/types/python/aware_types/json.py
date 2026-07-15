from __future__ import annotations

from datetime import date, datetime
from enum import Enum as PyEnum
from pathlib import Path
from typing import TypeAlias, cast
from uuid import UUID

from pydantic import BaseModel
from pydantic_core import core_schema as _cs


JsonValue: TypeAlias = (
    None
    | bool
    | int
    | float
    | str
    # NOTE: intentionally non-recursive for Pydantic/runtime compatibility.
    | list[object]
    | dict[str, object]
)


def _normalize_json_value(value: object) -> JsonValue:
    if value is None:
        return None
    if isinstance(value, PyEnum):
        return _normalize_json_value(cast(object, value.value))
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, BaseModel):
        return _normalize_json_value(value.model_dump(mode="json"))
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, tuple):
        tuple_items = cast(tuple[object, ...], value)
        normalized_items: list[object] = [_normalize_json_value(item) for item in tuple_items]
        return normalized_items
    if isinstance(value, list):
        list_items = cast(list[object], value)
        normalized_list_items: list[object] = [_normalize_json_value(item) for item in list_items]
        return normalized_list_items
    if isinstance(value, dict):
        normalized: dict[str, object] = {}
        for key, item in cast(dict[object, object], value).items():
            if not isinstance(key, str):
                raise TypeError("Json object keys must be strings")
            normalized[key] = _normalize_json_value(item)
        return normalized
    raise TypeError("JsonValue must be a JSON-compatible value")


class JsonObject(dict[str, JsonValue]):
    """JSON object helper type for Python models."""

    @classmethod
    def __get_pydantic_core_schema__(  # type: ignore[name-defined]
        cls,
        source_type: object,
        handler: object,
    ) -> _cs.CoreSchema:
        dict_any_schema = _cs.dict_schema(_cs.str_schema(), _cs.any_schema())

        def _coerce(value: object) -> "JsonObject":
            if isinstance(value, cls):
                return value
            if isinstance(value, dict):
                normalized = _normalize_json_value(cast(dict[object, object], value))
                if not isinstance(normalized, dict):
                    raise TypeError("JsonObject normalization must return a dict")
                typed_normalized: dict[str, JsonValue] = {}
                for key, item in normalized.items():
                    typed_normalized[key] = cast(JsonValue, item)
                return cls(typed_normalized)
            raise TypeError("JsonObject must be a dict-like object")

        def _ser(value: "JsonObject") -> dict[str, JsonValue]:
            return dict(value)

        return _cs.no_info_after_validator_function(
            _coerce,
            dict_any_schema,
            serialization=_cs.plain_serializer_function_ser_schema(
                _ser,
                return_schema=dict_any_schema,
            ),
        )


class JsonArray(list[JsonValue]):
    """JSON array helper type for Python models."""

    @classmethod
    def __get_pydantic_core_schema__(  # type: ignore[name-defined]
        cls,
        source_type: object,
        handler: object,
    ) -> _cs.CoreSchema:
        list_any_schema = _cs.list_schema(_cs.any_schema())

        def _coerce(value: object) -> "JsonArray":
            if isinstance(value, cls):
                return value
            if isinstance(value, list):
                normalized = _normalize_json_value(cast(list[object], value))
                if not isinstance(normalized, list):
                    raise TypeError("JsonArray normalization must return a list")
                typed_normalized: list[JsonValue] = []
                for item in normalized:
                    typed_normalized.append(cast(JsonValue, item))
                return cls(typed_normalized)
            raise TypeError("JsonArray must be a list-like object")

        def _ser(value: "JsonArray") -> list[JsonValue]:
            return list(value)

        return _cs.no_info_after_validator_function(
            _coerce,
            list_any_schema,
            serialization=_cs.plain_serializer_function_ser_schema(
                _ser,
                return_schema=list_any_schema,
            ),
        )


# Backwards compatible alias (legacy code expects `Json` to behave like an object).
Json = JsonObject
