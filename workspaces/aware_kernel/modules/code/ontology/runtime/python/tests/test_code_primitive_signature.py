from __future__ import annotations

from aware_code.primitive_codec_base import CodePrimitiveCodecBase
from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code.primitive_signature import build_code_primitive_signature
from aware_code.stable_ids import (
    stable_code_primitive_type_element_type_id,
    stable_code_primitive_type_id,
    stable_code_primitive_type_union_type_id,
)
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code.types import JsonObject


class _TestCodec(CodePrimitiveCodecBase):
    def parse_exact(self, type_text: str) -> CodePrimitiveType | None:
        raise NotImplementedError

    def parse(self, type_text: str) -> CodePrimitiveType | None:
        raise NotImplementedError

    def render(self, prim: CodePrimitiveType) -> str | None:
        raise NotImplementedError

    def enum_ident(self, type_text: str) -> str:
        raise NotImplementedError

    def get_inner_type(self, type_text: str) -> str:
        raise NotImplementedError

    def is_void(self, type_text: str) -> bool:
        raise NotImplementedError

    def is_list(self, type_text: str) -> bool:
        raise NotImplementedError

    def is_set(self, type_text: str) -> bool:
        raise NotImplementedError

    def parse_literal(self, literal: str) -> object:
        raise NotImplementedError

    def to_literal_string(self, value: object) -> str:
        raise NotImplementedError


def test_primitive_codec_base_builds_canonical_leaf_ids() -> None:
    codec = _TestCodec()

    prim = codec.integer()

    assert prim.signature == "integer"
    assert prim.id == stable_code_primitive_type_id(signature="integer")


def test_primitive_codec_base_builds_canonical_tuple_slots() -> None:
    codec = _TestCodec()

    prim = codec.tuple(codec.integer(), codec.string())

    assert prim.signature == "tuple<integer,string>"
    assert prim.id == stable_code_primitive_type_id(signature="tuple<integer,string>")
    assert [slot.position for slot in prim.code_primitive_type_element_types] == [0, 1]
    assert prim.code_primitive_type_element_types[
        0
    ].id == stable_code_primitive_type_element_type_id(
        code_primitive_type_id=prim.id,
        position=0,
    )
    assert prim.code_primitive_type_element_types[
        1
    ].id == stable_code_primitive_type_element_type_id(
        code_primitive_type_id=prim.id,
        position=1,
    )


def test_primitive_codec_base_builds_canonical_union_slots() -> None:
    codec = _TestCodec()

    prim = codec.union(codec.integer(), codec.uuid())

    assert prim.signature == "union<integer|uuid>"
    assert prim.id == stable_code_primitive_type_id(signature="union<integer|uuid>")
    assert [slot.position for slot in prim.code_primitive_type_union_types] == [0, 1]
    assert prim.code_primitive_type_union_types[
        0
    ].id == stable_code_primitive_type_union_type_id(
        code_primitive_type_id=prim.id,
        position=0,
    )
    assert prim.code_primitive_type_union_types[
        1
    ].id == stable_code_primitive_type_union_type_id(
        code_primitive_type_id=prim.id,
        position=1,
    )


def test_build_code_primitive_signature_supports_current_constraint_shapes() -> None:
    assert (
        build_code_primitive_signature(
            base_type=CodePrimitiveBaseType.json,
            constraints=JsonObject({"json_kind": "object"}),
        )
        == "json<object>"
    )
    assert (
        build_code_primitive_signature(
            base_type=CodePrimitiveBaseType.vector,
            constraints=JsonObject({"dimension": 1536}),
        )
        == "vector<1536>"
    )
    assert (
        build_code_primitive_signature(
            base_type=CodePrimitiveBaseType.string,
            constraints=JsonObject({"one_of": ["linear", "exponential"]}),
        )
        == 'string{"one_of":["linear","exponential"]}'
    )


def test_build_code_primitive_signature_canonicalizes_generic_constraint_shape() -> (
    None
):
    assert (
        build_code_primitive_signature(
            base_type=CodePrimitiveBaseType.json,
            constraints=JsonObject({"pattern": "A+"}),
        )
        == 'json{"pattern":"A+"}'
    )


def test_build_code_primitive_type_defaults_generic_containers_to_any_members() -> None:
    prim = build_code_primitive_type(base_type=CodePrimitiveBaseType.dict)

    assert prim.signature == "dict<any,any>"
    assert (
        prim.key_type is not None
        and prim.key_type.base_type == CodePrimitiveBaseType.any
    )
    assert (
        prim.value_type is not None
        and prim.value_type.base_type == CodePrimitiveBaseType.any
    )
