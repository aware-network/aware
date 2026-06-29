"""Validation tests for SQL Type Descriptor Adapter and Factory mapping."""

from sql_grammar.type_descriptor_adapter import SqlTypeDescriptorAdapter

from aware_code.type_descriptor_nodes import TypeNodeKind, CollectionKind


def test_sql_adapter_primitives_collections_vector_ident():
    adapter = SqlTypeDescriptorAdapter()

    n_text = adapter.parse_type("TEXT")
    assert n_text.kind == TypeNodeKind.PRIMITIVE

    n_array = adapter.parse_type("text[]")
    assert n_array.kind == TypeNodeKind.COLLECTION and n_array.collection_kind == CollectionKind.LIST
    assert n_array.element is not None and n_array.element.kind == TypeNodeKind.PRIMITIVE

    n_vec = adapter.parse_type("VECTOR(768)")
    assert n_vec.kind == TypeNodeKind.PRIMITIVE
    assert (n_vec.text or "").lower().startswith("vector(")

    # Nested arrays preserve recursion
    n_vec_arr = adapter.parse_type("VECTOR(256)[]")
    assert n_vec_arr.kind == TypeNodeKind.COLLECTION
    assert n_vec_arr.element is not None and n_vec_arr.element.kind == TypeNodeKind.PRIMITIVE

    # ARRAY<T> syntax
    a1 = adapter.parse_type("ARRAY<TEXT>")
    assert a1.kind == TypeNodeKind.COLLECTION
    assert a1.element is not None and a1.element.kind == TypeNodeKind.PRIMITIVE

    # ARRAY(...) syntax
    a2 = adapter.parse_type("ARRAY(VECTOR(512))")
    assert a2.kind == TypeNodeKind.COLLECTION
    assert a2.element is not None and a2.element.kind == TypeNodeKind.PRIMITIVE

    n_udt = adapter.parse_type("public.transaction_intent_status")
    assert n_udt.kind == TypeNodeKind.IDENT
    assert (n_udt.text or "").startswith("public.")

    # Quoted qualified ident should remain IDENT (codec won't parse it as primitive)
    q = adapter.parse_type('"public.transaction_intent_status"')
    assert q.kind == TypeNodeKind.IDENT
