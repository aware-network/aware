from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorRole
from aware_meta_ontology.attribute.attribute_type_descriptor_link import AttributeTypeDescriptorLink

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.stable_ids import stable_attribute_type_descriptor_link_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_attribute_type_descriptor(
    attribute_type_descriptor_id: UUID, child_id: UUID, role: AttributeTypeDescriptorRole, position: int = 0
) -> AttributeTypeDescriptorLink:
    """
    Create deterministic descriptor child link under one AttributeTypeDescriptor.

    Contract:
    - Parent `attribute_type_descriptor_id` is propagated by constructor lowering.
    - Identity resolves from `(attribute_type_descriptor_id via path, child_id, role, position)`.
    """

    # --- AWARE: LOGIC START build_via_attribute_type_descriptor
    if position < 0:
        raise RuntimeError("AttributeTypeDescriptorLink.build_via_attribute_type_descriptor requires position >= 0")

    session = current_handler_session()
    child = session.imap_get(AttributeTypeDescriptor, child_id)
    if child is None:
        raise RuntimeError(
            "AttributeTypeDescriptorLink.build_via_attribute_type_descriptor requires existing child descriptor: "
            f"child_id={child_id}"
        )

    role_value = role.value if hasattr(role, "value") else str(role)
    link_id = stable_attribute_type_descriptor_link_id(
        attribute_type_descriptor_id=attribute_type_descriptor_id,
        child_id=child_id,
        role=role_value,
        position=position,
    )
    existing = session.imap_get(AttributeTypeDescriptorLink, link_id)
    if existing is not None:
        existing_child_id = existing.child_id or (existing.child.id if existing.child is not None else None)
        if (
            existing.attribute_type_descriptor_id != attribute_type_descriptor_id
            or existing_child_id != child_id
            or existing.role != role
            or existing.position != position
        ):
            raise RuntimeError(
                "AttributeTypeDescriptorLink.build_via_attribute_type_descriptor payload mismatch for existing link: "
                f"attribute_type_descriptor_link_id={link_id}"
            )
        if existing.child is None:
            existing.child = child
            existing.child_id = child.id
        return existing

    return AttributeTypeDescriptorLink(
        id=link_id,
        attribute_type_descriptor_id=attribute_type_descriptor_id,
        child=child,
        child_id=child.id,
        role=role,
        position=position,
    )
    # --- AWARE: LOGIC END build_via_attribute_type_descriptor
