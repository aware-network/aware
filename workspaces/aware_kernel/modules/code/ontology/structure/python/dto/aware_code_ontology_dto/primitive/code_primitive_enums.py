from __future__ import annotations

# Standard
from enum import Enum


class CodePrimitiveBaseType(Enum):
    """Code Primitive BaseType enum."""

    boolean = "boolean"
    bytes = "bytes"
    datetime = "datetime"
    float = "float"
    integer = "integer"
    string = "string"
    uuid = "uuid"
    array = "array"
    dict = "dict"
    tuple = "tuple"
    set = "set"
    union = "union"
    any = "any"
    null = "null"
    json = "json"
    vector = "vector"
