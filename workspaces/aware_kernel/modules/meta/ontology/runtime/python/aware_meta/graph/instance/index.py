"""Index for ObjectInstanceGraph."""

from __future__ import annotations

from uuid import UUID
from typing import Any


# Kernel Graph Ontology
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph

# Meta Runtime
from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind


# Aware Graph
from aware_meta.graph.support.index.index import GraphIndex


class ObjectInstanceGraphIndex(GraphIndex[ObjectInstanceGraphMemberKind]):
    """Index for ObjectInstanceGraph that maps paths to entities and node kinds."""

    def __init__(self):
        """Initialize the index."""
        self._paths: dict[tuple[str, ...], tuple[Any, ObjectInstanceGraphMemberKind]] = {}
        self._by_id: dict[UUID, Any] = {}

    def get_all_paths(
        self,
    ) -> dict[tuple[str, ...], tuple[Any, ObjectInstanceGraphMemberKind]]:
        """Get all indexed paths."""
        return self._paths.copy()

    def get_entity_at_path(self, path: tuple[str, ...]) -> Any | None:
        """Get entity at the given path."""
        if path in self._paths:
            return self._paths[path][0]
        return None

    def get_entity_by_id(self, entity_id: UUID) -> Any | None:
        """
        Get an entity by its ID for fast lookups.

        Args:
            entity_id: The UUID of the entity to find

        Returns:
            The entity if found, otherwise None
        """
        return self._by_id.get(entity_id)

    def get_kind_at_path(self, path: tuple[str, ...]) -> ObjectInstanceGraphMemberKind | None:
        """Get node kind at the given path."""
        if path in self._paths:
            return self._paths[path][1]
        return None

    def add(
        self,
        entity: Any,
        path: tuple[str, ...],
        node_kind: ObjectInstanceGraphMemberKind,
    ) -> None:
        """Add an entity to the index."""
        self._paths[path] = (entity, node_kind)
        # Add to ID index if entity has an ID
        if hasattr(entity, "id") and entity.id:
            self._by_id[entity.id] = entity

    def clean(self) -> None:
        """Clean the index."""
        self._paths.clear()

    def get_by_kind(self, node_kind: ObjectInstanceGraphMemberKind) -> list[Any]:
        """Get all entities of a specific node kind."""
        return [entity for entity, kind in self._paths.values() if kind == node_kind]

    def get_object_instance_paths(self) -> dict[tuple[str, ...], Any]:
        """Get all paths that represent instances (canonical: ClassInstance)."""
        return {
            path: entity
            for path, (entity, kind) in self._paths.items()
            if kind == ObjectInstanceGraphMemberKind.class_instance
        }

    def get_attribute_paths(self) -> dict[tuple[str, ...], Any]:
        """Get all paths that represent attributes."""
        return {
            path: entity
            for path, (entity, kind) in self._paths.items()
            if kind == ObjectInstanceGraphMemberKind.attribute
        }

    def get_relationship_paths(self) -> dict[tuple[str, ...], Any]:
        """Get all paths that represent relationship instances."""
        return {
            path: entity
            for path, (entity, kind) in self._paths.items()
            if kind == ObjectInstanceGraphMemberKind.relationship_instance
        }

    def get_entity_by_stable_id(self, stable_id: UUID, reconciler) -> Any | None:
        """
        Get an entity by its stable ID.

        Args:
            stable_id: The stable ID to search for
            reconciler: The reconciler to use for getting stable IDs

        Returns:
            The entity if found, otherwise None
        """
        for entity, kind in self._paths.values():
            if reconciler.get_stable_id(entity) == stable_id:
                return entity
        return None


def build_index(graph: ObjectInstanceGraph) -> ObjectInstanceGraphIndex:
    """Build and cache the index for this graph."""
    index = ObjectInstanceGraphIndex()

    # Canonical: graph SSOT is ClassInstance + ClassInstanceRelationship.
    for ci in graph.class_instances:
        if ci.id is None:
            continue
        index.add(
            ci,
            ("class_instances", str(ci.id)),
            ObjectInstanceGraphMemberKind.class_instance,
        )
        # Index Attribute nodes so debug tooling (delta drift summaries) can resolve
        # attribute_config_id/name and show meaningful pre/post values.
        #
        # NOTE:
        # The canonical OIG hash does not depend on Attribute ids, but change graphs
        # reference attributes by id, so indexing them is required for attribution.
        attrs = getattr(ci, "attributes", None) or []
        for attr in attrs:
            attr_id = getattr(attr, "id", None)
            if attr_id is None:
                continue
            index.add(
                attr,
                ("class_instances", str(ci.id), "attributes", str(attr_id)),
                ObjectInstanceGraphMemberKind.attribute,
            )

    for rel in graph.class_instance_relationships:
        if rel.id is None:
            continue
        index.add(
            rel,
            ("class_instance_relationships", str(rel.id)),
            ObjectInstanceGraphMemberKind.relationship_instance,
        )

    # Cache the built index
    return index
