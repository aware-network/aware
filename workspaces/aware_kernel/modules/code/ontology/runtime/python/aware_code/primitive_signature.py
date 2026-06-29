"""Canonical structural signatures for CodePrimitiveType."""

from __future__ import annotations

import json

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

# Code Runtime
from aware_code.types import JsonObject


def _constraints_tag(
    *,
    base_type: CodePrimitiveBaseType,
    constraints: JsonObject | None,
) -> str:
    if constraints is None:
        return ""
    raw = dict(constraints)
    if base_type == CodePrimitiveBaseType.json:
        json_kind = raw.get("json_kind")
        if json_kind in {"value", "object", "array"} and len(raw) == 1:
            return f"<{json_kind}>"
    if base_type == CodePrimitiveBaseType.vector:
        dimension = raw.get("dimension")
        if isinstance(dimension, int) and len(raw) == 1:
            return f"<{dimension}>"
    payload = json.dumps(raw, sort_keys=True, separators=(",", ":"))
    return payload


def build_code_primitive_signature(
    *,
    base_type: CodePrimitiveBaseType,
    item_type: CodePrimitiveType | None = None,
    key_type: CodePrimitiveType | None = None,
    value_type: CodePrimitiveType | None = None,
    element_types: tuple[CodePrimitiveType, ...] = (),
    union_types: tuple[CodePrimitiveType, ...] = (),
    constraints: JsonObject | None = None,
) -> str:
    base = base_type.value
    if base_type in {
        CodePrimitiveBaseType.any,
        CodePrimitiveBaseType.boolean,
        CodePrimitiveBaseType.bytes,
        CodePrimitiveBaseType.datetime,
        CodePrimitiveBaseType.float,
        CodePrimitiveBaseType.integer,
        CodePrimitiveBaseType.null,
        CodePrimitiveBaseType.string,
        CodePrimitiveBaseType.uuid,
        CodePrimitiveBaseType.json,
        CodePrimitiveBaseType.vector,
    }:
        return f"{base}{_constraints_tag(base_type=base_type, constraints=constraints)}"
    if base_type in {CodePrimitiveBaseType.array, CodePrimitiveBaseType.set}:
        if item_type is None:
            raise ValueError(f"{base} requires item_type for canonical signature")
        return f"{base}<{item_type.signature}>"
    if base_type == CodePrimitiveBaseType.dict:
        if key_type is None or value_type is None:
            raise ValueError("dict requires key_type and value_type for canonical signature")
        return f"dict<{key_type.signature},{value_type.signature}>"
    if base_type == CodePrimitiveBaseType.tuple:
        if not element_types:
            raise ValueError("tuple requires at least one element type for canonical signature")
        return "tuple<" + ",".join(element.signature for element in element_types) + ">"
    if base_type == CodePrimitiveBaseType.union:
        if not union_types:
            raise ValueError("union requires at least one member type for canonical signature")
        return "union<" + "|".join(member.signature for member in union_types) + ">"
    raise ValueError(f"Unsupported CodePrimitiveBaseType for canonical signature: {base_type.value}")
