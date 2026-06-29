"""Validation tests for Python Type Descriptor Adapter and Meta mapping."""

from python_grammar.type_descriptor_adapter import PythonTypeDescriptorAdapter

from aware_code.type_descriptor_nodes import TypeNodeKind, CollectionKind


def test_adapter_primitives_and_collections():
    adapter = PythonTypeDescriptorAdapter()

    n_int = adapter.parse_type("int")
    assert n_int.kind == TypeNodeKind.PRIMITIVE
    assert (n_int.text or "").lower() == "int"

    n_list = adapter.parse_type("list[str]")
    assert n_list.kind == TypeNodeKind.COLLECTION
    assert n_list.collection_kind == CollectionKind.LIST
    assert n_list.element is not None and n_list.element.kind == TypeNodeKind.PRIMITIVE

    n_set = adapter.parse_type("set[int]")
    assert n_set.kind == TypeNodeKind.COLLECTION
    assert n_set.collection_kind == CollectionKind.SET
    assert n_set.element is not None and n_set.element.kind == TypeNodeKind.PRIMITIVE

    n_dict = adapter.parse_type("dict[str, int]")
    assert n_dict.kind == TypeNodeKind.MAPPING
    assert n_dict.key is not None and n_dict.key.kind == TypeNodeKind.PRIMITIVE
    assert n_dict.value is not None and n_dict.value.kind == TypeNodeKind.PRIMITIVE


def test_adapter_tuple_and_union_and_optional():
    adapter = PythonTypeDescriptorAdapter()

    n_tuple = adapter.parse_type("tuple[str, int]")
    assert n_tuple.kind == TypeNodeKind.TUPLE
    assert len(n_tuple.elements) == 2
    assert n_tuple.elements[0].kind == TypeNodeKind.PRIMITIVE
    assert n_tuple.elements[1].kind == TypeNodeKind.PRIMITIVE

    n_union_old = adapter.parse_type("Union[str, int]")
    assert n_union_old.kind == TypeNodeKind.UNION
    assert len(n_union_old.members) == 2

    n_union_bar = adapter.parse_type("str | int")
    assert n_union_bar.kind == TypeNodeKind.UNION
    assert len(n_union_bar.members) == 2

    n_opt = adapter.parse_type("Optional[int]")
    assert n_opt.kind == TypeNodeKind.UNION
    # Optional normalized to Union[int, None]
    kinds = [m.kind for m in n_opt.members]
    assert kinds.count(TypeNodeKind.PRIMITIVE) == 2


def test_adapter_ident_flags_self_and_forward_ref():
    adapter = PythonTypeDescriptorAdapter()

    n_self = adapter.parse_type("Self")
    assert n_self.kind == TypeNodeKind.IDENT
    assert n_self.is_self is True
    assert (n_self.text or "") == "Self"

    n_fwd = adapter.parse_type("'User'")
    assert n_fwd.kind == TypeNodeKind.IDENT
    assert n_fwd.is_forward_ref is True
    assert (n_fwd.text or "") == "User"


def test_adapter_ident_vs_primitive_disambiguation():
    adapter = PythonTypeDescriptorAdapter()

    # Should be IDENT, not misclassified as integer
    n_ident = adapter.parse_type("Intent")
    assert n_ident.kind == TypeNodeKind.IDENT
    assert (n_ident.text or "") == "Intent"

    # Should be PRIMITIVE via exact token mapping
    n_prim = adapter.parse_type("integer")
    assert n_prim.kind == TypeNodeKind.PRIMITIVE
