"""Validation tests for Aware canonical TypeParser boundary (raw token SSOT)."""

from aware_grammar.type_parser import AwareTypeParser


def test_parser_strips_field_modifiers_and_edge_annotations():
    p = AwareTypeParser()

    assert p.strip_trailing_field_modifiers("AnalyticMetric[] @Edge many") == "AnalyticMetric[]"
    assert p.strip_edge_annotation("AnalyticMetric[] @Edge") == "AnalyticMetric[]"
    # Multiple modifiers: parser should cut at first whitespace outside parens
    assert p.strip_trailing_field_modifiers("AnalyticMetric[] @Edge many unique") == "AnalyticMetric[]"
    # Tuple should preserve internal whitespace/commas and only strip trailing modifiers
    assert p.strip_trailing_field_modifiers("(User, Post) @SomeEdge many") == "(User, Post)"


def test_parser_optional_and_array_suffix_extraction():
    p = AwareTypeParser()

    assert p.get_optional_suffix_inner("String?") == "String"
    assert p.get_optional_suffix_inner("Int?") == "Int"
    assert p.get_array_suffix_inner("String[]") == "String"
    assert p.get_array_suffix_inner("String?[]") == "String?"
    # Preserve qualifiers + suffix stacking
    assert p.get_optional_suffix_inner("code.CodeLanguage?") == "code.CodeLanguage"
    assert p.get_array_suffix_inner("code.CodeLanguage[]") == "code.CodeLanguage"


def test_parser_parametric_and_enum_ident():
    p = AwareTypeParser()

    assert p.get_parametric_call("Vector(1536)") == ("Vector", "1536")
    # Whitespace inside parentheses is allowed by raw regex
    assert p.get_parametric_call("Vector( 1536 )") == ("Vector", "1536")
    assert p.enum_ident("Vector(1536)") == "Vector"
    assert p.enum_ident("Vector(1536)?") == "Vector"
    assert p.enum_ident("Vector(1536)[]") == "Vector"
    assert p.enum_ident("String?[]") == "String?"
    # Qualified identifiers keep qualifiers (resolution is later)
    assert p.enum_ident("code.CodeLanguage?[]") == "code.CodeLanguage?"
    assert p.get_dict_kv("Dict[String, Int]") == ("String", "Int")
    assert p.get_dict_kv("Dict[String, Dict[String, Int]]") == ("String", "Dict[String, Int]")
    assert p.enum_ident("Dict[String, Int]?") == "Dict"


def test_parser_tuple_entries_with_labels_and_nested_parametrics():
    p = AwareTypeParser()

    entries = p.get_tuple_entries("(user: User, vec: Vector(1536), ok: Bool)")
    assert entries is not None
    assert [e.label for e in entries] == ["user", "vec", "ok"]
    assert [e.type_text for e in entries] == ["User", "Vector(1536)", "Bool"]

    # Nested combos as tuple entries
    entries2 = p.get_tuple_entries("(x: Vector(1536)?[], y: String?[], z: code.CodeLanguage?[])")
    assert entries2 is not None
    assert [e.label for e in entries2] == ["x", "y", "z"]
    assert [e.type_text for e in entries2] == ["Vector(1536)?[]", "String?[]", "code.CodeLanguage?[]"]

    entries3 = p.get_tuple_entries("(meta: Dict[String, Int], name: String)")
    assert entries3 is not None
    assert [e.label for e in entries3] == ["meta", "name"]
    assert [e.type_text for e in entries3] == ["Dict[String, Int]", "String"]
