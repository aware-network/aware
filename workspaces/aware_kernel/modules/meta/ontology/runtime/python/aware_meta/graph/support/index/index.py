"""Generic graph index implementation."""

from __future__ import annotations

from enum import Enum
from typing import Generic, TypeVar
from uuid import UUID

from aware_meta.graph.support.member import GraphMember

# Type parameter for node kind
T = TypeVar("T", bound=Enum)


class GraphIndex(Generic[T]):
    """
    Generic O(1) path/index implementation.

    Works with any graph whose nodes implement GraphMember protocol.
    Automatically builds paths from node.path_key and walks children.

    This concrete implementation replaces all graph-specific index classes,
    eliminating hundreds of lines of boilerplate per graph type.
    """

    def __init__(self):
        """Initialize the index."""
        self._by_path: dict[tuple[str, ...], tuple[GraphMember[T], T]] = {}
        self._by_id: dict[UUID, GraphMember[T]] = {}

    def get_all_paths(self) -> dict[tuple[str, ...], tuple[GraphMember[T], T]]:
        """Get all indexed paths."""
        return self._by_path.copy()

    def get_entity_at_path(self, path: tuple[str, ...]) -> GraphMember[T] | None:
        """Get entity at the given path."""
        result = self._by_path.get(path)
        return result[0] if result else None

    def get_by_path(self, path: tuple[str, ...]) -> tuple[GraphMember[T], T] | None:
        """Get entity and kind at the given path."""
        return self._by_path.get(path)

    def get_entity_by_id(self, entity_id: UUID) -> GraphMember[T] | None:
        """Get entity by its ID for fast lookups."""
        return self._by_id.get(entity_id)

    def add(self, entity: GraphMember[T], path: tuple[str, ...], node_kind: T) -> None:
        """Add an entity to the index."""
        self._by_path[path] = (entity, node_kind)
        entity_id = entity.get_id()
        if entity_id is not None:
            self._by_id[entity_id] = entity

    def clean(self) -> None:
        """Clean the index."""
        self._by_path.clear()
        self._by_id.clear()
