"""Tests for SQL primitive type detection and functionality."""

# Primitive types
from sql_grammar.primitive_codec import SqlPrimitiveCodec

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

from aware_code.types import Json


def from_string_or_raise(primitive_codec: SqlPrimitiveCodec, type_text: str) -> CodePrimitiveType:
    primitive = primitive_codec.parse(type_text)
    if not primitive:
        raise ValueError(f"Failed to parse primitive type: {type_text}")
    return primitive


def test_basic_primitive_type_detection():
    """Test that SQL primitive types are correctly detected."""
    primitive_codec = SqlPrimitiveCodec()
    # Test basic primitive types
    assert from_string_or_raise(primitive_codec, "TEXT").base_type == CodePrimitiveBaseType.string
    assert from_string_or_raise(primitive_codec, "VARCHAR").base_type == CodePrimitiveBaseType.string
    assert from_string_or_raise(primitive_codec, "INTEGER").base_type == CodePrimitiveBaseType.integer
    assert from_string_or_raise(primitive_codec, "INT").base_type == CodePrimitiveBaseType.integer
    assert from_string_or_raise(primitive_codec, "BOOLEAN").base_type == CodePrimitiveBaseType.boolean
    assert from_string_or_raise(primitive_codec, "BOOL").base_type == CodePrimitiveBaseType.boolean
    assert from_string_or_raise(primitive_codec, "FLOAT").base_type == CodePrimitiveBaseType.float
    assert from_string_or_raise(primitive_codec, "DECIMAL").base_type == CodePrimitiveBaseType.float
    assert from_string_or_raise(primitive_codec, "NUMERIC").base_type == CodePrimitiveBaseType.float
    assert from_string_or_raise(primitive_codec, "BYTEA").base_type == CodePrimitiveBaseType.bytes
    assert from_string_or_raise(primitive_codec, "TIMESTAMP").base_type == CodePrimitiveBaseType.datetime
    assert from_string_or_raise(primitive_codec, "UUID").base_type == CodePrimitiveBaseType.uuid
    assert from_string_or_raise(primitive_codec, "JSONB").base_type == CodePrimitiveBaseType.json
    assert from_string_or_raise(primitive_codec, "JSON").base_type == CodePrimitiveBaseType.json
    assert from_string_or_raise(primitive_codec, "VECTOR").base_type == CodePrimitiveBaseType.vector

    # Test case insensitive
    assert from_string_or_raise(primitive_codec, "text").base_type == CodePrimitiveBaseType.string
    assert from_string_or_raise(primitive_codec, "integer").base_type == CodePrimitiveBaseType.integer
    assert from_string_or_raise(primitive_codec, "boolean").base_type == CodePrimitiveBaseType.boolean


def test_array_types():
    """Test SQL array types."""
    primitive_codec = SqlPrimitiveCodec()
    # Test basic array
    text_array = from_string_or_raise(primitive_codec, "TEXT[]")
    assert text_array.base_type == CodePrimitiveBaseType.array
    assert text_array.item_type is not None
    assert text_array.item_type.base_type == CodePrimitiveBaseType.string
    assert primitive_codec.render(text_array) == "TEXT[]"

    # Test integer array
    int_array = from_string_or_raise(primitive_codec, "INTEGER[]")
    assert int_array.base_type == CodePrimitiveBaseType.array
    assert int_array.item_type is not None
    assert int_array.item_type.base_type == CodePrimitiveBaseType.integer
    assert primitive_codec.render(int_array) == "INTEGER[]"

    # Test case insensitive arrays
    bool_array = from_string_or_raise(primitive_codec, "boolean[]")
    assert bool_array.base_type == CodePrimitiveBaseType.array
    assert bool_array.item_type is not None
    assert bool_array.item_type.base_type == CodePrimitiveBaseType.boolean

    # Nested arrays
    nested = from_string_or_raise(primitive_codec, "TEXT[][]")
    assert nested.base_type == CodePrimitiveBaseType.array
    assert nested.item_type is not None and nested.item_type.base_type == CodePrimitiveBaseType.array
    assert primitive_codec.render(nested) == "TEXT[][]"

    # ARRAY<T> / ARRAY[T] / ARRAY(T) syntaxes
    arr_angle = from_string_or_raise(primitive_codec, "ARRAY<TEXT>")
    assert arr_angle.base_type == CodePrimitiveBaseType.array
    assert arr_angle.item_type is not None and arr_angle.item_type.base_type == CodePrimitiveBaseType.string

    arr_sq = from_string_or_raise(primitive_codec, "ARRAY[INTEGER]")
    assert arr_sq.base_type == CodePrimitiveBaseType.array
    assert arr_sq.item_type is not None and arr_sq.item_type.base_type == CodePrimitiveBaseType.integer

    arr_paren = from_string_or_raise(primitive_codec, "ARRAY(BOOLEAN)")
    assert arr_paren.base_type == CodePrimitiveBaseType.array
    assert arr_paren.item_type is not None and arr_paren.item_type.base_type == CodePrimitiveBaseType.boolean


def test_vector_types():
    """Test SQL vector types with dimensions."""
    primitive_codec = SqlPrimitiveCodec()
    # Test basic vector without parameters
    vector = from_string_or_raise(primitive_codec, "VECTOR")
    assert vector.base_type == CodePrimitiveBaseType.vector
    assert vector.constraints is None
    assert primitive_codec.render(vector) == "VECTOR"

    # Test vector with dimension
    vector_512 = from_string_or_raise(primitive_codec, "VECTOR(512)")
    assert vector_512.base_type == CodePrimitiveBaseType.vector
    assert vector_512.constraints == {"dimension": 512}
    assert primitive_codec.render(vector_512) == "VECTOR(512)"

    # Test vector with different dimension
    vector_1536 = from_string_or_raise(primitive_codec, "VECTOR(1536)")
    assert vector_1536.base_type == CodePrimitiveBaseType.vector
    assert vector_1536.constraints == {"dimension": 1536}
    assert primitive_codec.render(vector_1536) == "VECTOR(1536)"

    # Test case insensitive
    vector_lower = from_string_or_raise(primitive_codec, "vector(256)")
    assert vector_lower.base_type == CodePrimitiveBaseType.vector
    assert vector_lower.constraints == {"dimension": 256}

    # Vector inside array wrappers
    vec_arr = from_string_or_raise(primitive_codec, "VECTOR(512)[]")
    assert vec_arr.base_type == CodePrimitiveBaseType.array
    assert vec_arr.item_type is not None and vec_arr.item_type.base_type == CodePrimitiveBaseType.vector
    assert vec_arr.item_type.constraints == {"dimension": 512}

    vec_arr2 = from_string_or_raise(primitive_codec, "ARRAY(VECTOR(512))")
    assert vec_arr2.base_type == CodePrimitiveBaseType.array
    assert vec_arr2.item_type is not None and vec_arr2.item_type.base_type == CodePrimitiveBaseType.vector
    assert vec_arr2.item_type.constraints == {"dimension": 512}


def test_void_type_detection():
    """Test void type detection."""
    primitive_codec = SqlPrimitiveCodec()
    assert primitive_codec.is_void("VOID") is True
    assert primitive_codec.is_void("void") is True
    assert primitive_codec.is_void("NONE") is True
    assert primitive_codec.is_void("none") is True
    assert primitive_codec.is_void("TEXT") is False
    assert primitive_codec.is_void("INTEGER") is False


def test_to_string_conversion():
    """Test conversion from primitive types back to SQL syntax."""
    # Test basic types
    primitive_codec = SqlPrimitiveCodec()
    text_type = build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    assert primitive_codec.render(text_type) == "TEXT"

    int_type = build_code_primitive_type(base_type=CodePrimitiveBaseType.integer)
    assert primitive_codec.render(int_type) == "INTEGER"

    bool_type = build_code_primitive_type(base_type=CodePrimitiveBaseType.boolean)
    assert primitive_codec.render(bool_type) == "BOOLEAN"

    # Test array types
    array_type = build_code_primitive_type(
        base_type=CodePrimitiveBaseType.array,
        item_type=build_code_primitive_type(base_type=CodePrimitiveBaseType.string),
    )
    assert primitive_codec.render(array_type) == "TEXT[]"

    # Test vector with constraints
    vector_type = build_code_primitive_type(
        base_type=CodePrimitiveBaseType.vector,
        constraints=Json({"dimension": 1024}),
    )
    assert primitive_codec.render(vector_type) == "VECTOR(1024)"

    # Test dictionary type (maps to JSONB)
    dict_type = build_code_primitive_type(base_type=CodePrimitiveBaseType.dict)
    assert primitive_codec.render(dict_type) == "JSONB"

    # Parameterized string types should normalize to TEXT (via mapping)
    assert from_string_or_raise(primitive_codec, "VARCHAR(255)").base_type == CodePrimitiveBaseType.string
    assert from_string_or_raise(primitive_codec, "CHAR(10)").base_type == CodePrimitiveBaseType.string
    assert from_string_or_raise(primitive_codec, "DOUBLE PRECISION").base_type == CodePrimitiveBaseType.float


def test_exact_token_disambiguation_does_not_use_substrings():
    """Ensure we don't misclassify enum-ish identifiers due to substrings like 'int' or 'uuid'."""
    primitive_codec = SqlPrimitiveCodec()
    assert primitive_codec.parse_exact("interface_os") is None
    assert primitive_codec.parse("interface_os") is None
    assert primitive_codec.parse_exact("transaction_intent_status") is None
    assert primitive_codec.parse("transaction_intent_status") is None


def test_literal_parsing():
    """Test parsing of SQL literals."""
    # Test boolean literals
    primitive_codec = SqlPrimitiveCodec()
    assert primitive_codec.parse_literal("TRUE") is True
    assert primitive_codec.parse_literal("true") is True
    assert primitive_codec.parse_literal("FALSE") is False
    assert primitive_codec.parse_literal("false") is False

    # Test null literal
    assert primitive_codec.parse_literal("NULL") is None
    assert primitive_codec.parse_literal("null") is None
    assert primitive_codec.parse_literal("NONE") is None

    # Test string literals
    assert primitive_codec.parse_literal("'hello'") == "hello"
    assert primitive_codec.parse_literal("'world'") == "world"
    assert primitive_codec.parse_literal('"test"') == "test"

    # Test number literals
    assert primitive_codec.parse_literal("42") == 42
    assert primitive_codec.parse_literal("3.14") == 3.14
    assert primitive_codec.parse_literal("-123") == -123


def test_to_literal_string():
    """Test conversion of Python values to SQL literal strings."""
    primitive_codec = SqlPrimitiveCodec()
    # Test basic types
    assert primitive_codec.to_literal_string(None) == "NULL"
    assert primitive_codec.to_literal_string(True) == "TRUE"
    assert primitive_codec.to_literal_string(False) == "FALSE"
    assert primitive_codec.to_literal_string("hello") == "'hello'"
    assert primitive_codec.to_literal_string(42) == "42"
    assert primitive_codec.to_literal_string(3.14) == "3.14"

    # Test string escaping
    assert primitive_codec.to_literal_string("can't") == "'can''t'"

    # Test complex types (converted to JSON strings)
    assert primitive_codec.to_literal_string([1, 2, 3]) == "'[1, 2, 3]'"
    assert primitive_codec.to_literal_string({"key": "value"}) == '\'{"key": "value"}\''


def test_is_list_detection():
    """Test the is_list method for SQL types."""
    # Test basic array types
    primitive_codec = SqlPrimitiveCodec()
    assert primitive_codec.is_list("INTEGER[]") is True
    assert primitive_codec.is_list("TEXT[]") is True
    assert primitive_codec.is_list("BOOLEAN[]") is True
    assert primitive_codec.is_list("VARCHAR(255)[]") is True
    assert primitive_codec.is_list("TIMESTAMP[]") is True

    # Test case insensitive
    assert primitive_codec.is_list("integer[]") is True
    assert primitive_codec.is_list("text[]") is True
    assert primitive_codec.is_list("boolean[]") is True

    # Test ARRAY<TYPE> notation
    assert primitive_codec.is_list("ARRAY<INTEGER>") is True
    assert primitive_codec.is_list("ARRAY<TEXT>") is True
    assert primitive_codec.is_list("array<boolean>") is True

    # Test ARRAY[TYPE] notation
    assert primitive_codec.is_list("ARRAY[INTEGER]") is True
    assert primitive_codec.is_list("ARRAY[TEXT]") is True
    assert primitive_codec.is_list("array[varchar]") is True

    # Test ARRAY(TYPE) notation
    assert primitive_codec.is_list("ARRAY(INTEGER)") is True
    assert primitive_codec.is_list("ARRAY(TEXT)") is True
    assert primitive_codec.is_list("array(boolean)") is True

    # Test vector arrays
    assert primitive_codec.is_list("VECTOR[]") is True
    assert primitive_codec.is_list("VECTOR(512)[]") is True

    # Test non-list types
    assert primitive_codec.is_list("INTEGER") is False
    assert primitive_codec.is_list("TEXT") is False
    assert primitive_codec.is_list("BOOLEAN") is False
    assert primitive_codec.is_list("VARCHAR(255)") is False
    assert primitive_codec.is_list("VECTOR") is False
    assert primitive_codec.is_list("VECTOR(1536)") is False
    assert primitive_codec.is_list("TIMESTAMP") is False

    # Test edge cases
    assert primitive_codec.is_list("") is False
    assert primitive_codec.is_list("   ") is False


def test_get_inner_type_extraction():
    """Test the get_inner_type method for SQL types."""
    primitive_codec = SqlPrimitiveCodec()
    # Test basic array types
    assert primitive_codec.get_inner_type("INTEGER[]") == "INTEGER"
    assert primitive_codec.get_inner_type("TEXT[]") == "TEXT"
    assert primitive_codec.get_inner_type("BOOLEAN[]") == "BOOLEAN"
    assert primitive_codec.get_inner_type("VARCHAR(255)[]") == "VARCHAR(255)"
    assert primitive_codec.get_inner_type("TIMESTAMP[]") == "TIMESTAMP"

    # Test case insensitive (preserves original casing)
    assert primitive_codec.get_inner_type("integer[]") == "integer"
    assert primitive_codec.get_inner_type("text[]") == "text"
    assert primitive_codec.get_inner_type("Boolean[]") == "Boolean"

    # Test ARRAY<TYPE> notation
    assert primitive_codec.get_inner_type("ARRAY<INTEGER>") == "INTEGER"
    assert primitive_codec.get_inner_type("ARRAY<TEXT>") == "TEXT"
    assert primitive_codec.get_inner_type("array<boolean>") == "boolean"
    assert primitive_codec.get_inner_type("ARRAY<VARCHAR(100)>") == "VARCHAR(100)"

    # Test ARRAY[TYPE] notation
    assert primitive_codec.get_inner_type("ARRAY[INTEGER]") == "INTEGER"
    assert primitive_codec.get_inner_type("ARRAY[TEXT]") == "TEXT"
    assert primitive_codec.get_inner_type("array[varchar]") == "varchar"
    assert primitive_codec.get_inner_type("ARRAY[TIMESTAMP WITH TIME ZONE]") == "TIMESTAMP WITH TIME ZONE"

    # Test ARRAY(TYPE) notation
    assert primitive_codec.get_inner_type("ARRAY(INTEGER)") == "INTEGER"
    assert primitive_codec.get_inner_type("ARRAY(TEXT)") == "TEXT"
    assert primitive_codec.get_inner_type("array(boolean)") == "boolean"

    # Test vector arrays
    assert primitive_codec.get_inner_type("VECTOR[]") == "VECTOR"
    assert primitive_codec.get_inner_type("VECTOR(512)[]") == "VECTOR(512)"
    assert primitive_codec.get_inner_type("vector(1024)[]") == "vector(1024)"

    # Test complex types with parameters
    assert primitive_codec.get_inner_type("DECIMAL(10,2)[]") == "DECIMAL(10,2)"
    assert primitive_codec.get_inner_type("NUMERIC(precision, scale)[]") == "NUMERIC(precision, scale)"

    # Test non-list types (should return unchanged)
    assert primitive_codec.get_inner_type("INTEGER") == "INTEGER"
    assert primitive_codec.get_inner_type("TEXT") == "TEXT"
    assert primitive_codec.get_inner_type("BOOLEAN") == "BOOLEAN"
    assert primitive_codec.get_inner_type("VARCHAR(255)") == "VARCHAR(255)"
    assert primitive_codec.get_inner_type("VECTOR") == "VECTOR"
    assert primitive_codec.get_inner_type("VECTOR(1536)") == "VECTOR(1536)"
    assert primitive_codec.get_inner_type("TIMESTAMP") == "TIMESTAMP"

    # Test edge cases
    assert primitive_codec.get_inner_type("") == ""
    assert primitive_codec.get_inner_type("   ") == "   "


def test_is_list_and_get_inner_type_consistency():
    """Test that is_list and get_inner_type work consistently together."""
    primitive_codec = SqlPrimitiveCodec()
    test_cases = [
        # (type_string, is_list_expected, inner_type_expected)
        ("INTEGER[]", True, "INTEGER"),
        ("TEXT[]", True, "TEXT"),
        ("BOOLEAN[]", True, "BOOLEAN"),
        ("VARCHAR(255)[]", True, "VARCHAR(255)"),
        ("VECTOR[]", True, "VECTOR"),
        ("VECTOR(512)[]", True, "VECTOR(512)"),
        ("ARRAY<INTEGER>", True, "INTEGER"),
        ("ARRAY[TEXT]", True, "TEXT"),
        ("ARRAY(BOOLEAN)", True, "BOOLEAN"),
        ("integer[]", True, "integer"),
        ("array<text>", True, "text"),
        ("INTEGER", False, "INTEGER"),
        ("TEXT", False, "TEXT"),
        ("BOOLEAN", False, "BOOLEAN"),
        ("VARCHAR(255)", False, "VARCHAR(255)"),
        ("VECTOR", False, "VECTOR"),
        ("VECTOR(1536)", False, "VECTOR(1536)"),
        ("TIMESTAMP", False, "TIMESTAMP"),
    ]

    for type_str, expected_is_list, expected_inner_type in test_cases:
        actual_is_list = primitive_codec.is_list(type_str)
        actual_inner_type = primitive_codec.get_inner_type(type_str)

        assert (
            actual_is_list == expected_is_list
        ), f"is_list({type_str}) expected {expected_is_list}, got {actual_is_list}"
        assert (
            actual_inner_type == expected_inner_type
        ), f"get_inner_type({type_str}) expected {expected_inner_type}, got {actual_inner_type}"

        # Additional consistency check: if not a list, inner type should be unchanged
        if not expected_is_list:
            assert (
                actual_inner_type == type_str
            ), f"Non-list type {type_str} should return unchanged, got {actual_inner_type}"


def test_sql_constraints():
    """Test SQL constraint generation."""
    primitive_codec = SqlPrimitiveCodec()
    # Test string constraints
    string_type = build_code_primitive_type(
        base_type=CodePrimitiveBaseType.string, constraints=Json({"min_length": 5, "max_length": 100})
    )
    constraints = primitive_codec.get_sql_constraints(string_type)
    assert constraints is not None
    assert "LENGTH(value) >= 5" in constraints
    assert "LENGTH(value) <= 100" in constraints

    # Test numeric constraints
    int_type = build_code_primitive_type(
        base_type=CodePrimitiveBaseType.integer, constraints=Json({"minimum": 0, "maximum": 999})
    )
    constraints = primitive_codec.get_sql_constraints(int_type)
    assert constraints is not None
    assert "value >= 0" in constraints
    assert "value <= 999" in constraints

    # Test no constraints
    basic_type = build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    constraints = primitive_codec.get_sql_constraints(basic_type)
    assert constraints is None
