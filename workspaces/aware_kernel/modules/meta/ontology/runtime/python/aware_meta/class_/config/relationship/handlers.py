"""
Relationship helpers (SSOT utilities).

This module exists to centralize small, deterministic derivations over canonical
`ClassConfigRelationship` objects so renderers/transformers/builders do not
reimplement slightly different heuristics.
"""

from __future__ import annotations

from uuid import UUID

from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship


def get_association_class_ids(
    relationships: list[ClassConfigRelationship],
) -> set[UUID]:
    """
    Return the set of association (join-table / edge-container) class IDs referenced
    by the provided relationships.

    SSOT: association-ness is carried on `ClassConfigRelationship.class_config_relationship_association_edge`
    (relationship-level), not on `ClassConfigIdentity.is_edge` (class-level).
    """
    assoc_ids: set[UUID] = set()
    for rel in relationships:
        assoc = rel.class_config_relationship_association_edge
        if assoc is None:
            continue
        if assoc.class_config_id is None:
            continue
        assoc_ids.add(assoc.class_config_id)
    return assoc_ids
