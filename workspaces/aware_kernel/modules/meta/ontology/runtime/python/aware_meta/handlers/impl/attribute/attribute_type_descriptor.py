from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorRole
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_link import AttributeTypeDescriptorLink

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Code Ontology
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

# Meta Ontology
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta.graph.config.stable_ids import stable_attribute_type_descriptor_id
from aware_meta.primitive.config.builder import build_primitive_config

# Code Runtime
from aware_code.primitive_signature import build_code_primitive_signature

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_index,
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_primitive(primitive_base_type: CodePrimitiveBaseType) -> AttributeTypeDescriptor:
    """
    Create deterministic primitive descriptor chain.
    """

    # --- AWARE: LOGIC START create_primitive
    if not isinstance(primitive_base_type, CodePrimitiveBaseType):
        raw_primitive_base_type = str(primitive_base_type).strip()
        try:
            primitive_base_type = CodePrimitiveBaseType(raw_primitive_base_type)
        except ValueError:
            primitive_base_type = CodePrimitiveBaseType[raw_primitive_base_type.lower()]
    primitive_signature = build_code_primitive_signature(base_type=primitive_base_type)
    primitive_config = build_primitive_config(
        CodePrimitiveType(signature=primitive_signature, base_type=primitive_base_type)
    )
    attribute_type_descriptor_id = stable_attribute_type_descriptor_id(
        kind=AttributeTypeDescriptorKind.primitive.value,
        collection_kind=AttributeCollectionType.single.value,
        entity_id=primitive_config.id,
        child_links_fingerprint="",
    )
    session = current_handler_session()
    existing = session.imap_get(AttributeTypeDescriptor, attribute_type_descriptor_id)
    if existing is not None:
        if existing.kind != AttributeTypeDescriptorKind.primitive:
            raise RuntimeError(
                "AttributeTypeDescriptor.create_primitive kind mismatch for existing descriptor: "
                f"attribute_type_descriptor_id={attribute_type_descriptor_id}"
            )
        existing_primitive_config_id = existing.primitive_config_id
        if existing_primitive_config_id is not None and existing_primitive_config_id != primitive_config.id:
            raise RuntimeError(
                "AttributeTypeDescriptor.create_primitive primitive_config_id mismatch for existing descriptor: "
                f"attribute_type_descriptor_id={attribute_type_descriptor_id}"
            )
        return existing

    return AttributeTypeDescriptor(
        id=attribute_type_descriptor_id,
        kind=AttributeTypeDescriptorKind.primitive,
        collection_kind=AttributeCollectionType.single,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
    )
    # --- AWARE: LOGIC END create_primitive


async def create_enum(enum_config_id: UUID) -> AttributeTypeDescriptor:
    """
    Create deterministic enum descriptor from predeclared EnumConfig truth.
    """

    # --- AWARE: LOGIC START create_enum
    session = current_handler_session()
    enum_config = session.imap_get(EnumConfig, enum_config_id)
    if enum_config is None:
        raise RuntimeError(
            "AttributeTypeDescriptor.create_enum requires existing EnumConfig: " f"enum_config_id={enum_config_id}"
        )

    attribute_type_descriptor_id = stable_attribute_type_descriptor_id(
        kind=AttributeTypeDescriptorKind.enum.value,
        collection_kind=AttributeCollectionType.single.value,
        entity_id=enum_config_id,
        child_links_fingerprint="",
    )
    existing = session.imap_get(AttributeTypeDescriptor, attribute_type_descriptor_id)
    if existing is not None:
        if existing.kind != AttributeTypeDescriptorKind.enum:
            raise RuntimeError(
                "AttributeTypeDescriptor.create_enum kind mismatch for existing descriptor: "
                f"attribute_type_descriptor_id={attribute_type_descriptor_id}"
            )
        existing_enum_config_id = existing.enum_config_id
        if existing_enum_config_id is not None and existing_enum_config_id != enum_config_id:
            raise RuntimeError(
                "AttributeTypeDescriptor.create_enum enum_config_id mismatch for existing descriptor: "
                f"attribute_type_descriptor_id={attribute_type_descriptor_id}"
            )
        return existing
    return AttributeTypeDescriptor(
        id=attribute_type_descriptor_id,
        kind=AttributeTypeDescriptorKind.enum,
        collection_kind=AttributeCollectionType.single,
        enum_config=enum_config,
        enum_config_id=enum_config_id,
    )
    # --- AWARE: LOGIC END create_enum


async def create_class(class_config_id: UUID) -> AttributeTypeDescriptor:
    """
    Create deterministic class descriptor from predeclared ClassConfig truth.
    """

    # --- AWARE: LOGIC START create_class
    if not isinstance(class_config_id, UUID):
        class_config_id = UUID(str(class_config_id))
    session = current_handler_session()
    class_config = session.imap_get(ClassConfig, class_config_id)
    if class_config is None:
        try:
            class_config = current_handler_index().class_configs_by_id.get(
                class_config_id,
            )
        except (AttributeError, RuntimeError):
            class_config = None
    if class_config is None:
        raise RuntimeError(
            "AttributeTypeDescriptor.create_class requires existing ClassConfig: " f"class_config_id={class_config_id}"
        )

    attribute_type_descriptor_id = stable_attribute_type_descriptor_id(
        kind=AttributeTypeDescriptorKind.class_.value,
        collection_kind=AttributeCollectionType.single.value,
        entity_id=class_config_id,
        child_links_fingerprint="",
    )
    existing = session.imap_get(AttributeTypeDescriptor, attribute_type_descriptor_id)
    if existing is not None:
        if existing.kind != AttributeTypeDescriptorKind.class_:
            raise RuntimeError(
                "AttributeTypeDescriptor.create_class kind mismatch for existing descriptor: "
                f"attribute_type_descriptor_id={attribute_type_descriptor_id}"
            )
        existing_class_config_id = existing.class_config_id
        if existing_class_config_id is not None and existing_class_config_id != class_config_id:
            raise RuntimeError(
                "AttributeTypeDescriptor.create_class class_config_id mismatch for existing descriptor: "
                f"attribute_type_descriptor_id={attribute_type_descriptor_id}"
            )
        return existing
    return AttributeTypeDescriptor(
        id=attribute_type_descriptor_id,
        kind=AttributeTypeDescriptorKind.class_,
        collection_kind=AttributeCollectionType.single,
        class_config=class_config,
        class_config_id=class_config_id,
    )
    # --- AWARE: LOGIC END create_class


async def create_child_link(
    attribute_type_descriptor: AttributeTypeDescriptor,
    child_id: UUID,
    role: AttributeTypeDescriptorRole,
    position: int = 0,
) -> AttributeTypeDescriptorLink:
    """
    Create deterministic descriptor child link under this AttributeTypeDescriptor.

    Contract:
    - Parent `attribute_type_descriptor_id` is propagated by constructor lowering.
    - The child link stable id must resolve from
      `(attribute_type_descriptor_id via path, child_id, role, position)`.
    """

    # --- AWARE: LOGIC START create_child_link
    if attribute_type_descriptor.id is None:
        raise RuntimeError("AttributeTypeDescriptor.create_child_link requires attribute_type_descriptor.id")

    link = await AttributeTypeDescriptorLink.build_via_attribute_type_descriptor(
        attribute_type_descriptor_id=attribute_type_descriptor.id,
        child_id=child_id,
        role=role,
        position=position,
    )
    for existing in attribute_type_descriptor.child_links:
        if existing.id == link.id:
            if existing.child is None:
                existing.child = link.child
                existing.child_id = link.child_id
            return existing

    attribute_type_descriptor.child_links.append(link)
    return link
    # --- AWARE: LOGIC END create_child_link
