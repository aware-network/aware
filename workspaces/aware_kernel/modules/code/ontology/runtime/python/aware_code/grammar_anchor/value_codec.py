from __future__ import annotations

import json
import math

from aware_code_sdk.dto import (
    CodeGrammarAnchorRenderSemanticValue,
    CodeGrammarAnchorRenderSemanticValueKind,
)


class CodeGrammarValueCodecError(ValueError):
    pass


_AWARE_PRIMITIVE_TYPE_TEXT = {
    "any": "Any",
    "boolean": "Bool",
    "bool": "Bool",
    "bytes": "Bytes",
    "datetime": "DateTime",
    "date_time": "DateTime",
    "float": "Float",
    "integer": "Int",
    "int": "Int",
    "json": "Json",
    "string": "String",
    "uuid": "UUID",
    "vector": "Vector",
}


def decode_aware_string_literal(source_text: str) -> str:
    text = source_text.strip()
    if len(text) < 2 or text[0] != text[-1] or text[0] not in {'"', "'"}:
        return text
    if text[0] == '"':
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            return text[1:-1]
        return decoded if isinstance(decoded, str) else text[1:-1]
    return text[1:-1]


def encode_code_grammar_anchor_semantic_value(
    *,
    value_domain: str | None,
    semantic_value: CodeGrammarAnchorRenderSemanticValue,
) -> str:
    if value_domain == "identifier":
        return _encode_identifier(semantic_value)
    if value_domain == "aware_string_literal":
        return _encode_aware_string_literal(semantic_value)
    if value_domain == "aware_default_value":
        return _encode_aware_default_value(semantic_value)
    if value_domain == "aware_type_ref":
        return _encode_aware_type_ref(semantic_value)
    raise CodeGrammarValueCodecError(
        f"unsupported grammar render value_domain: {value_domain!r}"
    )


def _encode_identifier(
    semantic_value: CodeGrammarAnchorRenderSemanticValue,
) -> str:
    if semantic_value.kind != CodeGrammarAnchorRenderSemanticValueKind.string:
        raise CodeGrammarValueCodecError(
            "identifier requires semantic value kind string"
        )
    value = semantic_value.string_value
    if value is None or not value.isidentifier():
        raise CodeGrammarValueCodecError(
            "identifier requires an identifier-shaped string_value"
        )
    return value


def _encode_aware_string_literal(
    semantic_value: CodeGrammarAnchorRenderSemanticValue,
) -> str:
    if semantic_value.kind != CodeGrammarAnchorRenderSemanticValueKind.string:
        raise CodeGrammarValueCodecError(
            "aware_string_literal requires semantic value kind string"
        )
    if semantic_value.string_value is None:
        raise CodeGrammarValueCodecError("aware_string_literal requires string_value")
    return json.dumps(semantic_value.string_value, ensure_ascii=False)


def _encode_aware_default_value(
    semantic_value: CodeGrammarAnchorRenderSemanticValue,
) -> str:
    kind = semantic_value.kind
    if kind == CodeGrammarAnchorRenderSemanticValueKind.string:
        if semantic_value.string_value is None:
            raise CodeGrammarValueCodecError(
                "aware_default_value string requires string_value"
            )
        return json.dumps(semantic_value.string_value, ensure_ascii=False)
    if kind == CodeGrammarAnchorRenderSemanticValueKind.boolean:
        if semantic_value.boolean_value is None:
            raise CodeGrammarValueCodecError(
                "aware_default_value boolean requires boolean_value"
            )
        return "true" if semantic_value.boolean_value else "false"
    if kind == CodeGrammarAnchorRenderSemanticValueKind.integer:
        if semantic_value.integer_value is None:
            raise CodeGrammarValueCodecError(
                "aware_default_value integer requires integer_value"
            )
        return str(semantic_value.integer_value)
    if kind == CodeGrammarAnchorRenderSemanticValueKind.float:
        if semantic_value.float_value is None or not math.isfinite(
            semantic_value.float_value
        ):
            raise CodeGrammarValueCodecError(
                "aware_default_value float requires a finite float_value"
            )
        return json.dumps(semantic_value.float_value, allow_nan=False)
    if kind == CodeGrammarAnchorRenderSemanticValueKind.null:
        return "null"
    if kind == CodeGrammarAnchorRenderSemanticValueKind.json:
        return json.dumps(
            semantic_value.json_value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    raise CodeGrammarValueCodecError(
        f"aware_default_value does not support semantic value kind {kind.value!r}"
    )


def _encode_aware_type_ref(
    semantic_value: CodeGrammarAnchorRenderSemanticValue,
) -> str:
    if semantic_value.kind != CodeGrammarAnchorRenderSemanticValueKind.type_ref:
        raise CodeGrammarValueCodecError(
            "aware_type_ref requires semantic value kind type_ref"
        )
    type_ref = semantic_value.type_ref_value
    if type_ref is None or not type_ref.type_name.strip():
        raise CodeGrammarValueCodecError(
            "aware_type_ref requires type_ref_value.type_name"
        )
    type_key = type_ref.type_name.rsplit(".", maxsplit=1)[-1].lower()
    rendered_type = _AWARE_PRIMITIVE_TYPE_TEXT.get(type_key)
    if rendered_type is None:
        raise CodeGrammarValueCodecError(
            f"aware_type_ref primitive type is unsupported: {type_ref.type_name!r}"
        )
    return f"{rendered_type}?" if type_ref.nullable else rendered_type


__all__ = [
    "CodeGrammarValueCodecError",
    "decode_aware_string_literal",
    "encode_code_grammar_anchor_semantic_value",
]
