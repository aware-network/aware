"""Tests for Aware primitive type detection and functionality."""

import pytest
from pathlib import Path

# Code Runtime
from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code.types.json import Json

# Kernel Graph Ontology
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Primitive types
from aware_grammar.primitive_codec import AwarePrimitiveCodec


def from_string_or_raise(primitive_codec: AwarePrimitiveCodec, type_text: str) -> CodePrimitiveType:
    primitive = primitive_codec.parse(type_text)
    if not primitive:
        raise ValueError(f"Failed to parse primitive type: {type_text}")
    return primitive


@pytest.fixture
def sample_aware_file():
    """Fixture that returns the path to the sample Aware file."""
    current_dir = Path(__file__).parent
    sample_file = current_dir / ".." / "samples" / "attribute_detection.aware"

    if not sample_file.exists():
        pytest.fail(f"Sample file not found: {sample_file}")

    return str(sample_file)


def test_basic_primitive_type_detection():
    """Test that Aware primitive types are correctly detected."""
    # Test basic primitive types
    primitive_codec = AwarePrimitiveCodec()
    assert from_string_or_raise(primitive_codec, "String").base_type == CodePrimitiveBaseType.string
    assert from_string_or_raise(primitive_codec, "Int").base_type == CodePrimitiveBaseType.integer
    assert from_string_or_raise(primitive_codec, "Bool").base_type == CodePrimitiveBaseType.boolean
    assert from_string_or_raise(primitive_codec, "Float").base_type == CodePrimitiveBaseType.float
    assert from_string_or_raise(primitive_codec, "Bytes").base_type == CodePrimitiveBaseType.bytes
    assert from_string_or_raise(primitive_codec, "DateTime").base_type == CodePrimitiveBaseType.datetime
    assert from_string_or_raise(primitive_codec, "UUID").base_type == CodePrimitiveBaseType.uuid
    assert from_string_or_raise(primitive_codec, "Json").base_type == CodePrimitiveBaseType.json
    assert from_string_or_raise(primitive_codec, "Any").base_type == CodePrimitiveBaseType.any
    assert from_string_or_raise(primitive_codec, "Vector").base_type == CodePrimitiveBaseType.vector


def test_optional_types():
    """Test Aware optional types with ? syntax."""
    # Test optional string
    primitive_codec = AwarePrimitiveCodec()
    optional_str = from_string_or_raise(primitive_codec, "String?")
    assert optional_str is not None
    assert optional_str.base_type == CodePrimitiveBaseType.union
    assert optional_str.union_types and len(optional_str.union_types) == 2

    # Check that one type is String and one is Null
    types = [t.base_type for t in optional_str.union_types]
    assert CodePrimitiveBaseType.string in types
    assert CodePrimitiveBaseType.null in types

    # Test conversion back to string
    assert primitive_codec.render(optional_str) == "String?"


def test_array_types():
    """Test Aware array types with [] syntax."""
    # Test basic array
    primitive_codec = AwarePrimitiveCodec()
    string_array = from_string_or_raise(primitive_codec, "String[]")
    assert string_array is not None
    assert string_array.base_type == CodePrimitiveBaseType.array
    assert string_array.item_type is not None
    assert string_array.item_type.base_type == CodePrimitiveBaseType.string
    assert primitive_codec.render(string_array) == "String[]"

    # Optional arrays are invalid (use optional elements instead).
    with pytest.raises(ValueError):
        _ = from_string_or_raise(primitive_codec, "Int[]?")

    # Test array of optional types
    array_optional = from_string_or_raise(primitive_codec, "String?[]")
    assert array_optional is not None
    assert array_optional.base_type == CodePrimitiveBaseType.array
    assert array_optional.item_type is not None
    assert array_optional.item_type.base_type == CodePrimitiveBaseType.union
    assert primitive_codec.render(array_optional) == "String?[]"


def test_dict_types():
    """Test Aware dict types with Dict[K, V] syntax."""
    primitive_codec = AwarePrimitiveCodec()

    dict_type = from_string_or_raise(primitive_codec, "Dict[String, Int]")
    assert dict_type.base_type == CodePrimitiveBaseType.dict
    assert dict_type.key_type is not None and dict_type.key_type.base_type == CodePrimitiveBaseType.string
    assert dict_type.value_type is not None and dict_type.value_type.base_type == CodePrimitiveBaseType.integer
    assert primitive_codec.render(dict_type) == "Dict[String, Int]"

    # Optional dict
    optional_dict = from_string_or_raise(primitive_codec, "Dict[String, Int]?")
    assert optional_dict.base_type == CodePrimitiveBaseType.union
    assert primitive_codec.render(optional_dict) == "Dict[String, Int]?"

    # Array of dicts
    dict_array = from_string_or_raise(primitive_codec, "Dict[String, Int][]")
    assert dict_array.base_type == CodePrimitiveBaseType.array
    assert dict_array.item_type is not None and dict_array.item_type.base_type == CodePrimitiveBaseType.dict
    assert primitive_codec.render(dict_array) == "Dict[String, Int][]"


def test_parametric_vector_types():
    """Test Aware parametric Vector types with dimension parameters."""
    primitive_codec = AwarePrimitiveCodec()
    # Test basic vector without parameters
    vector = from_string_or_raise(primitive_codec, "Vector")
    assert vector is not None
    assert vector.base_type == CodePrimitiveBaseType.vector
    assert vector.constraints is None
    assert primitive_codec.render(vector) == "Vector"

    # Test vector with dimension
    vector_1536 = from_string_or_raise(primitive_codec, "Vector(1536)")
    assert vector_1536 is not None
    assert vector_1536.base_type == CodePrimitiveBaseType.vector
    assert vector_1536.constraints == {"dimension": 1536}
    assert primitive_codec.render(vector_1536) == "Vector(1536)"

    # Whitespace inside parentheses should be accepted by the raw token parser
    vector_ws = from_string_or_raise(primitive_codec, "Vector( 1536 )")
    assert vector_ws.base_type == CodePrimitiveBaseType.vector
    assert vector_ws.constraints == {"dimension": 1536}
    assert primitive_codec.render(vector_ws) == "Vector(1536)"

    # Test using base class factory method
    vector_base = primitive_codec.vector(1024)
    assert vector_base is not None
    assert vector_base.base_type == CodePrimitiveBaseType.vector
    assert vector_base.constraints == {"dimension": 1024}
    assert primitive_codec.render(vector_base) == "Vector(1024)"

    # Test optional vector with dimension
    optional_vector = from_string_or_raise(primitive_codec, "Vector(512)?")
    assert optional_vector is not None
    assert optional_vector.base_type == CodePrimitiveBaseType.union
    assert primitive_codec.render(optional_vector) == "Vector(512)?"

    # Test array of vectors with dimension
    vector_array = from_string_or_raise(primitive_codec, "Vector(256)[]")
    assert vector_array is not None
    assert vector_array.base_type == CodePrimitiveBaseType.array
    assert vector_array.item_type is not None
    assert vector_array.item_type.base_type == CodePrimitiveBaseType.vector
    assert vector_array.item_type.constraints == {"dimension": 256}
    assert primitive_codec.render(vector_array) == "Vector(256)[]"


def test_vector_utility_methods():
    """Test Vector-specific utility methods."""
    primitive_codec = AwarePrimitiveCodec()
    # Test is_vector_type
    assert primitive_codec.is_vector_type("Vector")
    assert primitive_codec.is_vector_type("Vector(1536)")
    assert primitive_codec.is_vector_type("Vector?")
    assert primitive_codec.is_vector_type("Vector(512)?")
    assert primitive_codec.is_vector_type("Vector[]")
    assert not primitive_codec.is_vector_type("String")
    assert not primitive_codec.is_vector_type("Int")

    # Test get_vector_dimension
    assert primitive_codec.get_vector_dimension("Vector") is None
    assert primitive_codec.get_vector_dimension("Vector(1536)") == 1536
    assert primitive_codec.get_vector_dimension("Vector(512)?") == 512
    assert primitive_codec.get_vector_dimension("Vector(256)[]") == 256
    assert primitive_codec.get_vector_dimension("String") is None


def test_enum_type_stripping():
    """Test the enum_type method that strips decorations."""
    primitive_codec = AwarePrimitiveCodec()
    # Test basic types
    assert primitive_codec.enum_ident("String") == "String"
    assert primitive_codec.enum_ident("Int") == "Int"

    # Test stripping optional marker
    assert primitive_codec.enum_ident("String?") == "String"
    assert primitive_codec.enum_ident("Bool?") == "Bool"

    # Test stripping array marker
    assert primitive_codec.enum_ident("String[]") == "String"
    assert primitive_codec.enum_ident("Int[]") == "Int"

    # Optional arrays are invalid
    with pytest.raises(ValueError):
        _ = primitive_codec.enum_ident("String[]?")

    # Test stripping parametric type parameters
    assert primitive_codec.enum_ident("Vector(1536)") == "Vector"
    assert primitive_codec.enum_ident("Vector(512)?") == "Vector"
    assert primitive_codec.enum_ident("Vector(256)[]") == "Vector"


def test_primitive_type_detection():
    """Test the is_primitive_type method."""
    primitive_codec = AwarePrimitiveCodec()
    # Test basic primitives
    assert primitive_codec.is_primitive_type("String")
    assert primitive_codec.is_primitive_type("Int")
    assert primitive_codec.is_primitive_type("Bool")
    assert primitive_codec.is_primitive_type("Float")
    assert primitive_codec.is_primitive_type("Vector")

    # Test with decorations
    assert primitive_codec.is_primitive_type("String?")
    assert primitive_codec.is_primitive_type("Int[]")
    with pytest.raises(ValueError):
        _ = primitive_codec.is_primitive_type("Bool[]?")
    assert primitive_codec.is_primitive_type("Vector(1536)")
    assert primitive_codec.is_primitive_type("Vector(512)?")

    # Test non-primitives
    assert not primitive_codec.is_primitive_type("User")
    assert not primitive_codec.is_primitive_type("Post")
    assert not primitive_codec.is_primitive_type("CustomType")

    # Unknown parametric should not be treated as a primitive
    assert primitive_codec.parse("Foo(1)") is None


def test_void_type_detection():
    """Test void type detection."""
    primitive_codec = AwarePrimitiveCodec()
    assert primitive_codec.is_void("Void")
    assert primitive_codec.is_void("void")
    assert not primitive_codec.is_void("String")
    assert not primitive_codec.is_void("Int")


def test_to_string_conversion():
    """Test conversion from primitive types back to Aware syntax."""
    primitive_codec = AwarePrimitiveCodec()
    # Test basic types
    string_type = primitive_codec.string()
    assert primitive_codec.render(string_type) == "String"

    int_type = primitive_codec.integer()
    assert primitive_codec.render(int_type) == "Int"

    bool_type = primitive_codec.boolean()
    assert primitive_codec.render(bool_type) == "Bool"

    # Test array types
    # Test optional types (union with null)
    optional_type = primitive_codec.union(
        build_code_primitive_type(base_type=CodePrimitiveBaseType.string),
        build_code_primitive_type(base_type=CodePrimitiveBaseType.null),
    )
    assert primitive_codec.render(optional_type) == "String?"

    # Test vector with constraints
    vector_type = build_code_primitive_type(
        base_type=CodePrimitiveBaseType.vector,
        constraints=Json({"dimension": 1536}),
    )
    assert primitive_codec.render(vector_type) == "Vector(1536)"


def test_literal_parsing():
    """Test parsing of Aware literals."""
    primitive_codec = AwarePrimitiveCodec()
    # Test boolean literals
    assert primitive_codec.parse_literal("true") is True
    assert primitive_codec.parse_literal("false") is False

    # Test null literal
    assert primitive_codec.parse_literal("null") is None

    # Test string literals
    assert primitive_codec.parse_literal('"hello"') == "hello"
    assert primitive_codec.parse_literal("'world'") == "world"

    # Test number literals
    assert primitive_codec.parse_literal("42") == 42
    assert primitive_codec.parse_literal("3.14") == 3.14

    # Strict JSON object/array literals (defaults)
    assert primitive_codec.parse_literal("[]") == []
    assert primitive_codec.parse_literal("[1,2,3]") == [1, 2, 3]
    assert primitive_codec.parse_literal("{}") == {}
    assert primitive_codec.parse_literal('{"key":"value"}') == {"key": "value"}
    with pytest.raises(ValueError):
        _ = primitive_codec.parse_literal("{'key': 'value'}")

    # Test cast removal (type::cast syntax)
    assert primitive_codec.parse_literal('"test"::String') == "test"
    assert primitive_codec.parse_literal("42::Int") == 42


def test_to_literal_string():
    """Test conversion of Python values to Aware literal strings."""
    primitive_codec = AwarePrimitiveCodec()
    # Test basic types
    assert primitive_codec.to_literal_string(None) == "null"
    assert primitive_codec.to_literal_string(True) == "true"
    assert primitive_codec.to_literal_string(False) == "false"
    assert primitive_codec.to_literal_string("hello") == '"hello"'
    assert primitive_codec.to_literal_string(42) == "42"
    assert primitive_codec.to_literal_string(3.14) == "3.14"

    # Test string escaping
    assert primitive_codec.to_literal_string('say "hello"') == '"say \\"hello\\""'

    # Test complex types (strict JSON literals for defaults)
    assert primitive_codec.to_literal_string([1, 2, 3]) == "[1,2,3]"
    assert primitive_codec.to_literal_string({"key": "value"}) == '{"key":"value"}'


def test_make_nullable():
    """Test the make_nullable method."""
    primitive_codec = AwarePrimitiveCodec()
    # Test making a basic type nullable
    string_type = primitive_codec.string()
    nullable_string = primitive_codec.make_nullable(string_type)
    assert nullable_string.base_type == CodePrimitiveBaseType.union
    assert len(nullable_string.union_types) == 2
    assert primitive_codec.render(nullable_string) == "String?"


def test_factory_methods():
    """Test the factory methods for creating primitive types."""
    primitive_codec = AwarePrimitiveCodec()
    # Test basic factory methods
    assert primitive_codec.any().base_type == CodePrimitiveBaseType.any
    assert primitive_codec.integer().base_type == CodePrimitiveBaseType.integer
    assert primitive_codec.float().base_type == CodePrimitiveBaseType.float
    assert primitive_codec.string().base_type == CodePrimitiveBaseType.string
    assert primitive_codec.boolean().base_type == CodePrimitiveBaseType.boolean
    assert primitive_codec.datetime().base_type == CodePrimitiveBaseType.datetime
    assert primitive_codec.uuid().base_type == CodePrimitiveBaseType.uuid
    assert primitive_codec.json().base_type == CodePrimitiveBaseType.json

    # Test vector factory method
    vector_no_dim = primitive_codec.vector()
    assert vector_no_dim.base_type == CodePrimitiveBaseType.vector
    assert vector_no_dim.constraints is None

    vector_with_dim = primitive_codec.vector(1536)
    assert vector_with_dim.base_type == CodePrimitiveBaseType.vector
    assert vector_with_dim.constraints == {"dimension": 1536}

    # Test array factory method
    string_array = primitive_codec.array(primitive_codec.string())
    assert string_array.base_type == CodePrimitiveBaseType.array
    assert string_array.item_type is not None
    assert string_array.item_type.base_type == CodePrimitiveBaseType.string

    # Test union factory method
    union_type = primitive_codec.union(primitive_codec.string(), primitive_codec.integer())
    assert union_type.base_type == CodePrimitiveBaseType.union
    assert len(union_type.union_types) == 2
    assert union_type.union_types[0].base_type == CodePrimitiveBaseType.string
    assert union_type.union_types[1].base_type == CodePrimitiveBaseType.integer


def test_complex_type_combinations():
    """Test complex combinations of Aware types."""
    primitive_codec = AwarePrimitiveCodec()
    # Optional arrays are invalid (use optional elements instead).
    with pytest.raises(ValueError):
        _ = primitive_codec.parse("String[]?")

    # Test array of optional items
    array_optional = primitive_codec.parse("String?[]")
    assert array_optional is not None
    assert array_optional.base_type == CodePrimitiveBaseType.array
    assert array_optional.item_type is not None
    assert array_optional.item_type.base_type == CodePrimitiveBaseType.union
    assert primitive_codec.render(array_optional) == "String?[]"

    # Optional vectors in arrays are invalid
    with pytest.raises(ValueError):
        _ = primitive_codec.parse("Vector(1024)[]?")


def test_is_list_detection():
    """Test the is_list method for Aware types."""
    primitive_codec = AwarePrimitiveCodec()
    # Test basic array types
    assert primitive_codec.is_list("String[]") is True
    assert primitive_codec.is_list("Int[]") is True
    assert primitive_codec.is_list("Bool[]") is True
    assert primitive_codec.is_list("Float[]") is True
    assert primitive_codec.is_list("User[]") is True

    # Optional arrays are invalid
    with pytest.raises(ValueError):
        _ = primitive_codec.is_list("String[]?")

    # Test vector arrays
    assert primitive_codec.is_list("Vector[]") is True
    assert primitive_codec.is_list("Vector(1536)[]") is True
    with pytest.raises(ValueError):
        _ = primitive_codec.is_list("Vector(512)[]?")
    # With edge annotations/modifiers
    assert primitive_codec.is_list("Vector(1536)[] @Edge many") is True
    assert primitive_codec.is_list("AnalyticMetric[] @Edge many") is True

    # Test non-list types
    assert primitive_codec.is_list("String") is False
    assert primitive_codec.is_list("Int") is False
    assert primitive_codec.is_list("Bool") is False
    assert primitive_codec.is_list("Float") is False
    assert primitive_codec.is_list("User") is False
    assert primitive_codec.is_list("Vector") is False
    assert primitive_codec.is_list("Vector(1536)") is False

    # Test optional non-list types
    assert primitive_codec.is_list("String?") is False
    assert primitive_codec.is_list("Int?") is False
    assert primitive_codec.is_list("Vector(512)?") is False

    # Test edge cases
    assert primitive_codec.is_list("") is False
    assert primitive_codec.is_list("   ") is False


def test_get_inner_type_extraction():
    """Test the get_inner_type method for Aware types."""
    primitive_codec = AwarePrimitiveCodec()
    # Test basic array types
    assert primitive_codec.get_inner_type("String[]") == "String"
    assert primitive_codec.get_inner_type("Int[]") == "Int"
    assert primitive_codec.get_inner_type("Bool[]") == "Bool"
    assert primitive_codec.get_inner_type("Float[]") == "Float"
    assert primitive_codec.get_inner_type("User[]") == "User"

    # Optional arrays are invalid
    with pytest.raises(ValueError):
        _ = primitive_codec.get_inner_type("String[]?")

    # Test vector arrays
    assert primitive_codec.get_inner_type("Vector[]") == "Vector"
    assert primitive_codec.get_inner_type("Vector(1536)[]") == "Vector(1536)"
    with pytest.raises(ValueError):
        _ = primitive_codec.get_inner_type("Vector(512)[]?")

    # Edge modifiers should not interfere with inner-type extraction
    assert primitive_codec.get_inner_type("Vector(256)[] @Edge many") == "Vector(256)"
    assert primitive_codec.get_inner_type("AnalyticMetric[] @Edge many") == "AnalyticMetric"

    # Test complex parametric types
    assert primitive_codec.get_inner_type("Vector(1024)[]") == "Vector(1024)"
    with pytest.raises(ValueError):
        _ = primitive_codec.get_inner_type("Vector(256)[]?")

    # Test non-list types (should return unchanged)
    assert primitive_codec.get_inner_type("String") == "String"
    assert primitive_codec.get_inner_type("Int") == "Int"
    assert primitive_codec.get_inner_type("Bool") == "Bool"
    assert primitive_codec.get_inner_type("User") == "User"
    assert primitive_codec.get_inner_type("Vector") == "Vector"
    assert primitive_codec.get_inner_type("Vector(1536)") == "Vector(1536)"

    # Test optional non-list types (should return unchanged)
    assert primitive_codec.get_inner_type("String?") == "String?"
    assert primitive_codec.get_inner_type("Int?") == "Int?"
    assert primitive_codec.get_inner_type("Vector(512)?") == "Vector(512)?"

    # Test edge cases
    assert primitive_codec.get_inner_type("") == ""
    assert primitive_codec.get_inner_type("   ") == "   "


def test_is_list_and_get_inner_type_consistency():
    """Test that is_list and get_inner_type work consistently together."""
    primitive_codec = AwarePrimitiveCodec()
    test_cases = [
        # (type_string, is_list_expected, inner_type_expected)
        ("String[]", True, "String"),
        ("Int[]", True, "Int"),
        ("User[]", True, "User"),
        ("Vector(1536)[]", True, "Vector(1536)"),
        ("String", False, "String"),
        ("Int", False, "Int"),
        ("Vector", False, "Vector"),
        ("String?", False, "String?"),
        ("Vector(1024)?", False, "Vector(1024)?"),
    ]

    for type_text, expected_is_list, expected_inner_type in test_cases:
        actual_is_list = primitive_codec.is_list(type_text)
        actual_inner_type = primitive_codec.get_inner_type(type_text)

        assert (
            actual_is_list == expected_is_list
        ), f"is_list({type_text}) expected {expected_is_list}, got {actual_is_list}"
        assert (
            actual_inner_type == expected_inner_type
        ), f"get_inner_type({type_text}) expected {expected_inner_type}, got {actual_inner_type}"

        # Additional consistency check: if not a list, inner type should be unchanged
        if not expected_is_list:
            assert (
                actual_inner_type == type_text
            ), f"Non-list type {type_text} should return unchanged, got {actual_inner_type}"
