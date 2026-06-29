"""Dart-specific primitive type implementation."""

from __future__ import annotations
import re
from typing import cast
from typing_extensions import override

from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

from aware_code.primitive_codec_base import CodePrimitiveCodecBase

from dart_grammar.type_parser import DartTypeParser


# Dart type mappings
DART_TYPE_MAPPING: dict[CodePrimitiveBaseType, str] = {
    CodePrimitiveBaseType.any: "dynamic",
    CodePrimitiveBaseType.boolean: "bool",
    CodePrimitiveBaseType.bytes: "Uint8List",
    CodePrimitiveBaseType.datetime: "DateTime",
    CodePrimitiveBaseType.integer: "int",
    CodePrimitiveBaseType.float: "double",
    CodePrimitiveBaseType.json: "Map<String, dynamic>",
    CodePrimitiveBaseType.null: "null",
    CodePrimitiveBaseType.string: "String",
    CodePrimitiveBaseType.uuid: "UuidValue",
    CodePrimitiveBaseType.vector: "List<double>",
    CodePrimitiveBaseType.dict: "Map",
    CodePrimitiveBaseType.array: "List",
}


class DartPrimitiveCodec(CodePrimitiveCodecBase):
    """
    Dart-specific primitive type implementation.

    Extends the core CodePrimitiveType with Dart-specific functionality.
    """

    def __init__(self, parser: DartTypeParser | None = None) -> None:
        self._parser: DartTypeParser = parser or DartTypeParser()

    @override
    def parse_exact(self, type_text: str) -> CodePrimitiveType | None:
        """Exact token mapping for Dart primitives (no generics/nullables).

        Use when caller handled `?`, List/Set/Map wrappers.
        """
        if not type_text:
            return None
        t = type_text.strip()
        low = t.lower()
        # Map exact tokens (case-insensitive) to base types
        if t in ["String"]:
            return self._primitive(base_type=CodePrimitiveBaseType.string)
        if t in ["int"]:
            return self._primitive(base_type=CodePrimitiveBaseType.integer)
        if t in ["double", "num"]:
            return self._primitive(base_type=CodePrimitiveBaseType.float)
        if t in ["bool"]:
            return self._primitive(base_type=CodePrimitiveBaseType.boolean)
        if t in ["DateTime"]:
            return self._primitive(base_type=CodePrimitiveBaseType.datetime)
        if t in ["Uint8List", "Uint8ClampedList", "Int8List"]:
            return self._primitive(base_type=CodePrimitiveBaseType.bytes)
        if t in ["UuidValue"]:
            return self._primitive(base_type=CodePrimitiveBaseType.uuid)
        if low in ["dynamic", "object"]:
            return self._primitive(base_type=CodePrimitiveBaseType.any)
        if low in ["void", "null"]:
            return self._primitive(base_type=CodePrimitiveBaseType.null)
        if t in ["List"]:
            return self._primitive(
                base_type=CodePrimitiveBaseType.array, item_type=self._primitive(base_type=CodePrimitiveBaseType.any)
            )
        if t in ["Map"]:
            return self._primitive(base_type=CodePrimitiveBaseType.dict)
        if t in ["Set"]:
            return self._primitive(
                base_type=CodePrimitiveBaseType.set, item_type=self._primitive(base_type=CodePrimitiveBaseType.any)
            )
        return None

    @override
    def parse(self, type_text: str) -> CodePrimitiveType | None:
        """
        Create a DartPrimitiveType from a Dart type annotation.

        Handles patterns like:
        - String, int, bool, double, DateTime
        - String?, int?, bool? (nullable types)
        - List<String>, Map<String, int>
        - List<String>?, Map<String, int>?
        - dynamic, Object, void
        """
        if not type_text:
            return None

        type_text = type_text.strip()

        # Nullable suffix: T? -> UNION[T, null] (canonical, like Python/Aware)
        opt_inner = self._parser.get_optional_inner(type_text)
        if opt_inner is not None:
            base_type = self.parse(opt_inner)
            if base_type is None:
                return None
            return self.union(base_type, self._primitive(base_type=CodePrimitiveBaseType.null))

        # Generic types: List<T>, Set<T>, Map<K, V>
        list_inner = self._parser.get_list_inner(type_text)
        if list_inner is not None:
            inner_type = self.parse(list_inner)
            if inner_type is None:
                return None
            return self._primitive(base_type=CodePrimitiveBaseType.array, item_type=inner_type)

        set_inner = self._parser.get_set_inner(type_text)
        if set_inner is not None:
            inner_type = self.parse(set_inner) or self._primitive(base_type=CodePrimitiveBaseType.any)
            return self._primitive(base_type=CodePrimitiveBaseType.set, item_type=inner_type)

        kv = self._parser.get_dict_kv(type_text)
        if kv is not None:
            key_s, val_s = kv
            key_type = self.parse(key_s)
            value_type = self.parse(val_s)
            if key_type and value_type:
                return self._primitive(base_type=CodePrimitiveBaseType.dict, key_type=key_type, value_type=value_type)
            return self._primitive(base_type=CodePrimitiveBaseType.dict)

        # String types
        if type_text in ["String"]:
            return self._primitive(base_type=CodePrimitiveBaseType.string)

        # Numeric types
        if type_text in ["int"]:
            return self._primitive(base_type=CodePrimitiveBaseType.integer)
        if type_text in ["double", "num"]:
            return self._primitive(base_type=CodePrimitiveBaseType.float)

        # Boolean
        if type_text in ["bool"]:
            return self._primitive(base_type=CodePrimitiveBaseType.boolean)

        # DateTime
        if type_text in ["DateTime"]:
            return self._primitive(base_type=CodePrimitiveBaseType.datetime)

        # Bytes
        if type_text in ["Uint8List", "Uint8ClampedList", "Int8List"]:
            return self._primitive(base_type=CodePrimitiveBaseType.bytes)

        # Special Dart types
        if type_text in ["dynamic"]:
            return self._primitive(base_type=CodePrimitiveBaseType.any)
        if type_text in ["Object"]:
            return self._primitive(base_type=CodePrimitiveBaseType.any)
        if type_text in ["void"]:
            return self._primitive(base_type=CodePrimitiveBaseType.null)
        if type_text in ["null"]:
            return self._primitive(base_type=CodePrimitiveBaseType.null)

        # UUID types (AWARE-specific)
        if type_text in ["UuidValue"]:
            return self._primitive(base_type=CodePrimitiveBaseType.uuid)

        # Collections without generics
        if type_text in ["List"]:
            return self._primitive(
                base_type=CodePrimitiveBaseType.array, item_type=self._primitive(base_type=CodePrimitiveBaseType.any)
            )
        if type_text in ["Map"]:
            return self._primitive(base_type=CodePrimitiveBaseType.dict)
        if type_text in ["Set"]:
            return self._primitive(
                base_type=CodePrimitiveBaseType.set, item_type=self._primitive(base_type=CodePrimitiveBaseType.any)
            )

        # Unknown identifier (likely a class) -> return None so higher layers treat as CLASS
        return None

    @override
    def render(self, prim: CodePrimitiveType) -> str | None:
        """Convert this primitive type to Dart type annotation syntax."""
        base_type_str = ""

        # Optional (nullable) encoded canonically as UNION[T, null] -> render as `T?`
        if prim.base_type == CodePrimitiveBaseType.union and prim.union_types:
            if len(prim.union_types) == 2 and any(t.base_type == CodePrimitiveBaseType.null for t in prim.union_types):
                non_null = next(t for t in prim.union_types if t.base_type != CodePrimitiveBaseType.null)
                inner = self.render(non_null) or "dynamic"
                # Avoid invalid double-nullable like `Object??` when inner is already nullable.
                if inner.endswith("?"):
                    return inner
                return f"{inner}?"
            # Dart has no general unions
            return "Object"

        # Handle array types (List<T>)
        if prim.base_type == CodePrimitiveBaseType.array:
            if prim.item_type:
                item_type_str = self.render(prim.item_type)
                if item_type_str:
                    base_type_str = f"List<{item_type_str}>"
                else:
                    base_type_str = "List<dynamic>"
            else:
                base_type_str = "List<dynamic>"

        # Handle set types (Set<T>)
        elif prim.base_type == CodePrimitiveBaseType.set:
            if prim.item_type:
                item_type_str = self.render(prim.item_type)
                if item_type_str:
                    base_type_str = f"Set<{item_type_str}>"
                else:
                    base_type_str = "Set<dynamic>"
            else:
                base_type_str = "Set<dynamic>"

        # Handle dictionary types (Map<K, V>)
        elif prim.base_type == CodePrimitiveBaseType.dict:
            if prim.key_type and prim.value_type:
                key_type_str = self.render(prim.key_type) or "String"
                value_type_str = self.render(prim.value_type) or "dynamic"
                base_type_str = f"Map<{key_type_str}, {value_type_str}>"
            else:
                base_type_str = "Map<String, dynamic>"

        # Handle JSON leaf variants (JsonValue/JsonObject/JsonArray) via json_kind constraint.
        elif prim.base_type == CodePrimitiveBaseType.json:
            kind = None
            if prim.constraints:
                kind_val = prim.constraints.get("json_kind")
                if isinstance(kind_val, str):
                    kind = kind_val.lower()
            if kind == "array":
                base_type_str = "List<dynamic>"
            elif kind == "value":
                # Use Object? to allow JSON null without relying on descriptor optionality.
                base_type_str = "Object?"
            else:
                # Default / legacy Json = object-shaped JSON.
                base_type_str = "Map<String, dynamic>"

        else:
            # Get from Dart type mapping
            dart_type = DART_TYPE_MAPPING.get(prim.base_type)
            if dart_type:
                base_type_str = dart_type
            else:
                base_type_str = "dynamic"

        return base_type_str

    @override
    def is_void(self, type_text: str) -> bool:
        """Check if a Dart type is void."""
        return type_text.lower() in ["void", "null"]

    @override
    def is_list(self, type_text: str, include_set: bool = True) -> bool:
        """
        Check if a Dart type string represents a list/array.
        By default, this will also check for set types.

        Detects patterns like:
        - List<Type>
        - List<Type>?
        - Set<Type>
        - Set<Type>?

        Args:
            type_str: The Dart type string to check
            include_set: Whether to include set types in the check (default: True)
        Returns:
            True if the type represents a list/array, False otherwise
        """
        if not type_text:
            return False
        s = type_text.strip()
        opt_inner = self._parser.get_optional_inner(s)
        if opt_inner is not None:
            s = opt_inner
        if self._parser.get_list_inner(s) is not None:
            return True
        if include_set and self._parser.get_set_inner(s) is not None:
            return True
        return False

    @override
    def is_set(self, type_text: str) -> bool:
        """
        Check if a Dart type string represents a set type.
        """
        if not type_text:
            return False
        s = type_text.strip()
        opt_inner = self._parser.get_optional_inner(s)
        if opt_inner is not None:
            s = opt_inner
        return self._parser.get_set_inner(s) is not None

    @override
    def get_inner_type(self, type_text: str) -> str:
        """
        Extract the inner type from a Dart list/array/collection type string.

        Examples:
        - List<String> -> String
        - List<int> -> int
        - Set<User> -> User
        - List<String>? -> String?
        - Set<MyType>? -> MyType?

        Args:
            type_str: The Dart type string to extract from

        Returns:
            The inner type string, or the original string if not a list type
        """
        if not type_text:
            return type_text

        original_type_str = type_text
        s = type_text.strip()

        was_nullable = False
        opt_inner = self._parser.get_optional_inner(s)
        if opt_inner is not None:
            was_nullable = True
            s = opt_inner

        inner = self._parser.get_list_inner(s)
        if inner is None:
            inner = self._parser.get_set_inner(s)
        if inner is not None:
            return f"{inner.strip()}?" if was_nullable else inner.strip()

        return original_type_str

    @override
    def enum_ident(self, type_text: str) -> str:
        """
        Return the canonical name for enum comparison.

        Strips Dart-specific adornments like nullable markers.
        """
        # Remove nullable marker
        if type_text.endswith("?"):
            type_text = type_text[:-1]

        # Remove generic parameters (not common for enums but for completeness)
        if "<" in type_text and ">" in type_text:
            type_text = re.sub(r"<[^>]*>", "", type_text)

        return type_text.strip()

    @override
    def parse_literal(self, literal: str) -> object:
        """Parse a Dart literal into a Dart value."""
        lit = literal.strip()

        # Handle null
        if lit.lower() == "null":
            return None

        # Handle boolean literals
        if lit.lower() == "true":
            return True
        if lit.lower() == "false":
            return False

        # Handle string literals (single or double quotes)
        if (lit.startswith("'") and lit.endswith("'")) or (lit.startswith('"') and lit.endswith('"')):
            content = lit[1:-1]
            content = content.replace(r"\'", "'")
            content = content.replace(r"\"", '"')
            content = content.replace(r"\\", "\\")
            content = content.replace(r"\n", "\n")
            content = content.replace(r"\t", "\t")
            content = content.replace(r"\r", "\r")
            return content

        # Handle numeric literals
        try:
            if "." not in lit and "e" not in lit.lower():
                return int(lit)
            else:
                return float(lit)
        except ValueError:
            pass

        # Handle list literals []
        if lit.startswith("[") and lit.endswith("]"):
            try:
                content = lit[1:-1].strip()
                if not content:
                    return []
                return lit
            except Exception:
                return lit

        # Handle map literals {}
        if lit.startswith("{") and lit.endswith("}"):
            try:
                content = lit[1:-1].strip()
                if not content:
                    return {}
                return lit
            except Exception:
                return lit

        # Handle const expressions
        if lit.startswith("const "):
            return self.parse_literal(lit[6:].strip())

        return lit

    @override
    def to_literal_string(self, value: object) -> str:
        """Convert a Python value to a Dart literal string."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            escaped = value.replace("\\", "\\\\")
            escaped = escaped.replace("'", "\\'")
            escaped = escaped.replace("\n", "\\n")
            escaped = escaped.replace("\t", "\\t")
            escaped = escaped.replace("\r", "\\r")
            return f"'{escaped}'"
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, float):
            return str(value)
        elif isinstance(value, list):
            list_value = cast(list[object], value)
            elements = [self.to_literal_string(item) for item in list_value]
            return f"[{', '.join(elements)}]"
        elif isinstance(value, dict):
            dict_value = cast(dict[object, object], value)
            pairs: list[str] = []
            for k, v in dict_value.items():
                key_str = self.to_literal_string(k)
                value_str = self.to_literal_string(v)
                pairs.append(f"{key_str}: {value_str}")
            return f"{{{', '.join(pairs)}}}"
        elif isinstance(value, set):
            set_value = cast(set[object], value)
            elements = [self.to_literal_string(item) for item in set_value]
            return f"{{{', '.join(elements)}}}"
        else:
            return f"'{str(value)}'"
