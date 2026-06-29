"""Validation tests for Dart canonical Type Descriptor Adapter."""

from dart_grammar.type_descriptor_adapter import DartTypeDescriptorAdapter

from aware_code.type_descriptor_nodes import TypeNodeKind, CollectionKind


def test_adapter_primitives_collections_mapping_nullable():
    adapter = DartTypeDescriptorAdapter()

    n_str = adapter.parse_type("String")
    assert n_str.kind == TypeNodeKind.PRIMITIVE

    n_list = adapter.parse_type("List<String>")
    assert n_list.kind == TypeNodeKind.COLLECTION and n_list.collection_kind == CollectionKind.LIST
    assert n_list.element is not None and n_list.element.kind == TypeNodeKind.PRIMITIVE

    n_set = adapter.parse_type("Set<int>")
    assert n_set.kind == TypeNodeKind.COLLECTION and n_set.collection_kind == CollectionKind.SET
    assert n_set.element is not None and n_set.element.kind == TypeNodeKind.PRIMITIVE

    n_map = adapter.parse_type("Map<String, int>")
    assert n_map.kind == TypeNodeKind.MAPPING
    assert n_map.key is not None and n_map.value is not None
    assert n_map.key.kind == TypeNodeKind.PRIMITIVE and n_map.value.kind == TypeNodeKind.PRIMITIVE

    n_nullable = adapter.parse_type("String?")
    assert n_nullable.kind == TypeNodeKind.UNION
    kinds = {m.kind for m in n_nullable.members}
    assert TypeNodeKind.PRIMITIVE in kinds


def test_adapter_nested_generics_and_unknown_idents():
    adapter = DartTypeDescriptorAdapter()

    # Nested generics
    n = adapter.parse_type("Map<String, List<int>>")
    assert n.kind == TypeNodeKind.MAPPING
    assert n.key is not None and n.value is not None
    assert n.key.kind == TypeNodeKind.PRIMITIVE
    assert n.value.kind == TypeNodeKind.COLLECTION
    assert n.value.collection_kind == CollectionKind.LIST
    assert n.value.element is not None and n.value.element.kind == TypeNodeKind.PRIMITIVE

    # Unknown identifiers inside generics should become IDENT at the leaves
    u = adapter.parse_type("List<User>")
    assert u.kind == TypeNodeKind.COLLECTION
    assert u.element is not None and u.element.kind == TypeNodeKind.IDENT
    assert (u.element.text or "") == "User"

    m = adapter.parse_type("Map<String, User>")
    assert m.kind == TypeNodeKind.MAPPING
    assert m.value is not None and m.value.kind == TypeNodeKind.IDENT
    assert (m.value.text or "") == "User"

    # Nullable outer collection should become UNION[collection, null]
    opt = adapter.parse_type("List<User>?")
    assert opt.kind == TypeNodeKind.UNION
    assert any(mem.kind == TypeNodeKind.COLLECTION for mem in opt.members)

    # Nullable inner type inside generic should become UNION at the element
    inner_opt = adapter.parse_type("List<int?>")
    assert inner_opt.kind == TypeNodeKind.COLLECTION
    assert inner_opt.element is not None
    assert inner_opt.element.kind == TypeNodeKind.UNION

    # More disambiguation: substring shouldn't trigger primitive
    n2 = adapter.parse_type("Integer")
    assert n2.kind == TypeNodeKind.IDENT


def test_adapter_ident_vs_primitive_disambiguation():
    adapter = DartTypeDescriptorAdapter()

    # IDENT should not be misclassified due to substring 'int'
    n_ident = adapter.parse_type("Intention")
    assert n_ident.kind == TypeNodeKind.IDENT
    assert (n_ident.text or "") == "Intention"

    # Primitive exact token remains primitive
    n_prim = adapter.parse_type("int")
    assert n_prim.kind == TypeNodeKind.PRIMITIVE
