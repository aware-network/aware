from dataclasses import dataclass, field
from typing import Any, Generic, Union

from aware_meta.graph.support.node import GraphNode
from aware_meta.graph.support.member import T_Kind


# TODO: CLARIFY IF REQUIRED


@dataclass
class TreeContainer(Generic[T_Kind]):
    """Simple container for the root of the tree - doesn't need a specific node kind."""

    entity: Any
    name: str
    children: list[GraphNode] = field(default_factory=list)

    def add_child(self, child: GraphNode) -> None:
        """Add a child node."""
        self.children.append(child)


# Union type for tree nodes - can be either a container (root) or a regular node
TreeNode = Union[TreeContainer[T_Kind], GraphNode]
