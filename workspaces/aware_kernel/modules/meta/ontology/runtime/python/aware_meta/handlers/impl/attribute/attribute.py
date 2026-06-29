from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.attribute.attribute import Attribute

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.stable_ids import stable_attribute_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create(owner_key: UUID, attribute_config_id: UUID, value_root_id: UUID | None = None) -> Attribute:
    """
    Create deterministic Attribute identity from caller-owned `owner_key` + `attribute_config_id`.

    Contract:
    - `owner_key` is the owner-scoped semantic anchor for shared structural Attribute identity.
    - Parent containment / edge routing must not enter the Attribute stable-id formula.
    - Direct owner foreign keys remain topology truth only.
    """

    # --- AWARE: LOGIC START create
    session = current_handler_session()
    attribute_config = session.imap_get(AttributeConfig, attribute_config_id)
    if attribute_config is None:
        raise RuntimeError(
            "Attribute.create requires existing AttributeConfig: " f"attribute_config_id={attribute_config_id}"
        )

    attribute_id = stable_attribute_id(
        owner_key=owner_key,
        attribute_config_id=attribute_config_id,
    )
    existing = session.imap_get(Attribute, attribute_id)
    if existing is not None:
        if existing.owner_key != owner_key or existing.attribute_config_id != attribute_config_id:
            raise RuntimeError(
                "Attribute.create payload mismatch for existing Attribute: " f"attribute_id={attribute_id}"
            )
        if existing.attribute_config is None:
            existing.attribute_config = attribute_config
        if value_root_id is not None and existing.value_root_id not in {None, value_root_id}:
            raise RuntimeError(
                "Attribute.create value_root_id mismatch for existing Attribute: " f"attribute_id={attribute_id}"
            )
        return existing

    if value_root_id is None:
        raise RuntimeError(
            "Attribute.create currently requires existing value_root_id; "
            "raw-value lowering must happen through Meta builders first."
        )
    value_root = session.imap_get(AttributeValue, value_root_id)
    if value_root is None:
        raise RuntimeError("Attribute.create requires existing AttributeValue root: " f"value_root_id={value_root_id}")

    return Attribute(
        id=attribute_id,
        owner_key=owner_key,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config_id,
        value_root=value_root,
        value_root_id=value_root_id,
    )
    # --- AWARE: LOGIC END create
