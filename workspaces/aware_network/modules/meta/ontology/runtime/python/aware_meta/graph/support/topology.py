"""Topology protocols for graph traversal.

`GraphMember` describes the *view* of a single node (identity, path, content),
while `GraphTopology` describes how nodes are connected into a graph or tree.

This separation keeps membership (identity/diff) orthogonal to traversal
strategy, and allows different graphs to supply custom topologies without
teaching `GraphMember` how to walk the underlying ORM models.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Protocol, Generic

from aware_meta.graph.support.member import GraphMember, T_Kind


class GraphTopology(Protocol, Generic[T_Kind]):
    """Protocol for traversing a graph of GraphMembers."""

    def get_children(
        self,
        parent: GraphMember[T_Kind],
    ) -> Mapping[T_Kind, Iterable[GraphMember[T_Kind]]]:
        """
        Return logical children for a given parent node, grouped by kind.

        Implementations are free to:
        - Reuse existing member instances or construct them on demand.
        - Consult additional context (e.g., indexes) to shape the tree.
        """
        ...


__all__ = ["GraphTopology"]
