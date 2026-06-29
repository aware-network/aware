from __future__ import annotations

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta.attribute.config.type_descriptor_helpers import (
    resolve_type_class_config_id,
    resolve_type_info,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import (
    AttributeTypeDescriptorLink,
)
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig


def _link(
    *,
    parent: AttributeTypeDescriptor,
    child: AttributeTypeDescriptor,
    role: Role,
    position: int = 0,
) -> AttributeTypeDescriptorLink:
    return AttributeTypeDescriptorLink(
        attribute_type_descriptor_id=parent.id,
        child=child,
        child_id=child.id,
        role=role,
        position=position,
    )


def _attr(name: str, descriptor: AttributeTypeDescriptor) -> AttributeConfig:
    return AttributeConfig(
        owner_key="test.Owner",
        name=name,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )


def _primitive_descriptor(base_type: CodePrimitiveBaseType) -> AttributeTypeDescriptor:
    primitive_type = CodePrimitiveType(signature=base_type.value, base_type=base_type)
    primitive_config = PrimitiveConfig(
        primitive_type=primitive_type, primitive_type_id=primitive_type.id
    )
    return AttributeTypeDescriptor(
        kind=Kind.primitive,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
    )


def test_resolve_type_info_handles_self_referential_collection_descriptor() -> None:
    descriptor = AttributeTypeDescriptor(
        kind=Kind.collection,
        collection_kind=AttributeCollectionType.list,
        child_links=[],
    )
    descriptor.child_links.append(
        _link(parent=descriptor, child=descriptor, role=Role.element)
    )

    info = resolve_type_info(_attr("items", descriptor))

    assert info.kind == Kind.collection
    assert info.collection_kind == AttributeCollectionType.list
    assert resolve_type_class_config_id(_attr("items", descriptor)) is None


def test_resolve_type_info_skips_cycle_and_keeps_union_candidate() -> None:
    descriptor = AttributeTypeDescriptor(kind=Kind.union, child_links=[])
    primitive = _primitive_descriptor(CodePrimitiveBaseType.string)
    descriptor.child_links.append(
        _link(parent=descriptor, child=descriptor, role=Role.member, position=0)
    )
    descriptor.child_links.append(
        _link(parent=descriptor, child=primitive, role=Role.member, position=1)
    )

    info = resolve_type_info(_attr("value", descriptor))

    assert info.kind == Kind.primitive
    assert info.primitive_config is primitive.primitive_config
