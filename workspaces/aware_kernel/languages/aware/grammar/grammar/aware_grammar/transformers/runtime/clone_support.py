"""Structural clone helpers for runtime-transform stages."""

from __future__ import annotations

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_link import AttributeTypeDescriptorLink


def clone_attribute_config_for_runtime_function(*, source_attribute: AttributeConfig) -> AttributeConfig:
    """Clone only the structural AttributeConfig payload needed by runtime functions."""

    type_descriptor = clone_attribute_type_descriptor_tree(descriptor=source_attribute.type_descriptor)
    return AttributeConfig(
        id=source_attribute.id,
        type_descriptor=type_descriptor,
        code_section_attribute=None,
        owner_key=source_attribute.owner_key,
        name=source_attribute.name,
        description=source_attribute.description,
        default_value=source_attribute.default_value,
        is_primary=source_attribute.is_primary,
        is_public=source_attribute.is_public,
        is_required=source_attribute.is_required,
        is_unique=source_attribute.is_unique,
        is_virtual=source_attribute.is_virtual,
        exclude_serialization=source_attribute.exclude_serialization,
        type_descriptor_id=type_descriptor.id,
        code_section_attribute_id=None,
    )


def clone_attribute_type_descriptor_tree(*, descriptor: AttributeTypeDescriptor) -> AttributeTypeDescriptor:
    """Clone the descriptor tree while preserving shared type references by pointer."""

    clone = AttributeTypeDescriptor(
        id=descriptor.id,
        class_config=descriptor.class_config,
        enum_config=descriptor.enum_config,
        primitive_config=descriptor.primitive_config,
        child_links=[],
        collection_kind=descriptor.collection_kind,
        kind=descriptor.kind,
        class_config_id=descriptor.class_config_id,
        enum_config_id=descriptor.enum_config_id,
        primitive_config_id=descriptor.primitive_config_id,
    )
    for source_link in descriptor.child_links:
        child_clone = clone_attribute_type_descriptor_tree(descriptor=source_link.child)
        clone.child_links.append(
            AttributeTypeDescriptorLink(
                id=source_link.id,
                child=child_clone,
                role=source_link.role,
                position=source_link.position,
                attribute_type_descriptor_id=clone.id,
                child_id=child_clone.id,
            )
        )
    return clone


__all__ = [
    "clone_attribute_config_for_runtime_function",
    "clone_attribute_type_descriptor_tree",
]
