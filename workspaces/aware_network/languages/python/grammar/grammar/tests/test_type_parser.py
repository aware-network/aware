"""Validation tests for Python canonical TypeParser + TypeDescriptorAdapter boundary."""

from python_grammar.type_parser import PythonTypeParser
from python_grammar.type_descriptor_adapter import PythonTypeDescriptorAdapter

from aware_code.type_descriptor_nodes import TypeNodeKind, CollectionKind


def test_parser_optional_union_tuple_mapping_and_collections():
    p = PythonTypeParser()

    assert p.get_optional_inner("Optional[int]") == "int"
    assert p.get_optional_inner("typing.Optional[  str ]") == "str"

    assert p.get_classvar_inner("ClassVar[int]") == "int"

    assert p.get_union_members("Union[str, int]") == ["str", "int"]
    assert p.get_union_members("str | int") == ["str", "int"]
    # Depth-aware split: `dict[str, int] | None` should not split inside dict brackets
    assert p.get_union_members("dict[str, int] | None") == ["dict[str, int]", "None"]
    assert p.get_union_members("Union[dict[str, int], None]") == ["dict[str, int]", "None"]

    assert p.get_tuple_elements("tuple[str, int]") == ["str", "int"]
    assert p.get_tuple_elements("Tuple[dict[str, int], list[str]]") == ["dict[str, int]", "list[str]"]
    assert p.get_tuple_elements("typing.Tuple[Optional[str], dict[str, int]]") == ["Optional[str]", "dict[str, int]"]

    assert p.get_dict_kv("dict[str, int]") == ("str", "int")
    assert p.get_dict_kv("Dict[str, list[int]]") == ("str", "list[int]")
    assert p.get_dict_kv("typing.Dict[str, int]") == ("str", "int")

    assert p.get_list_inner("list[int]") == "int"
    assert p.get_list_inner("Sequence[User]") == "User"
    assert p.get_list_inner("typing.List[User]") == "User"
    assert p.get_set_inner("set[int]") == "int"
    assert p.get_set_inner("typing.FrozenSet[str]") == "str"
    assert p.strip_forward_ref_quotes("'User'") == ("User", True)


def test_parser_annotated_and_vector_dim_meta():
    p = PythonTypeParser()

    annotated = p.get_annotated_parts("Annotated[Vector, VectorDim(768)]")
    assert annotated is not None
    base, metas = annotated
    assert base == "Vector"
    assert "VectorDim(768)" in metas
    assert p.get_vector_dim_meta(metas) == 768

    # Non-vector Annotated should still parse into parts
    annotated2 = p.get_annotated_parts("Annotated[User, SomeMeta]")
    assert annotated2 is not None
    assert annotated2[0] == "User"


def test_adapter_builds_typenodes_using_parser_and_codec():
    a = PythonTypeDescriptorAdapter()

    n_opt = a.parse_type("Optional[int]")
    assert n_opt.kind == TypeNodeKind.UNION
    assert len(n_opt.members) == 2

    n_map = a.parse_type("dict[str, int]")
    assert n_map.kind == TypeNodeKind.MAPPING
    assert n_map.key is not None and n_map.key.kind == TypeNodeKind.PRIMITIVE
    assert n_map.value is not None and n_map.value.kind == TypeNodeKind.PRIMITIVE

    n_list = a.parse_type("list[str]")
    assert n_list.kind == TypeNodeKind.COLLECTION
    assert n_list.collection_kind == CollectionKind.LIST
    assert n_list.element is not None and n_list.element.kind == TypeNodeKind.PRIMITIVE

    n_set = a.parse_type("set[int]")
    assert n_set.kind == TypeNodeKind.COLLECTION
    assert n_set.collection_kind == CollectionKind.SET
    assert n_set.element is not None and n_set.element.kind == TypeNodeKind.PRIMITIVE

    n_union = a.parse_type("dict[str, int] | None")
    assert n_union.kind == TypeNodeKind.UNION
    assert len(n_union.members) == 2

    # Forward refs and Self should stay IDENT (not PRIMITIVE)
    n_self = a.parse_type("Self")
    assert n_self.kind == TypeNodeKind.IDENT and n_self.is_self is True
    n_fwd = a.parse_type("'User'")
    assert n_fwd.kind == TypeNodeKind.IDENT and n_fwd.is_forward_ref is True

    n_vec = a.parse_type("Annotated[Vector, VectorDim(768)]")
    assert n_vec.kind == TypeNodeKind.PRIMITIVE
    assert (n_vec.text or "").startswith("Vector(")
