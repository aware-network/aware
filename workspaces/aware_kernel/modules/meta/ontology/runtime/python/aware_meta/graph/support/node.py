"""Generic graph node representation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, List, Optional, TypeVar

from aware_meta.graph.support.member import T_Kind

# NOTE: Using General Ontology History Change type used by ALL AWARE CHANGES.
from aware_history_ontology.change.change_enums import ChangeType

# Type parameter for node kind
T_Entity = TypeVar("T_Entity")


@dataclass
class GraphNode(Generic[T_Entity, T_Kind]):
    """Represents a node in the tree with its entity, kind, operation, and children."""

    entity: T_Entity
    kind: T_Kind
    name: str
    operation: Optional[ChangeType] = None
    children: List[GraphNode[T_Entity, T_Kind]] = field(default_factory=list)

    def add_child(self, child: GraphNode[T_Entity, T_Kind]) -> None:
        """Add a child node."""
        self.children.append(child)

    @classmethod
    def from_entity(
        cls,
        entity: Any,
        kind: T_Kind,
        name: str,
        operation: Optional[ChangeType] = None,
    ) -> GraphNode[T_Entity, T_Kind]:
        """Create a node from an entity."""
        return cls(entity=entity, kind=kind, name=name, operation=operation)

    def get_all_nodes(self) -> List[GraphNode[T_Entity, T_Kind]]:
        """Get all nodes in the subtree (including self)."""
        nodes: list[GraphNode[T_Entity, T_Kind]] = [self]
        for child in self.children:
            nodes.extend(child.get_all_nodes())
        return nodes

    def has_changes(self) -> bool:
        """Check if this node or any of its descendants have changes."""
        if self.operation is not None:
            return True
        return any(child.has_changes() for child in self.children)
