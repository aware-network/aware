"""Python-specific primitive type implementation."""

import ast
from typing import cast
from typing_extensions import override

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

from aware_code.primitive_codec_base import CodePrimitiveCodecBase
from aware_code.type_descriptor_nodes import CollectionKind
from aware_code.types import JsonObject

from python_grammar.type_parser import PythonTypeParser


# Python type mappings
PYTHON_TYPE_MAPPING: dict[CodePrimitiveBaseType, str] = {
    CodePrimitiveBaseType.any: "Any",
    CodePrimitiveBaseType.boolean: "bool",
    CodePrimitiveBaseType.bytes: "bytes",
    CodePrimitiveBaseType.datetime: "datetime",
    CodePrimitiveBaseType.integer: "int",
    CodePrimitiveBaseType.float: "float",
    CodePrimitiveBaseType.json: "Json",
    CodePrimitiveBaseType.null: "None",
    CodePrimitiveBaseType.string: "str",
    CodePrimitiveBaseType.uuid: "UUID",
    CodePrimitiveBaseType.vector: "Vector",
    CodePrimitiveBaseType.dict: "dict",
    CodePrimitiveBaseType.array: "list",
}


class PythonPrimitiveCodec(CodePrimitiveCodecBase):
    """
    Python-specific primitive type implementation.

    Extends the core CodePrimitiveType with Python-specific functionality.
    """

    is_classvar: bool = False  # Track if this was originally a ClassVar[T]

    def __init__(self, parser: PythonTypeParser | None = None):
        self._parser: PythonTypeParser = parser or PythonTypeParser()

    @override
    def parse_exact(self, type_text: str) -> CodePrimitiveType | None:
        """Exact token mapping for Python primitives (no generics/unions).

        Use when structural wrappers (Optional, List, Dict, Union) are handled elsewhere.
        """
        if not type_text:
            return None
        t = type_text.strip()
        # Strip quotes
        if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
            t = t[1:-1]
        low = t.lower()
        exact_map = {
            "any": CodePrimitiveBaseType.any,
            "object": CodePrimitiveBaseType.any,
            "list": CodePrimitiveBaseType.array,
            "bool": CodePrimitiveBaseType.boolean,
            "boolean": CodePrimitiveBaseType.boolean,
            "bytes": CodePrimitiveBaseType.bytes,
            "bytearray": CodePrimitiveBaseType.bytes,
            "datetime": CodePrimitiveBaseType.datetime,
            "dict": CodePrimitiveBaseType.dict,
            "date": CodePrimitiveBaseType.datetime,
            "time": CodePrimitiveBaseType.datetime,
            "int": CodePrimitiveBaseType.integer,
            "integer": CodePrimitiveBaseType.integer,
            "float": CodePrimitiveBaseType.float,
            "double": CodePrimitiveBaseType.float,
            "decimal": CodePrimitiveBaseType.float,
            "numeric": CodePrimitiveBaseType.float,
            "json": CodePrimitiveBaseType.json,
            "jsonarray": CodePrimitiveBaseType.json,
            "jsonobject": CodePrimitiveBaseType.json,
            "jsonvalue": CodePrimitiveBaseType.json,
            "none": CodePrimitiveBaseType.null,
            "nonetype": CodePrimitiveBaseType.null,
            "set": CodePrimitiveBaseType.set,
            "str": CodePrimitiveBaseType.string,
            "string": CodePrimitiveBaseType.string,
            "uuid": CodePrimitiveBaseType.uuid,
            "uuidvalue": CodePrimitiveBaseType.uuid,
            "vector": CodePrimitiveBaseType.vector,
        }
        base = exact_map.get(low)
        if base is None and "." in low:
            # Accept dotted primitive references like `uuid.UUID` and `datetime.datetime`
            # by attempting to map the final identifier token.
            leaf = low.rsplit(".", 1)[-1].strip()
            base = exact_map.get(leaf)
        if base is None:
            # Unknown token: do not coerce to Any. Callers that want a fallback
            # should explicitly use self.any(). This is critical for correct
            # IDENT vs PRIMITIVE disambiguation at the TypeNode layer.
            return None
        if base == CodePrimitiveBaseType.json:
            if low.endswith("jsonarray"):
                return self._primitive(
                    base_type=base,
                    constraints=JsonObject({"json_kind": "array"}),
                )
            if low.endswith("jsonobject"):
                return self._primitive(
                    base_type=base,
                    constraints=JsonObject({"json_kind": "object"}),
                )
            if low.endswith("jsonvalue"):
                return self._primitive(
                    base_type=base,
                    constraints=JsonObject({"json_kind": "value"}),
                )
        return self._primitive(base_type=base)

    def is_literal(self, type_text: str) -> bool:
        return self._parser.get_literal_inner(type_text) is not None

    @override
    def parse(self, type_text: str) -> CodePrimitiveType | None:
        """
        Create a PythonPrimitiveType from a Python type annotation.
        """
        if not type_text:
            return None

        type_text = type_text.strip()

        # Handle Literal[...] -> string with constraints.one_of
        primitive_type = self.get_literal(type_text)
        if primitive_type is not None:
            return primitive_type

        # Handle Vector(…) parametric
        primitive_type = self.get_vector(type_text)
        if primitive_type is not None:
            return primitive_type

        # Handle Optional[T] (must run BEFORE generic Union processing)
        primitive_type = self.get_optional(type_text)
        if primitive_type is not None:
            return primitive_type

        # Handle ClassVar[T] - extract the inner type
        primitive_type = self.get_class_var(type_text)
        if primitive_type is not None:
            return primitive_type

        # Handle union types – "Union[a, b]"  or  "A | B"
        primitive_type = self.get_union(type_text)
        if primitive_type is not None:
            return primitive_type

        # Handle container / mapping types
        primitive_type = self.get_list(type_text)
        if primitive_type is not None:
            return primitive_type

        primitive_type = self.get_dict(type_text)
        if primitive_type is not None:
            return primitive_type

        return self.parse_exact(type_text.lower())

    def get_class_var(self, type_text: str) -> CodePrimitiveType | None:
        """
        Extract the inner type from a ClassVar[T] type string.
        """
        inner = self._parser.get_classvar_inner(type_text)
        if inner is not None:
            inner_type = self.parse(inner)
            if inner_type:
                return inner_type
            raise ValueError(f"Failed to parse inner type from ClassVar[{type_text}]")
        return None

    def get_optional(self, type_text: str) -> CodePrimitiveType | None:
        """
        Extract the inner type from an Optional[T] type string.
        """
        # !! TODO: DETECT ' T | None' syntax
        inner = self._parser.get_optional_inner(type_text)
        if inner is not None:
            inner_type = self.parse(inner)
            if inner_type:
                return self.make_nullable(inner_type)
            raise ValueError(f"Failed to parse inner type from Optional[{type_text}]")
        return None

    def get_vector(self, type_text: str) -> CodePrimitiveType | None:
        """
        Extract the inner type from a Vector(…) type string.
        """
        call = self._parser.get_call(type_text)
        if call is not None:
            name, args = call
            if name == "Vector":
                try:
                    dim = int(args.strip())
                    return self._primitive(
                        base_type=CodePrimitiveBaseType.vector,
                        constraints=JsonObject({"dimension": dim}),
                    )
                except Exception:
                    return self._primitive(base_type=CodePrimitiveBaseType.vector)
        if (type_text or "").strip().lower() == "vector":
            return self._primitive(base_type=CodePrimitiveBaseType.vector)
        return None

    def get_literal(self, type_text: str) -> CodePrimitiveType | None:
        """
        Extract the inner type from a Literal[...] type string.
        """
        raw = self._parser.get_literal_inner(type_text)
        if raw is not None:
            # Split top-level by commas, strip quotes
            # Note: this is a simple splitter; sufficient for string literal sets
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            values: list[str] = []
            for p in parts:
                if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                    values.append(p[1:-1])
                else:
                    values.append(p)
            one_of_values: list[object] = [value for value in values]
            constraints = JsonObject()
            constraints["one_of"] = one_of_values
            return self._primitive(
                base_type=CodePrimitiveBaseType.string,
                constraints=constraints,
            )
        return None

    def get_union(self, type_text: str) -> CodePrimitiveType | None:
        """
        Extract the inner types from a Union[T, ...] type string.
        """
        union_types = self._parser.get_union_members(type_text) or []
        if union_types:
            # Build PythonPrimitiveType objects for each component
            parsed_types: list[CodePrimitiveType] = []
            for t_str in union_types:
                parsed_t = self.parse(t_str)
                if parsed_t is None:
                    parsed_t = self.any()
                parsed_types.append(parsed_t)
            return self.union(*parsed_types)
        return None

    def get_list(self, type_text: str) -> CodePrimitiveType | None:
        """
        Extract the inner type from a List[T] type string.
        """
        inner = self._parser.get_list_inner(type_text)
        if inner is not None:
            inner_type = self.parse(inner)
            if inner_type:
                return self._primitive(base_type=CodePrimitiveBaseType.array, item_type=inner_type)
            raise ValueError(f"Failed to parse inner type from List[{type_text}]")
        return None

    def get_dict(self, type_text: str) -> CodePrimitiveType | None:
        """
        Extract the inner type from a Dict[K, V] type string.
        """
        kv = self._parser.get_dict_kv(type_text)
        if kv is not None:
            key_s, val_s = kv
            key_type = self.parse(key_s)
            value_type = self.parse(val_s)
            if key_type and value_type:
                return self._primitive(base_type=CodePrimitiveBaseType.dict, key_type=key_type, value_type=value_type)
            raise ValueError(f"Failed to parse key or value from Dict[{type_text}]")
        return None

    @override
    def enum_ident(self, type_text: str) -> str:
        """
        Normalize a Python type annotation to the canonical enum name identifier.

        Rules:
        - Optional[T] -> T
        - Union[T, None] or T | None -> T
        - List[T]/Sequence[T]/typing.List[T] -> T
        - Strip quotes for forward refs and return the last dotted component
        """
        if not type_text:
            return type_text

        text, _is_fwd = self._parser.strip_forward_ref_quotes(type_text)

        # Optional[T] -> T
        opt_inner = self._parser.get_optional_inner(text)
        if opt_inner is not None:
            text = opt_inner

        # Union[T, None] or T | None -> pick non-None (first non-None member)
        members = self._parser.get_union_members(text)
        if members:
            non_none = [m for m in members if m not in ("None", "NoneType", "null")]
            if non_none:
                text = non_none[0]

        # List/Sequence wrappers -> inner
        list_inner = self._parser.get_list_inner(text)
        if list_inner is not None:
            text = list_inner

        # Return last dotted component (e.g., module.CodeLanguage -> CodeLanguage)
        return (text or "").split(".")[-1]

    # NOTE: split_top_level moved to PythonTypeParser (raw token SSOT).

    @override
    def render(self, prim: CodePrimitiveType) -> str | None:
        """Convert this primitive type to Python type annotation syntax."""
        # Handle array types (list[T])
        if prim.base_type == CodePrimitiveBaseType.array and prim.item_type:
            item_type_str = self.render(prim.item_type)
            if item_type_str:
                base_type = f"list[{item_type_str}]"
            else:
                base_type = "list"
        # Handle vector types
        elif prim.base_type == CodePrimitiveBaseType.vector:
            dim = None
            if prim.constraints:
                dim = prim.constraints.get("dimension")
                if dim:
                    base_type = f"Annotated[Vector, VectorDim({dim})]"
            base_type = "Vector" if dim else "Vector"
        elif prim.base_type == CodePrimitiveBaseType.json:
            kind = None
            if prim.constraints:
                kind_val = prim.constraints.get("json_kind")
                if isinstance(kind_val, str):
                    kind = kind_val.lower()
            if kind == "array":
                base_type = "JsonArray"
            elif kind == "object":
                base_type = "JsonObject"
            elif kind == "value":
                base_type = "JsonValue"
            else:
                base_type = "Json"
        # Handle dictionary types (Dict[K, V])
        elif prim.base_type == CodePrimitiveBaseType.dict:
            # Use both key and value types if available
            if prim.key_type and prim.value_type:
                key_type_str = self.render(prim.key_type) or "Any"
                value_type_str = self.render(prim.value_type) or "Any"
                base_type = f"dict[{key_type_str}, {value_type_str}]"
            else:
                base_type = "dict[str, Any]"
        # Handle union types
        elif prim.base_type == CodePrimitiveBaseType.union and prim.union_types:
            # Check if this is an optional type (union with null)
            null_types = [t for t in prim.union_types if t.base_type == CodePrimitiveBaseType.null]
            non_null_types = [t for t in prim.union_types if t.base_type != CodePrimitiveBaseType.null]

            if len(null_types) == 1 and len(non_null_types) == 1:
                # This is Optional[T] case
                inner_type_str = self.render(non_null_types[0]) or "Any"
                base_type = f"Optional[{inner_type_str}]"
            elif len(null_types) > 0 and len(non_null_types) == 1:
                # Multiple nulls with one non-null, still Optional
                inner_type_str = self.render(non_null_types[0]) or "Any"
                base_type = f"Optional[{inner_type_str}]"
            else:
                # Regular union
                type_strs = [self.render(t) or "Any" for t in prim.union_types]
                base_type = f"Union[{', '.join(type_strs)}]"
        else:
            # Get from Python type mapping
            python_type = PYTHON_TYPE_MAPPING.get(prim.base_type)
            if python_type:
                base_type = python_type
            else:
                base_type = "Any"

        # Wrap in ClassVar if this was originally a ClassVar
        # !!! TODO: CLARIFY !!
        if self.is_classvar:
            return f"ClassVar[{base_type}]"

        return base_type

    @override
    def is_void(self, type_text: str) -> bool:
        """Check if a Python type is void (None)."""
        return type_text.lower() in ["none", "null", "void"]

    @override
    def is_list(self, type_text: str) -> bool:
        """
        Check if a Python type string represents a list/array/collection.

        Detects patterns like:
        - List[Type]
        - list[Type]
        - typing.List[Type]
        - Sequence[Type]
        - MutableSequence[Type]

        Args:
            type_str: The Python type string to check

        Returns:
            True if the type represents a list/array/collection, False otherwise
        """
        if not type_text:
            return False
        s = type_text.strip()

        if self._parser.get_list_inner(s) is not None:
            return True

        opt_inner = self._parser.get_optional_inner(s)
        if opt_inner is not None:
            return self.is_list(opt_inner)

        union_members = self._parser.get_union_members(s)
        if union_members:
            return any(self.is_list(m) for m in union_members)

        return False

    @override
    def is_set(self, type_text: str) -> bool:
        """
        Check if a Python type string represents a set/collection.
        """
        if not type_text:
            return False
        s = type_text.strip()
        if self._parser.get_set_inner(s) is not None:
            return True
        opt_inner = self._parser.get_optional_inner(s)
        if opt_inner is not None:
            return self.is_set(opt_inner)
        union_members = self._parser.get_union_members(s)
        if union_members:
            return any(self.is_set(m) for m in union_members)
        return False

    def get_collection_type(self, type_text: str) -> CollectionKind | None:
        """
        Get the collection type from a Python type string.

        Returns:
            - CollectionKind.SET for Set[T], set[T], typing.Set[T]
            - CollectionKind.LIST for List[T], list[T], Sequence[T], etc.
            - None for non-collection types
        """

        if not type_text:
            return None
        s = type_text.strip()

        if self._parser.get_set_inner(s) is not None:
            return CollectionKind.SET
        if self._parser.get_list_inner(s) is not None:
            return CollectionKind.LIST

        opt_inner = self._parser.get_optional_inner(s)
        if opt_inner is not None:
            return self.get_collection_type(opt_inner)

        union_members = self._parser.get_union_members(s)
        if union_members:
            for m in union_members:
                k = self.get_collection_type(m)
                if k is not None:
                    return k

        return None

    @override
    def get_inner_type(self, type_text: str) -> str:
        """
        Extract the inner type from a Python list/array/collection type string.

        Examples:
        - List[str] -> str
        - list[int] -> int
        - typing.List[User] -> User
        - Sequence[MyType] -> MyType
        - str[] -> str
        - Optional[List[str]] -> Optional[str]

        Args:
            type_str: The Python type string to extract from

        Returns:
            The inner type string, or the original string if not a list type
        """
        if not type_text:
            return type_text

        original = type_text
        s = type_text.strip()

        # Optional[List[T]] -> Optional[T]
        opt_inner = self._parser.get_optional_inner(s)
        if opt_inner is not None:
            # Only unwrap if the inner is actually a collection
            if self.is_list(opt_inner) or self.is_set(opt_inner):
                inner = self.get_inner_type(opt_inner)
                return f"Optional[{inner}]"
            return original

        # Direct list/set wrappers
        list_inner = self._parser.get_list_inner(s)
        if list_inner is not None:
            return list_inner
        set_inner = self._parser.get_set_inner(s)
        if set_inner is not None:
            return set_inner

        # Union containing a collection: unwrap the first collection member and rebuild
        union_members = self._parser.get_union_members(s)
        if union_members:
            for mem in union_members:
                if self.is_list(mem) or self.is_set(mem):
                    inner = self.get_inner_type(mem)
                    non_list = [m for m in union_members if not (self.is_list(m) or self.is_set(m))]
                    if self._parser.is_union_bracket_syntax(s):
                        return f"Union[{', '.join(non_list + [inner])}]" if non_list else inner
                    return " | ".join(non_list + [inner]) if non_list else inner

        # Not a collection type
        return original

    # ------------------------------------------------------------------
    # Literal parsing helpers
    # ------------------------------------------------------------------

    @override
    def parse_literal(self, literal: str) -> object | None:
        """Parse a raw Python literal (as captured from source) into a runtime value.

        This is used when translating default values from code into the
        language-agnostic meta-model. Where possible we rely on
        ``ast.literal_eval`` to safely evaluate the literal, falling back to
        simple heuristics when evaluation fails (e.g., for factory
        expressions or complex call expressions).
        """
        lit = literal.strip()

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
                return list(cast(set[object], value))
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
    def to_literal_string(self, value: object, raw_code: bool = False) -> str:
        """Convert a Python value to a Python literal string.

        Args:
            value: The value to convert
            raw_code: If True, string values are treated as raw Python code for ClassVar fields

        Examples:
            True -> "True"
            "hello" -> "'hello'"
            123 -> "123"
            {"a": 1} -> "{'a': 1}"
        """
        if value is None:
            return "None"
        elif isinstance(value, bool):
            return str(value)  # Returns "True" or "False"
        elif isinstance(value, str):
            return repr(value)
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, tuple, dict, set)):
            # Use repr for collections which gives proper Python syntax
            return repr(cast(object, value))
        else:
            # For any other type, use repr as fallback
            return repr(value)
