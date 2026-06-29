from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.class_.inline_value_instance_attribute import InlineValueInstanceAttribute

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_meta_ontology.stable_ids import stable_inline_value_instance_attribute_id

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_via_inline_value_instance(
    inline_value_instance_id: UUID, owner_key: UUID, attribute_config_id: UUID, value_root_id: UUID | None = None
) -> InlineValueInstanceAttribute:
    """
    Create one deterministic Attribute membership edge under an InlineValueInstance.

    Contract:
    - Parent `InlineValueInstance` scope is propagated by traversal lowering.
    - Edge identity derives from propagated inline-value-instance scope + constructed Attribute
    identity.
    - The edge owns topology only and must lower through `Attribute.create(...)` for target identity.
    """

    # --- AWARE: LOGIC START create_via_inline_value_instance
    session = current_handler_session()
    inline_value_instance = session.imap_get(InlineValueInstance, inline_value_instance_id)
    if inline_value_instance is None:
        raise RuntimeError(
            "InlineValueInstanceAttribute.create_via_inline_value_instance requires existing InlineValueInstance: "
            f"inline_value_instance_id={inline_value_instance_id}"
        )
    if inline_value_instance.owner_key != owner_key:
        raise RuntimeError(
            "InlineValueInstanceAttribute owner_key mismatch for existing InlineValueInstance: "
            f"inline_value_instance_id={inline_value_instance_id}"
        )
    attribute = await Attribute.create(
        owner_key=owner_key,
        attribute_config_id=attribute_config_id,
        value_root_id=value_root_id,
    )
    attribute_id = attribute.id
    if attribute_id is None:
        raise RuntimeError("Attribute.create must produce attribute.id for InlineValueInstanceAttribute membership")

    edge_id = stable_inline_value_instance_attribute_id(
        inline_value_instance_id=inline_value_instance_id,
        attribute_id=attribute_id,
    )
    existing = session.imap_get(InlineValueInstanceAttribute, edge_id)
    if existing is not None:
        if existing.inline_value_instance_id != inline_value_instance_id or existing.attribute_id != attribute_id:
            raise RuntimeError(
                "InlineValueInstanceAttribute.create_via_inline_value_instance payload mismatch for existing edge: "
                f"inline_value_instance_attribute_id={edge_id}"
            )
        if existing.attribute is None:
            existing.attribute = attribute
            existing.attribute_id = attribute_id
        return existing

    return InlineValueInstanceAttribute(
        id=edge_id,
        inline_value_instance_id=inline_value_instance_id,
        attribute=attribute,
        attribute_id=attribute_id,
    )
    # --- AWARE: LOGIC END create_via_inline_value_instance
