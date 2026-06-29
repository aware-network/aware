"""Tests for Python primitive type detection."""

import pytest

# Primitive types
from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

from python_grammar.primitive_codec import PythonPrimitiveCodec


def from_string_or_raise(primitive_codec: PythonPrimitiveCodec, type_text: str) -> CodePrimitiveType:
    primitive = primitive_codec.parse(type_text)
    if not primitive:
        raise ValueError(f"Failed to parse primitive type: {type_text}")
    return primitive


def test_primitive_type_detection():
    """Test that Python primitive types are correctly detected."""
    primitive_codec = PythonPrimitiveCodec()
    # Test basic primitive types
    assert from_string_or_raise(primitive_codec, "str").base_type == CodePrimitiveBaseType.string
    assert from_string_or_raise(primitive_codec, "int").base_type == CodePrimitiveBaseType.integer
    assert from_string_or_raise(primitive_codec, "bool").base_type == CodePrimitiveBaseType.boolean
    assert from_string_or_raise(primitive_codec, "float").base_type == CodePrimitiveBaseType.float
    assert from_string_or_raise(primitive_codec, "bytes").base_type == CodePrimitiveBaseType.bytes
    assert from_string_or_raise(primitive_codec, "None").base_type == CodePrimitiveBaseType.null

    # Unknown identifiers must not be coerced into primitives (critical for IDENT disambiguation)
    assert primitive_codec.parse("Self") is None
    assert primitive_codec.parse("Intent") is None

    # Test numeric types including Decimal
    assert from_string_or_raise(primitive_codec, "decimal").base_type == CodePrimitiveBaseType.float
    assert from_string_or_raise(primitive_codec, "numeric").base_type == CodePrimitiveBaseType.float

    # Test container types
    list_type = from_string_or_raise(primitive_codec, "list[str]")
    assert list_type is not None
    assert list_type.base_type == CodePrimitiveBaseType.array
    assert list_type.item_type and list_type.item_type.base_type == CodePrimitiveBaseType.string

    # Test dictionary types with key_type and value_type
    dict_type = from_string_or_raise(primitive_codec, "dict[str, int]")
    assert dict_type is not None
    assert dict_type.base_type == CodePrimitiveBaseType.dict
    assert dict_type.key_type and dict_type.key_type.base_type == CodePrimitiveBaseType.string
    assert dict_type.value_type and dict_type.value_type.base_type == CodePrimitiveBaseType.integer

    # Test dictionary with complex value type
    complex_dict_type = from_string_or_raise(primitive_codec, "dict[str, list[int]]")
    assert complex_dict_type is not None
    assert complex_dict_type.base_type == CodePrimitiveBaseType.dict
    assert complex_dict_type.key_type and complex_dict_type.key_type.base_type == CodePrimitiveBaseType.string
    assert complex_dict_type.value_type and complex_dict_type.value_type.base_type == CodePrimitiveBaseType.array
    assert (
        complex_dict_type.value_type.item_type
        and complex_dict_type.value_type.item_type.base_type == CodePrimitiveBaseType.integer
    )

    # Test dictionary with integer keys
    int_key_dict_type = from_string_or_raise(primitive_codec, "dict[int, str]")
    assert int_key_dict_type is not None
    assert int_key_dict_type.base_type == CodePrimitiveBaseType.dict
    assert int_key_dict_type.key_type and int_key_dict_type.key_type.base_type == CodePrimitiveBaseType.integer
    assert int_key_dict_type.value_type and int_key_dict_type.value_type.base_type == CodePrimitiveBaseType.string

    # Test Optional types
    optional_type = from_string_or_raise(primitive_codec, "Optional[str]")
    assert optional_type is not None
    assert optional_type.union_types and len(optional_type.union_types) == 2
    assert optional_type.union_types[0].base_type == CodePrimitiveBaseType.string
    assert optional_type.union_types[1].base_type == CodePrimitiveBaseType.null

    # Test Union types
    union_type = from_string_or_raise(primitive_codec, "Union[str, int]")
    assert union_type is not None
    assert union_type.union_types and len(union_type.union_types) == 2
    assert union_type.union_types[0].base_type == CodePrimitiveBaseType.string
    assert union_type.union_types[1].base_type == CodePrimitiveBaseType.integer

    # Test more complex types
    nested_type = from_string_or_raise(primitive_codec, "list[dict[str, int]]")
    assert nested_type is not None
    assert nested_type.base_type == CodePrimitiveBaseType.array
    assert nested_type.item_type and nested_type.item_type.base_type == CodePrimitiveBaseType.dict
    assert nested_type.item_type.key_type and nested_type.item_type.key_type.base_type == CodePrimitiveBaseType.string
    assert (
        nested_type.item_type.value_type and nested_type.item_type.value_type.base_type == CodePrimitiveBaseType.integer
    )


def test_primitive_type_transformation():
    """Test transformation between Python types and base types."""
    primitive_codec = PythonPrimitiveCodec()
    # Test to string conversion
    str_type = build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    assert primitive_codec.render(str_type) == "str"

    int_type = build_code_primitive_type(base_type=CodePrimitiveBaseType.integer)
    assert primitive_codec.render(int_type) == "int"

    # Test container types
    list_type = build_code_primitive_type(
        base_type=CodePrimitiveBaseType.array,
        item_type=build_code_primitive_type(base_type=CodePrimitiveBaseType.string),
    )
    assert primitive_codec.render(list_type) == "list[str]"

    # Test dictionary with key_type and value_type
    dict_type = build_code_primitive_type(
        base_type=CodePrimitiveBaseType.dict,
        key_type=build_code_primitive_type(base_type=CodePrimitiveBaseType.string),
        value_type=build_code_primitive_type(base_type=CodePrimitiveBaseType.integer),
    )
    assert primitive_codec.render(dict_type) == "dict[str, int]"

    # Test dictionary with complex value type
    complex_dict_type = build_code_primitive_type(
        base_type=CodePrimitiveBaseType.dict,
        key_type=build_code_primitive_type(base_type=CodePrimitiveBaseType.string),
        value_type=build_code_primitive_type(
            base_type=CodePrimitiveBaseType.array,
            item_type=build_code_primitive_type(base_type=CodePrimitiveBaseType.integer),
        ),
    )
    assert primitive_codec.render(complex_dict_type) == "dict[str, list[int]]"

    # Test union type to string conversion
    union_type = primitive_codec.union(
        build_code_primitive_type(base_type=CodePrimitiveBaseType.string),
        build_code_primitive_type(base_type=CodePrimitiveBaseType.integer),
    )
    assert primitive_codec.render(union_type) == "Union[str, int]"

    # Any should render as Any (canonical fallback)
    assert primitive_codec.render(build_code_primitive_type(base_type=CodePrimitiveBaseType.any)) == "Any"


def test_is_list_detection():
    """Test the is_list method for Python types."""
    primitive_codec = PythonPrimitiveCodec()
    # Test basic list types
    assert primitive_codec.is_list("List[str]") is True
    assert primitive_codec.is_list("list[int]") is True
    assert primitive_codec.is_list("typing.List[User]") is True

    # Test sequence types
    assert primitive_codec.is_list("Sequence[str]") is True
    assert primitive_codec.is_list("MutableSequence[int]") is True
    assert primitive_codec.is_list("typing.Sequence[User]") is True
    assert primitive_codec.is_list("typing.MutableSequence[Item]") is True

    # Test array bracket notation
    assert primitive_codec.is_list("str[]") is True
    assert primitive_codec.is_list("int[]") is True

    # Test optional lists
    assert primitive_codec.is_list("Optional[List[str]]") is True
    assert primitive_codec.is_list("Optional[list[int]]") is True

    # Test union types with lists
    assert primitive_codec.is_list("Union[List[str], None]") is True
    assert primitive_codec.is_list("List[str] | None") is True
    assert primitive_codec.is_list("str | List[int]") is True

    # Test non-list types
    assert primitive_codec.is_list("str") is False
    assert primitive_codec.is_list("int") is False
    assert primitive_codec.is_list("bool") is False
    assert primitive_codec.is_list("Optional[str]") is False
    assert primitive_codec.is_list("Union[str, int]") is False
    assert primitive_codec.is_list("dict[str, int]") is False

    # Test edge cases
    assert primitive_codec.is_list("") is False
    assert primitive_codec.is_list("   ") is False


def test_get_inner_type_extraction():
    """Test the get_inner_type method for Python types."""
    primitive_codec = PythonPrimitiveCodec()
    # Test basic list types
    assert primitive_codec.get_inner_type("List[str]") == "str"
    assert primitive_codec.get_inner_type("list[int]") == "int"
    assert primitive_codec.get_inner_type("typing.List[User]") == "User"

    # Test sequence types
    assert primitive_codec.get_inner_type("Sequence[str]") == "str"
    assert primitive_codec.get_inner_type("MutableSequence[int]") == "int"
    assert primitive_codec.get_inner_type("typing.Sequence[User]") == "User"
    assert primitive_codec.get_inner_type("typing.MutableSequence[Item]") == "Item"

    # Test array bracket notation
    assert primitive_codec.get_inner_type("str[]") == "str"
    assert primitive_codec.get_inner_type("int[]") == "int"
    assert primitive_codec.get_inner_type("User[]") == "User"

    # Test optional lists (should preserve Optional on inner type)
    assert primitive_codec.get_inner_type("Optional[List[str]]") == "Optional[str]"
    assert primitive_codec.get_inner_type("Optional[list[int]]") == "Optional[int]"

    # Test union types with lists
    assert primitive_codec.get_inner_type("Union[List[str], None]") == "Union[None, str]"
    assert primitive_codec.get_inner_type("List[str] | None") == "None | str"
    assert primitive_codec.get_inner_type("str | List[int]") == "str | int"

    # Test complex nested types
    assert primitive_codec.get_inner_type("List[dict[str, int]]") == "dict[str, int]"
    assert primitive_codec.get_inner_type("list[Optional[User]]") == "Optional[User]"

    # Test non-list types (should return unchanged)
    assert primitive_codec.get_inner_type("str") == "str"
    assert primitive_codec.get_inner_type("int") == "int"
    assert primitive_codec.get_inner_type("Optional[str]") == "Optional[str]"
    assert primitive_codec.get_inner_type("Union[str, int]") == "Union[str, int]"

    # Test edge cases
    assert primitive_codec.get_inner_type("") == ""
    assert primitive_codec.get_inner_type("   ") == "   "
