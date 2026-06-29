"""SQL-specific primitive type implementation"""

import re
import json

from typing_extensions import override

from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

from aware_code.primitive_codec_base import CodePrimitiveCodecBase
from aware_code.type_descriptor_nodes import CollectionKind
from aware_code.types.json import Json

from sql_grammar.type_parser import SqlTypeParser

# Common type node types
PRIMITIVE_TYPE_NODES = [
    # Keywords
    "keyword_boolean",
    "keyword_bytea",
    "keyword_jsonb",
    "keyword_real",
    "keyword_text",
    "keyword_timestamptz",
    "keyword_uuid",
    # Types
    "bigint",
    "decimal",
    "double",
    "float",
    "int",
    "numeric",
    "timestamp",
    "vector",
    # Custom types
    "object_reference",
]

# SQL type mappings
SQL_TYPE_MAPPING: dict[CodePrimitiveBaseType, str] = {
    CodePrimitiveBaseType.any: "TEXT",
    CodePrimitiveBaseType.boolean: "BOOLEAN",
    CodePrimitiveBaseType.bytes: "BYTEA",
    CodePrimitiveBaseType.datetime: "TIMESTAMP WITH TIME ZONE",
    CodePrimitiveBaseType.integer: "INTEGER",
    CodePrimitiveBaseType.float: "NUMERIC",
    CodePrimitiveBaseType.json: "JSONB",
    CodePrimitiveBaseType.null: "NULL",
    CodePrimitiveBaseType.string: "TEXT",
    CodePrimitiveBaseType.uuid: "UUID",
    CodePrimitiveBaseType.vector: "VECTOR",
}


class SqlPrimitiveCodec(CodePrimitiveCodecBase):
    """
    SQL-specific primitive type implementation.

    Extends the core CodePrimitiveType with SQL-specific functionality.
    """

    def __init__(self, parser: SqlTypeParser | None = None):
        self._parser = parser or SqlTypeParser()

    _parser: SqlTypeParser

    @override
    def enum_ident(self, type_text: str) -> str:
        """
        Normalize a SQL enum type name for matching against EnumConfig.name.

        - Strip schema qualification (schema.type -> type)
        - Return the base identifier (keep underscores; callers will apply casing)
        """
        if not type_text:
            return type_text
        txt = type_text.strip()
        # Remove surrounding quotes if any
        if txt.startswith('"') and txt.endswith('"'):
            txt = txt[1:-1]
        # Strip schema prefix (schema.type -> type)
        if "." in txt:
            txt = txt.split(".")[-1]
        return txt

    @override
    def parse_exact(self, type_text: str) -> CodePrimitiveType | None:
        """Exact type text mapping to primitive types (no substring heuristics).

        Use only when the caller has already ruled out arrays/vector(dim)/schema-qualified types.
        """
        t = self._parser.normalize_exact_token(type_text)
        if not t:
            return None

        # Canonical exact tokens and phrases
        INTEGER = CodePrimitiveBaseType.integer
        FLOAT = CodePrimitiveBaseType.float
        STRING = CodePrimitiveBaseType.string
        DATETIME = CodePrimitiveBaseType.datetime
        BOOLEAN = CodePrimitiveBaseType.boolean
        UUID = CodePrimitiveBaseType.uuid
        JSON = CodePrimitiveBaseType.json
        BYTES = CodePrimitiveBaseType.bytes
        VECTOR = CodePrimitiveBaseType.vector

        exact_map: dict[str, CodePrimitiveBaseType] = {
            # booleans
            "bool": BOOLEAN,
            "boolean": BOOLEAN,
            # bytes
            "bytea": BYTES,
            # json
            "json": JSON,
            "jsonb": JSON,
            # uuid
            "uuid": UUID,
            # strings
            "text": STRING,
            "varchar": STRING,
            "char": STRING,
            "character": STRING,
            "character varying": STRING,
            # datetime / date / time
            "timestamp": DATETIME,
            "timestamp with time zone": DATETIME,
            "timestamp without time zone": DATETIME,
            "timestamptz": DATETIME,
            "date": DATETIME,
            "time": DATETIME,
            # numeric / floats
            "real": FLOAT,
            "double precision": FLOAT,
            "float": FLOAT,
            "numeric": FLOAT,
            "decimal": FLOAT,
            # integers
            "int": INTEGER,
            "integer": INTEGER,
            "smallint": INTEGER,
            "bigint": INTEGER,
            "int2": INTEGER,
            "int4": INTEGER,
            "int8": INTEGER,
            "serial": INTEGER,
            "bigserial": INTEGER,
            "smallserial": INTEGER,
            # vector (dimension-less token)
            "vector": VECTOR,
        }

        base = exact_map.get(t)
        if base is None:
            return None
        return self._primitive(base_type=base)

    @override
    def parse(self, type_text: str) -> CodePrimitiveType | None:
        """
        Create a SQLPrimitiveType from a SQL type string.

        Args:
            sql_type: SQL type definition (e.g., "INTEGER", "TEXT[]")

        Returns:
            SQLPrimitiveType instance representing the SQL type
        """
        if not type_text:
            return None

        raw = type_text.strip()

        # Arrays (all supported syntaxes)
        inner = self._parser.get_array_inner(raw)
        if inner is not None:
            item_type = self.parse(inner)
            return self._primitive(base_type=CodePrimitiveBaseType.array, item_type=item_type)

        # Parametric calls (VECTOR(dim), VARCHAR(255), NUMERIC(...), etc.)
        call = self._parser.get_call(raw)
        if call is not None:
            name, args = call
            if name.strip().lower() == "vector":
                m = re.match(r"^\s*(\d+)\s*$", args)
                if m:
                    dimension = int(m.group(1))
                    return self._primitive(
                        base_type=CodePrimitiveBaseType.vector, constraints=Json({"dimension": dimension})
                    )
                return self._primitive(base_type=CodePrimitiveBaseType.vector)
            # For other parameterized types, treat as the base token (e.g., varchar(255) -> varchar)
            exact = self.parse_exact(name)
            if exact is not None:
                return exact

        # Prefer exact token mapping to avoid substring collisions
        exact = self.parse_exact(raw)
        if exact is not None:
            return exact
        return None

    @override
    def render(self, prim: CodePrimitiveType) -> str | None:
        """Convert this primitive type to SQL type syntax."""
        # Handle array types
        if prim.base_type == CodePrimitiveBaseType.array and prim.item_type:
            return f"{self.render(prim.item_type)}[]"

        # Handle dictionary types (as JSONB in SQL)
        if prim.base_type == CodePrimitiveBaseType.dict:
            return "JSONB"

        # Handle vector types
        if prim.base_type == CodePrimitiveBaseType.vector:
            if prim.constraints:
                dim = prim.constraints.get("dimension", 1536)
                if dim:
                    return f"VECTOR({dim})"
            return "VECTOR"

        # Get from SQL type mapping
        return SQL_TYPE_MAPPING.get(prim.base_type, None)

    def get_sql_constraints(self, prim: CodePrimitiveType) -> str | None:
        """
        Generate SQL constraints based on type constraints.

        Args:
            type_info: The primitive type info with constraints

        Returns:
            SQL constraint clause or None if no constraints
        """
        if not prim.constraints:
            return None

        constraints_obj = prim.constraints

        constraints: list[str] = []

        # Handle string constraints
        if prim.base_type == CodePrimitiveBaseType.string:
            min_length = constraints_obj.get("min_length")
            if min_length is not None:
                constraints.append(f"LENGTH(value) >= {min_length}")
            max_length = constraints_obj.get("max_length")
            if max_length is not None:
                constraints.append(f"LENGTH(value) <= {max_length}")
            pattern = constraints_obj.get("pattern")
            if pattern is not None:
                constraints.append(f"value ~ '{pattern}'")

        # Handle numeric constraints
        elif prim.base_type in [CodePrimitiveBaseType.integer, CodePrimitiveBaseType.float]:
            minimum = constraints_obj.get("minimum")
            if minimum is not None:
                constraints.append(f"value >= {minimum}")
            maximum = constraints_obj.get("maximum")
            if maximum is not None:
                constraints.append(f"value <= {maximum}")

        if constraints:
            return " AND ".join(constraints)
        return None

    @override
    def is_void(self, type_text: str) -> bool:
        """Check if a SQL type is void."""
        return type_text.lower() in ["void", "none"]

    @override
    def is_list(self, type_text: str) -> bool:
        """
        Check if a SQL type string represents a list/array/collection.

        Detects patterns like:
        - INTEGER[]
        - TEXT[]
        - VARCHAR(255)[]
        - ARRAY<INTEGER>
        - ARRAY[INTEGER]

        Args:
            type_text: The SQL type string to check

        Returns:
            True if the type represents a list/array/collection, False otherwise
        """
        if not type_text:
            return False

        type_text = type_text.strip().lower()

        # Check for array bracket notation (most common in SQL)
        if type_text.endswith("[]"):
            return True

        # Check for ARRAY<TYPE> notation
        if type_text.startswith("array<") and type_text.endswith(">"):
            return True

        # Check for ARRAY[TYPE] notation
        if type_text.startswith("array[") and type_text.endswith("]"):
            return True

        # Check for explicit ARRAY type (PostgreSQL style)
        if type_text.startswith("array(") and type_text.endswith(")"):
            return True

        return False

    @override
    def is_set(self, type_text: str) -> bool:
        """SQL has arrays but no native set type syntax."""
        return False

    def get_collection_type(self, type_text: str) -> CollectionKind | None:
        """
        Get the collection type from a SQL type string.

        SQL doesn't have native Set types, only arrays.
        Returns:
            - CollectionType.LIST for array types (INTEGER[], ARRAY<TYPE>, etc.)
            - CollectionType.SINGLE for non-collection types
        """

        if self.is_list(type_text):
            return CollectionKind.LIST
        return None

    @override
    def get_inner_type(self, type_text: str) -> str:
        """
        Extract the inner type from a SQL list/array/collection type string.

        Examples:
        - INTEGER[] -> INTEGER
        - TEXT[] -> TEXT
        - VARCHAR(255)[] -> VARCHAR(255)
        - ARRAY<INTEGER> -> INTEGER
        - ARRAY[TEXT] -> TEXT
        - ARRAY(BOOLEAN) -> BOOLEAN

        Args:
            type_text: The SQL type string to extract from

        Returns:
            The inner type string, or the original string if not a list type
        """
        if not type_text:
            return type_text

        original_type_text = type_text  # Keep original casing and content
        type_text_lower = type_text.strip().lower()

        # Handle array bracket notation (TYPE[] -> TYPE)
        if type_text_lower.endswith("[]"):
            return original_type_text[:-2].strip()

        # Handle ARRAY<TYPE> notation
        if type_text_lower.startswith("array<") and type_text_lower.endswith(">"):
            start_pos = len("array<")
            end_pos = len(original_type_text) - 1  # Remove >
            return original_type_text[start_pos:end_pos].strip()

        # Handle ARRAY[TYPE] notation
        if type_text_lower.startswith("array[") and type_text_lower.endswith("]"):
            start_pos = len("array[")
            end_pos = len(original_type_text) - 1  # Remove ]
            return original_type_text[start_pos:end_pos].strip()

        # Handle ARRAY(TYPE) notation
        if type_text_lower.startswith("array(") and type_text_lower.endswith(")"):
            start_pos = len("array(")
            end_pos = len(original_type_text) - 1  # Remove )
            return original_type_text[start_pos:end_pos].strip()

        # If we get here, it's not a recognized list type - return original unchanged
        return original_type_text

    # ------------------------------------------------------------------
    # Literal parsing helpers
    # ------------------------------------------------------------------

    @override
    def parse_literal(self, literal: str) -> object:
        """Parse a SQL literal into a SQL value.

        This implementation is intentionally conservative – it handles the
        most common literal forms that appear in DDL statements or column
        defaults. Complex expressions return the raw string so that higher
        layers can decide how to deal with them.
        """

        lit = literal.strip()

        low = lit.lower()

        # NULL / NONE handling
        if low in {"null", "none"}:
            return None

        # Boolean literals – SQL is case-insensitive
        if low in {"true", "false"}:
            return low == "true"

        # Remove quotes for quoted strings
        if (lit.startswith("'") and lit.endswith("'")) or (lit.startswith('"') and lit.endswith('"')):
            return lit[1:-1]

        # Numeric literals – try int then float
        try:
            return int(lit)
        except ValueError:
            try:
                return float(lit)
            except ValueError:
                pass

        # Fallback – return raw literal text
        return lit

    @override
    def to_literal_string(self, value: object) -> str:
        """Convert a Python value to an SQL literal string.

        Examples:
            True -> "TRUE"
            "hello" -> "'hello'"
            123 -> "123"
            {"a": 1} -> "'{\"a\": 1}'"
        """
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, str):
            # SQL uses single quotes, escape any internal single quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, tuple, dict)):
            # For complex structures, serialize to JSON and quote
            json_str = json.dumps(value)
            return f"'{json_str}'"
        else:
            # Convert to string and quote for safety
            return f"'{str(value)}'"
