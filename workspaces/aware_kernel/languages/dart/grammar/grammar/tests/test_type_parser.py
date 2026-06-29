"""Validation tests for Dart canonical TypeParser boundary (raw token SSOT)."""

from dart_grammar.type_parser import DartTypeParser


def test_parser_optional_suffix_and_generics_extraction():
    p = DartTypeParser()

    assert p.get_optional_inner("String?") == "String"
    assert p.get_optional_inner("List<String>?") == "List<String>"
    assert p.get_optional_inner("String") is None

    assert p.get_list_inner("List<String>") == "String"
    assert p.get_set_inner("Set<int>") == "int"
    assert p.get_dict_kv("Map<String, int>") == ("String", "int")

    # Whitespace tolerance
    assert p.get_list_inner("List < String >") == "String"
    # We accept whitespace before the nullable suffix as long as `?` is the last token
    assert p.get_set_inner("Set < int > ?") == "int"
    assert p.get_dict_kv("Map < String , int >") == ("String", "int")
    assert p.get_dict_kv("Map < String , List < int ? > > ?") == ("String", "List < int ? >")


def test_parser_supports_nested_generics():
    p = DartTypeParser()

    assert p.get_list_inner("List<Map<String, int>>") == "Map<String, int>"
    assert p.get_dict_kv("Map<String, List<int>>") == ("String", "List<int>")
    assert p.get_optional_inner("List<Map<String, List<int>>>?") == "List<Map<String, List<int>>>"
    assert p.get_dict_kv("Map<String, Map<String, int>>") == ("String", "Map<String, int>")
    assert p.get_list_inner("List < Map < String , List < int ? > > >") == "Map < String , List < int ? > >"
