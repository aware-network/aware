from __future__ import annotations

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

from aware_meta.attribute.config.type_descriptor_builder import from_primitive_type
from aware_meta.primitive.config.builder import build_primitive_config


def _make_list_of_string() -> CodePrimitiveType:
    return build_code_primitive_type(
        base_type=CodePrimitiveBaseType.array,
        item_type=build_code_primitive_type(base_type=CodePrimitiveBaseType.string),
    )


def _make_map_string_to_int() -> CodePrimitiveType:
    return build_code_primitive_type(
        base_type=CodePrimitiveBaseType.dict,
        key_type=build_code_primitive_type(base_type=CodePrimitiveBaseType.string),
        value_type=build_code_primitive_type(base_type=CodePrimitiveBaseType.integer),
    )


def test_primitive_config_id_is_stable_per_primitive_structure() -> None:
    p1 = _make_list_of_string()
    p2 = _make_list_of_string()

    c1 = build_primitive_config(p1)
    c2 = build_primitive_config(p2)

    assert c1.id == c2.id
    assert c1.primitive_type_id == c2.primitive_type_id
    assert c1.primitive_type.id == c2.primitive_type.id


def test_attribute_type_descriptor_ids_are_stable_for_same_primitive_structure() -> (
    None
):
    p1 = _make_map_string_to_int()
    p2 = _make_map_string_to_int()

    # For pure primitive shapes, enum/class resolution is not needed; pass None placeholders.
    d1 = from_primitive_type(type_descriptor_adapter=None, primitive_codec=None, fqn_scope=None, prim=p1)  # type: ignore[arg-type]
    d2 = from_primitive_type(type_descriptor_adapter=None, primitive_codec=None, fqn_scope=None, prim=p2)  # type: ignore[arg-type]

    assert d1.id == d2.id
    assert d1.kind == d2.kind

    # Child links (KEY + VALUE) should be stable too.
    assert [(l.role.value, l.position, l.child.id, l.id) for l in d1.child_links] == [
        (l.role.value, l.position, l.child.id, l.id) for l in d2.child_links
    ]
