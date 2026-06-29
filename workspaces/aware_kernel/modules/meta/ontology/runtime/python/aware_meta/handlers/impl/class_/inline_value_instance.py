from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_meta_ontology.class_.inline_value_instance_attribute import InlineValueInstanceAttribute

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.stable_ids import stable_inline_value_instance_id
from aware_meta.handlers.impl.class_ import (
    inline_value_instance_attribute as inline_value_instance_attribute_handler,
)

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_index, current_handler_session

# --- AWARE: USER_IMPORTS END


async def build(owner_key: UUID, class_config_id: UUID) -> InlineValueInstance:
    """
    Build deterministic InlineValueInstance from a caller-owned value anchor.

    Contract:
    - Identity resolves from `(owner_key, class_config_id)`.
    - `owner_key` is a semantic owner anchor, not an implicit parent-propagated FK.
    - InlineValueInstance is value-world truth only: no OIG scope, no source_object_id,
      no relationships, and no commit/change rails.
    """

    # --- AWARE: LOGIC START build
    session = current_handler_session()
    class_config = session.imap_get(ClassConfig, class_config_id)
    if class_config is None:
        class_config = current_handler_index().class_configs_by_id.get(class_config_id)
        if class_config is None:
            raise RuntimeError(
                "InlineValueInstance.build requires existing ClassConfig: " f"class_config_id={class_config_id}"
            )
        session.imap_add(class_config)

    inline_value_instance_id = stable_inline_value_instance_id(
        class_config_id=class_config_id,
        owner_key=owner_key,
    )
    existing = session.imap_get(InlineValueInstance, inline_value_instance_id)
    if existing is not None:
        if existing.class_config_id != class_config_id or existing.owner_key != owner_key:
            raise RuntimeError(
                "InlineValueInstance.build payload mismatch for existing InlineValueInstance: "
                f"inline_value_instance_id={inline_value_instance_id}"
            )
        if existing.class_config is None:
            existing.class_config = class_config
        return existing

    return InlineValueInstance(
        id=inline_value_instance_id,
        class_config=class_config,
        class_config_id=class_config_id,
        owner_key=owner_key,
        inline_value_instance_attributes=[],
    )
    # --- AWARE: LOGIC END build


async def create_attribute(
    inline_value_instance: InlineValueInstance, attribute_config_id: UUID, value_root_id: UUID | None = None
) -> InlineValueInstanceAttribute:
    """
    Create deterministic Attribute membership under this InlineValueInstance.

    Contract:
    - InlineValueInstance owns membership and topology only.
    - Attribute identity resolves from `(owner_key, attribute_config_id)` via shared owner key.
    - The returned edge is the honest containment rail for value-world Attribute membership.
    """

    # --- AWARE: LOGIC START create_attribute
    inline_value_instance_id = inline_value_instance.id
    if inline_value_instance_id is None:
        raise RuntimeError("InlineValueInstance.create_attribute requires inline_value_instance.id")

    edge = await inline_value_instance_attribute_handler.create_via_inline_value_instance(
        inline_value_instance_id=inline_value_instance_id,
        owner_key=inline_value_instance.owner_key,
        attribute_config_id=attribute_config_id,
        value_root_id=value_root_id,
    )
    for existing in inline_value_instance.inline_value_instance_attributes:
        if existing.id == edge.id:
            if existing.attribute is None:
                existing.attribute = edge.attribute
                existing.attribute_id = edge.attribute_id
            return existing

    inline_value_instance.inline_value_instance_attributes.append(edge)
    return edge
    # --- AWARE: LOGIC END create_attribute
