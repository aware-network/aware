from __future__ import annotations

from typing import Protocol
from uuid import UUID

from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph


class CandidateScopedRelationship(Protocol):
    id: UUID | None
    source_class_instance_id: UUID
    target_class_instance_id: UUID
    class_config_relationship_id: UUID


def relationship_in_candidate_scope(
    *,
    relationship: CandidateScopedRelationship,
    candidate_ids: set[UUID],
    include_relationship_config_ids: bool,
) -> bool:
    if relationship.id is not None and relationship.id in candidate_ids:
        return True
    if relationship.source_class_instance_id in candidate_ids:
        return True
    if relationship.target_class_instance_id in candidate_ids:
        return True
    return include_relationship_config_ids and relationship.class_config_relationship_id in candidate_ids


def candidate_class_instance_ids_for_source_object_ids(
    *,
    graph: ObjectInstanceGraph,
    source_object_ids: set[UUID],
) -> set[UUID]:
    if not source_object_ids:
        return set()
    return {
        class_instance.id
        for class_instance in graph.class_instances
        if class_instance.source_object_id in source_object_ids
    }


__all__ = [
    "CandidateScopedRelationship",
    "candidate_class_instance_ids_for_source_object_ids",
    "relationship_in_candidate_scope",
]
