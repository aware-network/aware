"""Aware implementation of the primitive types."""

import re
from typing import ClassVar, cast
from typing import final

from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

from aware_grammar.type_parser import AwareTypeParser

from aware_code.primitive_codec_base import CodePrimitiveCodecBase
from aware_code.types.json import JsonObject, JsonValue
from typing_extensions import override


# Aware type mappings to base types
AWARE_TO_BASE_MAPPING: dict[str, CodePrimitiveBaseType] = {
    "Any": CodePrimitiveBaseType.any,
    "Bool": CodePrimitiveBaseType.boolean,
    "Bytes": CodePrimitiveBaseType.bytes,
    "DateTime": CodePrimitiveBaseType.datetime,
    "Float": CodePrimitiveBaseType.float,
    "Int": CodePrimitiveBaseType.integer,
    "Json": CodePrimitiveBaseType.json,
    "JsonArray": CodePrimitiveBaseType.json,
    "JsonObject": CodePrimitiveBaseType.json,
    "JsonValue": CodePrimitiveBaseType.json,
    "Null": CodePrimitiveBaseType.null,
    "String": CodePrimitiveBaseType.string,
    "UUID": CodePrimitiveBaseType.uuid,
    "Vector": CodePrimitiveBaseType.vector,
}

_JSON_KIND_CONSTRAINT_KEY = "json_kind"
_JSON_KIND_BY_AWARE_TOKEN: dict[str, str] = {
    "JsonArray": "array",
    "JsonObject": "object",
    "JsonValue": "value",
}

# Optional lists are invalid in canonical Aware (use optional elements instead).
OPTIONAL_LIST_TYPE_ERROR_PREFIX = "Optional list types are not allowed"

# Base type to Aware type mappings (reverse of above)
BASE_TO_AWARE_MAPPING: dict[CodePrimitiveBaseType, str] = {
    CodePrimitiveBaseType.any: "Any",
    CodePrimitiveBaseType.boolean: "Bool",
    CodePrimitiveBaseType.datetime: "DateTime",
    CodePrimitiveBaseType.bytes: "Bytes",
    CodePrimitiveBaseType.float: "Float",
    CodePrimitiveBaseType.integer: "Int",
    CodePrimitiveBaseType.null: "Null",
    CodePrimitiveBaseType.json: "Json",
    CodePrimitiveBaseType.string: "String",
    CodePrimitiveBaseType.uuid: "UUID",
    CodePrimitiveBaseType.vector: "Vector",
}


def _coerce_json_literal(value: object) -> JsonValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        list_value = cast(list[object], value)
        normalized_items: list[object] = []
        for item in list_value:
            normalized_items.append(_coerce_json_literal(item))
        return normalized_items
    if isinstance(value, dict):
        dict_value = cast(dict[object, object], value)
        normalized: dict[str, object] = {}
        for key, item in dict_value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            normalized[key] = _coerce_json_literal(item)
        return normalized
    raise ValueError(f"Unsupported JSON literal value: {value!r}")


@final
class AwarePrimitiveCodec(CodePrimitiveCodecBase):
    """
    Aware-specific primitive type implementation.

    Extends the core CodePrimitiveCodec with Aware language specific functionality.
    """

    CAST_RX: ClassVar[re.Pattern[str]] = re.compile(
        r"""
        ^                       # start of string
        (?P<val>                # capture the literal itself…
            (?:
                '([^']|\\')*'   # …single-quoted string
            | "([^"]|\\" )*"  # …or double-quoted string
            | [^:]+           # …or any non-string literal (number, true/false, …)
            )
        )
        \s*::\s*                # optional whitespace + double colon
        (?P<cast>[A-Za-z0-9_\.]+) # the type name (event_status, public.some_type, …)
        $                       # end of string
    """,
        re.VERBOSE | re.IGNORECASE,
    )

    def __init__(self, parser: AwareTypeParser | None = None) -> None:
        self._parser = parser or AwareTypeParser()

    def _assert_not_optional_list(self, raw: str) -> None:
        if not raw:
            return
        opt_inner = self._parser.get_optional_suffix_inner(raw)
        if opt_inner is None:
            return
        if self._parser.get_array_suffix_inner(opt_inner) is not None:
            raise ValueError(f"{OPTIONAL_LIST_TYPE_ERROR_PREFIX}: {raw}")

    @override
    def parse_exact(self, type_text: str) -> CodePrimitiveType | None:
        """Exact token mapping for Aware primitives (no wrappers/params).

        Use when the caller already handled optional/collections/parametrics.
        Matches against AWARE_TO_BASE_MAPPING keys case-insensitively.
        """
        if not type_text:
            return None
        t = type_text.strip()
        # Strip simple quotes
        if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
            t = t[1:-1]
        # Remove parametric suffix like Vector(1536) using the raw-token SSOT
        call = self._parser.get_parametric_call(t)
        if call is not None:
            name, _params = call
            t = name
        # Exact match ignoring case
        for k, base in AWARE_TO_BASE_MAPPING.items():
            if k.lower() == t.lower():
                if base == CodePrimitiveBaseType.json and k in _JSON_KIND_BY_AWARE_TOKEN:
                    return self._primitive(
                        base_type=base,
                        constraints=JsonObject({_JSON_KIND_CONSTRAINT_KEY: _JSON_KIND_BY_AWARE_TOKEN[k]}),
                    )
                return self._primitive(base_type=base)
        return None

    @override
    def parse(self, type_text: str) -> CodePrimitiveType | None:
        """
        Create an AwarePrimitiveCodec from an Aware type string.

        Args:
            type_str: Aware type definition (e.g., "Int", "String[]", "Vector(1536)")

        Returns:
            AwarePrimitiveCodec instance representing the Aware type
        """
        raw = (type_text or "").strip()
        if not raw:
            return None
        raw = self._parser.strip_edge_annotation(self._parser.strip_trailing_field_modifiers(raw))
        self._assert_not_optional_list(raw)

        # Handle optional types (marked with ?)
        opt_inner = self._parser.get_optional_suffix_inner(raw)
        if opt_inner is not None:
            base_instance = self.parse(opt_inner)
            if not base_instance:
                return None
            return self.union(base_instance, self._primitive(base_type=CodePrimitiveBaseType.null))

        # Handle array types (marked with [])
        arr_inner = self._parser.get_array_suffix_inner(raw)
        if arr_inner is not None:
            item_type = self.parse(arr_inner)
            if not item_type:
                return None
            return self._primitive(base_type=CodePrimitiveBaseType.array, item_type=item_type)

        # Handle dictionary types (Dict[K, V])
        kv = self._parser.get_dict_kv(raw)
        if kv is not None:
            key_text, value_text = kv
            key_type = self.parse(key_text)
            value_type = self.parse(value_text)
            if not key_type or not value_type:
                return None
            return self._primitive(
                base_type=CodePrimitiveBaseType.dict,
                key_type=key_type,
                value_type=value_type,
            )

        # Handle parametric types (e.g., Vector(1536))
        call = self._parser.get_parametric_call(raw)
        if call is not None:
            base_type_name, params = call
            if base_type_name in AWARE_TO_BASE_MAPPING:
                base_type = AWARE_TO_BASE_MAPPING[base_type_name]
                if base_type == CodePrimitiveBaseType.vector:
                    try:
                        dimension = int(params.strip())
                        return self._primitive(
                            base_type=base_type,
                            constraints=JsonObject({"dimension": dimension}),
                        )
                    except Exception:
                        return self._primitive(base_type=base_type)
                parameters = [p.strip() for p in params.split(",") if p.strip()]
                parameter_values: list[object] = [*parameters]
                return self._primitive(
                    base_type=base_type,
                    constraints=JsonObject({"parameters": parameter_values}) if parameters else None,
                )
            return None

        # Handle primitive types (exact tokens)
        prim = self.parse_exact(raw)
        if prim is not None:
            return prim

        return None

    @override
    def render(self, prim: CodePrimitiveType) -> str:
        """
        Convert this primitive type to Aware type syntax.

        Returns:
            Aware type string
        """
        # Handle array types
        if prim.base_type == CodePrimitiveBaseType.array and prim.item_type:
            return f"{self.render(prim.item_type)}[]"

        # Handle dictionary types
        if prim.base_type == CodePrimitiveBaseType.dict:
            if prim.key_type and prim.value_type:
                return f"Dict[{self.render(prim.key_type)}, {self.render(prim.value_type)}]"
            return "Dict"

        # Handle union types (e.g., optional types)
        if prim.base_type == CodePrimitiveBaseType.union and prim.union_types:
            # Check if this is an optional type (union with null)
            if len(prim.union_types) == 2 and any(t.base_type == CodePrimitiveBaseType.null for t in prim.union_types):
                # Find the non-null type
                non_null_type = next(t for t in prim.union_types if t.base_type != CodePrimitiveBaseType.null)
                return f"{self.render(non_null_type)}?"

            # For other union types, just join with "|" (not in current grammar but future-proof)
            return " | ".join(self.render(t) for t in prim.union_types)

        # Handle JSON type variants (JsonValue/JsonObject/JsonArray)
        if prim.base_type == CodePrimitiveBaseType.json:
            kind = None
            if prim.constraints is not None:
                kind_val = prim.constraints.get(_JSON_KIND_CONSTRAINT_KEY)
                if isinstance(kind_val, str):
                    kind = kind_val.lower()
            if kind == "value":
                return "JsonValue"
            if kind == "object":
                return "JsonObject"
            if kind == "array":
                return "JsonArray"

        # Handle parametric types using constraints
        if prim.constraints and prim.base_type in BASE_TO_AWARE_MAPPING:
            base_name = BASE_TO_AWARE_MAPPING[prim.base_type]

            # For Vector types, check for dimension constraint
            if prim.base_type == CodePrimitiveBaseType.vector and "dimension" in prim.constraints:
                dimension = prim.constraints["dimension"]
                return f"{base_name}({dimension})"

            # For other parametric types, check for parameters constraint
            elif "parameters" in prim.constraints:
                parameters = prim.constraints["parameters"]
                if isinstance(parameters, list):
                    params_str = ", ".join(str(p) for p in parameters)
                else:
                    params_str = str(parameters)
                return f"{base_name}({params_str})"

        # Handle Normal Types
        if prim.base_type in BASE_TO_AWARE_MAPPING:
            return BASE_TO_AWARE_MAPPING[prim.base_type]

        raise ValueError(f"Unknown primitive type: {prim.base_type}")

    @override
    def enum_ident(self, type_text: str) -> str:
        """
        Aware grammar encodes cardinality in the suffix:
            Foo?   -> optional
            Bar[]  -> array
        Remove those decorations to expose the semantic type name.
        """
        raw = self._parser.strip_edge_annotation(self._parser.strip_trailing_field_modifiers(type_text)).strip()
        self._assert_not_optional_list(raw)
        return self._parser.enum_ident(raw)

    def is_primitive_type(self, type_str: str) -> bool:
        """Check if a string represents an Aware primitive type."""
        raw = self._parser.strip_edge_annotation(self._parser.strip_trailing_field_modifiers(type_str)).strip()
        self._assert_not_optional_list(raw)
        clean_type = self._parser.enum_ident(raw)
        if clean_type == "Dict":
            return True
        return clean_type in AWARE_TO_BASE_MAPPING

    def is_vector_type(self, type_str: str) -> bool:
        """Check if a string represents a Vector type (with or without parameters)."""
        raw = self._parser.strip_edge_annotation(self._parser.strip_trailing_field_modifiers(type_str)).strip()
        self._assert_not_optional_list(raw)
        return self._parser.enum_ident(raw) == "Vector"

    def get_vector_dimension(self, type_str: str) -> int | None:
        """Extract the dimension from a Vector type string like 'Vector(1536)'."""
        raw = self._parser.strip_edge_annotation(self._parser.strip_trailing_field_modifiers(type_str))
        self._assert_not_optional_list(raw)
        # Strip outer decorations
        opt_inner = self._parser.get_optional_suffix_inner(raw)
        if opt_inner is not None:
            raw = opt_inner
        arr_inner = self._parser.get_array_suffix_inner(raw)
        if arr_inner is not None:
            raw = arr_inner
        call = self._parser.get_parametric_call(raw)
        if call is None:
            return None
        name, params = call
        if name != "Vector":
            return None
        try:
            return int(params.strip())
        except Exception:
            return None

    @override
    def is_void(self, type_text: str) -> bool:
        """Check if an Aware type is void."""
        return type_text in ["Void", "void"]

    @override
    def is_list(self, type_text: str) -> bool:
        """
        Check if an Aware type string represents a list/array/collection.

        Detects patterns like:
        - Type[]

        Args:
            type_str: The Aware type string to check

        Returns:
            True if the type represents a list/array/collection, False otherwise
        """
        if not type_text:
            return False
        raw = self._parser.strip_edge_annotation(self._parser.strip_trailing_field_modifiers(type_text)).strip()
        self._assert_not_optional_list(raw)
        opt_inner = self._parser.get_optional_suffix_inner(raw)
        if opt_inner is not None:
            raw = opt_inner
        return self._parser.get_array_suffix_inner(raw) is not None

    @override
    def is_set(self, type_text: str) -> bool:
        """Aware Grammar doesn't support set types."""
        return False

    @override
    def get_inner_type(self, type_text: str) -> str:
        """
        Extract the inner type from an Aware list/array/collection type string.

        Examples:
        - String[] -> String
        - Int[] -> Int
        - User[] -> User
        - Vector(1536)[] -> Vector(1536)

        Args:
            type_str: The Aware type string to extract from

        Returns:
            The inner type string, or the original string if not a list type
        """
        if not type_text:
            return type_text

        original = type_text
        raw = self._parser.strip_edge_annotation(self._parser.strip_trailing_field_modifiers(type_text)).strip()
        self._assert_not_optional_list(raw)

        arr_inner = self._parser.get_array_suffix_inner(raw)
        if arr_inner is not None:
            return arr_inner

        return original

    # ------------------------------------------------------------------
    # Literal parsing helpers
    # ------------------------------------------------------------------

    @override
    def parse_literal(self, literal: str) -> object:
        """
        Parse an Aware‐language literal.
        Removes a trailing ``::TYPE`` cast if present, because the cast is
        redundant at the canonical layer and confuses the Python parser.
        """
        m = self.CAST_RX.match(literal.strip())
        if m:
            literal = m.group("val")  # keep only the literal token

        return self.python_parse_literal(literal)

    def python_parse_literal(self, literal: str) -> object:
        """Parse a raw Python literal (as captured from source) into a runtime value.

        This is used when translating default values from code into the
        language-agnostic meta-model. Where possible we rely on
        ``ast.literal_eval`` to safely evaluate the literal, falling back to
        simple heuristics when evaluation fails (e.g., for factory
        expressions or complex call expressions).

        NOTE: Copied from PythonPrimitiveCodec.parse_literal to avoid importing python_grammar at aware_grammar.
        """
        import ast

        lit = literal.strip()

        # Strict JSON literals for objects/arrays.
        #
        # Canonical Aware now supports JSON object/array literals for defaults (e.g. `{}` / `[]`).
        # We intentionally enforce strict JSON (double-quoted strings, no trailing commas) here so
        # defaults round-trip deterministically across materializations.
        if lit.startswith("{") or lit.startswith("["):
            import json

            try:
                parsed = cast(object, json.loads(lit))
                return _coerce_json_literal(parsed)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON literal: {e.msg}") from e

        # Explicit None/null handling
        if lit.lower() in {"none", "null"}:
            return None

        # Quickly map common boolean values that ast.literal_eval also handles
        if lit.lower() in {"true", "false"}:
            return lit.lower() == "true"

        # Attempt safe evaluation
        try:
            value = cast(object, ast.literal_eval(lit))
            # Convert sets to lists for JSON serialization
            if isinstance(value, set):
                set_value = cast(set[object], value)
                return list(set_value)
            return value
        except (ValueError, SyntaxError):
            # literal_eval failed – fall back.
            pass

        # Strip surrounding quotes for simple strings like 'hello' or "hello"
        if (lit.startswith("'") and lit.endswith("'")) or (lit.startswith('"') and lit.endswith('"')):
            return lit[1:-1]

        # As a last resort, return the raw text
        return lit

    @override
    def to_literal_string(self, value: object) -> str:
        """Convert a Python value to an Aware literal string.

        According to Aware's tree-sitter grammar, scalar literals are defined as:
        - string_literal: single or double quoted strings
        - number_literal: integers and decimals
        - boolean_literal: 'true' or 'false'
        - null_literal: 'null'

        Canonical defaults additionally support strict JSON object/array literals
        (e.g. `{}` / `[]`) so complex values can round-trip across
        materializations without being encoded as strings.

        Examples:
            True -> "true"
            "hello" -> "\"hello\""
            123 -> "123"
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            # Use double quotes for strings in Aware language
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, tuple, dict)):
            # Canonical defaults now support strict JSON objects/arrays in source.
            # Render complex values as JSON literals (unquoted) so they round-trip
            # through the parser and meta layer.
            import json

            try:
                serializable: object
                if isinstance(value, tuple):
                    serializable = list(cast(tuple[object, ...], value))
                elif isinstance(value, list):
                    serializable = cast(list[object], value)
                else:
                    serializable = cast(dict[str, object], value)
                return json.dumps(serializable, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            except (TypeError, ValueError):
                str_val = str(cast(object, value))
                escaped = str_val.replace('"', '\\"')
                return f'"{escaped}"'
        else:
            # For any other type, convert to string and quote
            str_val = str(value)
            escaped = str_val.replace('"', '\\"')
            return f'"{escaped}"'
