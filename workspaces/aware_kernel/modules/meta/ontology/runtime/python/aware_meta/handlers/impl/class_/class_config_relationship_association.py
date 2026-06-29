from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.class_.class_config_relationship_enums import ClassConfigRelationshipSideLoadingStrategy
from aware_meta_ontology.class_.class_config_relationship_association import ClassConfigRelationshipAssociation

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_via_class_config_relationship(
    class_config_relationship_id: UUID,
    class_config_id: UUID,
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
) -> ClassConfigRelationshipAssociation:
    """
    Create deterministic association metadata under a ClassConfigRelationship scope.

    Contract:
    - Parent `ClassConfigRelationship` scope is propagated by traversal lowering.
    - Stable identity derives from propagated relationship scope + `class_config_id`.
    """

    # --- AWARE: LOGIC START create_via_class_config_relationship
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_via_class_config_relationship
