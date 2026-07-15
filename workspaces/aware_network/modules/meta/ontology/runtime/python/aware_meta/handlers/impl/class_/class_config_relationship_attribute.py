from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.class_.class_config_relationship_attribute import ClassConfigRelationshipAttribute

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_via_class_config_relationship(
    class_config_relationship_id: UUID,
    attribute_config_id: UUID,
    direction: ClassConfigRelationshipDirection,
    role: ClassConfigRelationshipAttributeRole,
) -> ClassConfigRelationshipAttribute:
    """
    Create deterministic ClassConfigRelationshipAttribute under a parent relationship scope.

    Contract:
    - Parent `ClassConfigRelationship` scope is propagated by traversal lowering.
    - Stable identity derives from parent scope + `(attribute_config_id, direction, role)`.
    """

    # --- AWARE: LOGIC START create_via_class_config_relationship
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_via_class_config_relationship
