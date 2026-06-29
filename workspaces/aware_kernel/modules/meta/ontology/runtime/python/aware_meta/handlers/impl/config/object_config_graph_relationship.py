from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_relationship import ObjectConfigGraphRelationship
from aware_meta_ontology.graph.config.object_config_graph_relationship_class import ObjectConfigGraphRelationshipClass

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_class(
    object_config_graph_relationship: ObjectConfigGraphRelationship, class_config_id: UUID
) -> ObjectConfigGraphRelationshipClass:
    """
    Create deterministic ObjectConfigGraphRelationshipClass under this relationship.
    """

    # --- AWARE: LOGIC START create_class
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_class


async def build_via_object_config_graph(
    object_config_graph_id: UUID, target_object_config_graph_id: UUID
) -> ObjectConfigGraphRelationship:
    """
    Build deterministic ObjectConfigGraphRelationship within an ObjectConfigGraph scope.
    """

    # --- AWARE: LOGIC START build_via_object_config_graph
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_object_config_graph
