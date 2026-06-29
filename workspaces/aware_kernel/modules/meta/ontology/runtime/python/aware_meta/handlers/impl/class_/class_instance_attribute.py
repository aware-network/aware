from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.class_.class_instance_attribute import ClassInstanceAttribute

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.stable_ids import stable_class_instance_attribute_id

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_via_class_instance(
    class_instance_id: UUID, owner_key: UUID, attribute_config_id: UUID, value_root_id: UUID | None = None
) -> ClassInstanceAttribute:
    """
    Create one deterministic Attribute membership edge under a ClassInstance.

    Contract:
    - Parent `ClassInstance` scope is propagated by traversal lowering.
    - Edge identity derives from propagated class-instance scope + constructed Attribute identity.
    - The edge owns topology only and must lower through `Attribute.create(...)` for target identity.
    """

    # --- AWARE: LOGIC START create_via_class_instance
    session = current_handler_session()
    class_instance = session.imap_get(ClassInstance, class_instance_id)
    if class_instance is None:
        raise RuntimeError(
            "ClassInstanceAttribute.create_via_class_instance requires existing ClassInstance: "
            f"class_instance_id={class_instance_id}"
        )
    if class_instance.source_object_id != owner_key:
        raise RuntimeError(
            "ClassInstanceAttribute owner_key mismatch for existing ClassInstance: "
            f"class_instance_id={class_instance_id}"
        )

    attribute = await Attribute.create(
        owner_key=owner_key,
        attribute_config_id=attribute_config_id,
        value_root_id=value_root_id,
    )
    attribute_id = attribute.id
    if attribute_id is None:
        raise RuntimeError("Attribute.create must produce attribute.id for ClassInstanceAttribute membership")

    edge_id = stable_class_instance_attribute_id(
        class_instance_id=class_instance_id,
        attribute_id=attribute_id,
    )
    existing = session.imap_get(ClassInstanceAttribute, edge_id)
    if existing is not None:
        if existing.class_instance_id != class_instance_id or existing.attribute_id != attribute_id:
            raise RuntimeError(
                "ClassInstanceAttribute.create_via_class_instance payload mismatch for existing edge: "
                f"class_instance_attribute_id={edge_id}"
            )
        if existing.attribute is None:
            existing.attribute = attribute
            existing.attribute_id = attribute_id
        return existing

    return ClassInstanceAttribute(
        id=edge_id,
        class_instance_id=class_instance_id,
        attribute=attribute,
        attribute_id=attribute_id,
    )
    # --- AWARE: LOGIC END create_via_class_instance
