"""Validation tests for Aware Type Descriptor Adapter and Factory mapping."""

import pytest

from aware_grammar.type_descriptor_adapter import AwareTypeDescriptorAdapter

from aware_code.type_descriptor_nodes import TypeNodeKind, CollectionKind


def test_aware_adapter_primitives_collections_optional_parametric():
    adapter = AwareTypeDescriptorAdapter()

    n_str = adapter.parse_type("String")
    assert n_str.kind == TypeNodeKind.PRIMITIVE

    n_map = adapter.parse_type("Dict[String, Int]")
    assert n_map.kind == TypeNodeKind.MAPPING
    assert n_map.key is not None and n_map.value is not None
    assert n_map.key.kind == TypeNodeKind.PRIMITIVE
    assert n_map.value.kind == TypeNodeKind.PRIMITIVE

    n_list = adapter.parse_type("String[]")
    assert n_list.kind == TypeNodeKind.COLLECTION and n_list.collection_kind == CollectionKind.LIST
    assert n_list.element is not None and n_list.element.kind == TypeNodeKind.PRIMITIVE

    with pytest.raises(ValueError):
        _ = adapter.parse_type("String[]?")

    n_vec = adapter.parse_type("Vector(1536)")
    assert n_vec.kind == TypeNodeKind.PRIMITIVE
    assert (n_vec.text or "").startswith("Vector(")

    n_ident = adapter.parse_type("code.CodeLanguage")
    assert n_ident.kind == TypeNodeKind.IDENT
    assert (n_ident.text or "").startswith("code.")

    # Unknown parametric calls should remain IDENT (not PRIMITIVE)
    n_unknown_param = adapter.parse_type("Foo(1)")
    assert n_unknown_param.kind == TypeNodeKind.IDENT
    assert (n_unknown_param.text or "") == "Foo(1)"


def test_aware_ident_vs_primitive_disambiguation():
    adapter = AwareTypeDescriptorAdapter()

    n_ident = adapter.parse_type("Intent")
    assert n_ident.kind == TypeNodeKind.IDENT
    assert (n_ident.text or "") == "Intent"

    n_prim = adapter.parse_type("Int")
    assert n_prim.kind == TypeNodeKind.PRIMITIVE


def test_aware_adapter_strips_trailing_field_modifiers():
    adapter = AwareTypeDescriptorAdapter()

    n = adapter.parse_type("AnalyticMetric[] @AnalyticExecutionMetric many")
    assert n.kind == TypeNodeKind.COLLECTION
    assert n.collection_kind == CollectionKind.LIST
    assert n.element is not None
    assert n.element.kind == TypeNodeKind.IDENT
    assert (n.element.text or "") == "AnalyticMetric"

    # Ensure tuple parsing still works when modifiers trail the tuple type.
    t = adapter.parse_type("(User, Post) @SomeEdge")
    assert t.kind == TypeNodeKind.TUPLE
    assert [e.text for e in (t.elements or [])] == ["User", "Post"]

    # Optional + array + modifiers together is invalid: AnalyticMetric[]? @Edge many unique
    with pytest.raises(ValueError):
        _ = adapter.parse_type("AnalyticMetric[]? @Edge many unique")

    # Tuple labels should propagate through adapter
    named = adapter.parse_type("(user: User, post: Post)")
    assert named.kind == TypeNodeKind.TUPLE
    assert [e.label for e in named.elements] == ["user", "post"]
    assert [e.text for e in named.elements] == ["User", "Post"]

    # Tuple with nested combinations + modifiers
    complex_tuple = adapter.parse_type("(x: Vector(1536)?[], y: String?[]) @Edge many")
    assert complex_tuple.kind == TypeNodeKind.TUPLE
    assert [e.label for e in complex_tuple.elements] == ["x", "y"]
    # x: Vector(1536)?[] -> COLLECTION(list, UNION(Vector, Null))
    x_node = complex_tuple.elements[0]
    assert x_node.kind == TypeNodeKind.COLLECTION
    assert x_node.element is not None
    assert x_node.element.kind == TypeNodeKind.UNION
    # y: String?[] -> COLLECTION(list, UNION(String, Null))
    y_node = complex_tuple.elements[1]
    assert y_node.kind == TypeNodeKind.COLLECTION
    assert y_node.element is not None and y_node.element.kind == TypeNodeKind.UNION
