"""Tests for Dart canonical primitive type codec."""

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

from dart_grammar.primitive_codec import DartPrimitiveCodec


def from_string_or_raise(codec: DartPrimitiveCodec, type_text: str):
    prim = codec.parse(type_text)
    assert prim is not None, f"Failed to parse primitive: {type_text}"
    return prim


def test_basic_dart_types():
    codec = DartPrimitiveCodec()
    assert from_string_or_raise(codec, "String").base_type == CodePrimitiveBaseType.string
    assert from_string_or_raise(codec, "int").base_type == CodePrimitiveBaseType.integer
    assert from_string_or_raise(codec, "double").base_type == CodePrimitiveBaseType.float
    assert from_string_or_raise(codec, "num").base_type == CodePrimitiveBaseType.float
    assert from_string_or_raise(codec, "bool").base_type == CodePrimitiveBaseType.boolean
    assert from_string_or_raise(codec, "DateTime").base_type == CodePrimitiveBaseType.datetime
    assert from_string_or_raise(codec, "dynamic").base_type == CodePrimitiveBaseType.any
    assert from_string_or_raise(codec, "Object").base_type == CodePrimitiveBaseType.any
    assert from_string_or_raise(codec, "null").base_type == CodePrimitiveBaseType.null
    assert from_string_or_raise(codec, "void").base_type == CodePrimitiveBaseType.null
    assert from_string_or_raise(codec, "UuidValue").base_type == CodePrimitiveBaseType.uuid
    assert from_string_or_raise(codec, "Uint8List").base_type == CodePrimitiveBaseType.bytes


def test_nullable_suffix_parses_as_union_with_null_and_renders_back():
    codec = DartPrimitiveCodec()
    prim = from_string_or_raise(codec, "String?")
    assert prim.base_type == CodePrimitiveBaseType.union
    assert len(prim.union_types) == 2
    assert {t.base_type for t in prim.union_types} == {CodePrimitiveBaseType.string, CodePrimitiveBaseType.null}
    assert codec.render(prim) == "String?"


def test_generic_collection_types():
    codec = DartPrimitiveCodec()

    l = from_string_or_raise(codec, "List<String>")
    assert l.base_type == CodePrimitiveBaseType.array
    assert l.item_type is not None and l.item_type.base_type == CodePrimitiveBaseType.string
    assert codec.render(l) == "List<String>"

    s = from_string_or_raise(codec, "Set<int>")
    assert s.base_type == CodePrimitiveBaseType.set
    assert s.item_type is not None and s.item_type.base_type == CodePrimitiveBaseType.integer
    assert codec.render(s) == "Set<int>"

    m = from_string_or_raise(codec, "Map<String, int>")
    assert m.base_type == CodePrimitiveBaseType.dict
    assert m.key_type is not None and m.value_type is not None
    assert m.key_type.base_type == CodePrimitiveBaseType.string
    assert m.value_type.base_type == CodePrimitiveBaseType.integer
    assert codec.render(m) == "Map<String, int>"


def test_nested_generics_and_nullable_inner():
    codec = DartPrimitiveCodec()

    nested = from_string_or_raise(codec, "Map<String, List<int>>")
    assert nested.base_type == CodePrimitiveBaseType.dict
    assert nested.value_type is not None
    assert nested.value_type.base_type == CodePrimitiveBaseType.array
    assert nested.value_type.item_type is not None
    assert nested.value_type.item_type.base_type == CodePrimitiveBaseType.integer
    assert codec.render(nested) == "Map<String, List<int>>"

    # Nullable inner element type should stay encoded canonically as UNION[int, null]
    l = from_string_or_raise(codec, "List<int?>")
    assert l.base_type == CodePrimitiveBaseType.array
    assert l.item_type is not None and l.item_type.base_type == CodePrimitiveBaseType.union
    assert codec.render(l) == "List<int?>"

    # Deep nesting with optional + nested nullable inner
    deep = from_string_or_raise(codec, "Map<String, List<Map<String, int?>>>?")
    assert deep.base_type == CodePrimitiveBaseType.union
    assert codec.render(deep) == "Map<String, List<Map<String, int?>>>?"


def test_unknown_ident_in_generics_returns_none_for_codec_parse():
    """Codec should refuse to fabricate primitives when generic args are unknown identifiers."""
    codec = DartPrimitiveCodec()
    assert codec.parse("List<User>") is None
    assert codec.parse("Map<String, User>") is not None  # Map defaults to DICT even if value type is unknown


def test_nullable_generic_types_round_trip():
    codec = DartPrimitiveCodec()
    prim = from_string_or_raise(codec, "List<String>?")
    assert prim.base_type == CodePrimitiveBaseType.union
    assert codec.render(prim) == "List<String>?"


def test_is_list_and_get_inner_type():
    codec = DartPrimitiveCodec()

    assert codec.is_list("List<String>") is True
    assert codec.is_list("Set<int>") is True
    assert codec.is_list("List<String>?") is True
    assert codec.is_list("Set<int>?") is True
    assert codec.is_list("String") is False
    assert codec.is_list("Map<String, int>") is False

    assert codec.get_inner_type("List<String>") == "String"
    assert codec.get_inner_type("Set<bool>") == "bool"
    assert codec.get_inner_type("List<String>?") == "String?"
    assert codec.get_inner_type("Set<int>?") == "int?"


def test_literal_parsing_and_to_literal_string():
    codec = DartPrimitiveCodec()

    assert codec.parse_literal("null") is None
    assert codec.parse_literal("true") is True
    assert codec.parse_literal("FALSE") is False
    assert codec.parse_literal("42") == 42
    assert codec.parse_literal("3.14") == 3.14
    assert codec.parse_literal("'hello'") == "hello"
    assert codec.parse_literal('"world"') == "world"

    assert codec.to_literal_string(None) == "null"
    assert codec.to_literal_string(True) == "true"
    assert codec.to_literal_string(42) == "42"
    assert codec.to_literal_string("hello") == "'hello'"
    assert codec.to_literal_string([1, 2, 3]) == "[1, 2, 3]"
