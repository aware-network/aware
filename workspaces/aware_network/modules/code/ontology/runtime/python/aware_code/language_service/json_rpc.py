from __future__ import annotations

from typing import TypeAlias

JsonPrimitive: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonPrimitive | dict[str, "JsonValue"] | list["JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]
JsonArray: TypeAlias = list[JsonValue]

__all__ = [
    "JsonArray",
    "JsonObject",
    "JsonPrimitive",
    "JsonValue",
]
