from dataclasses import dataclass
from typing import Any, Generic, Mapping, Protocol, TypeVar
from uuid import UUID

from aware_history_ontology.change.change_enums import ChangeType

from aware_meta.graph.support.member import GraphMember, T_Kind
from aware_meta.graph.support.protocols.diff.container import TreeContainer


class GraphDiffProtocol(Protocol):
    """Protocol for graph diff operations (tree annotations / operations)."""

    def add_graph_specific_children_fn(self, graph: GraphMember[T_Kind], root: TreeContainer[T_Kind]) -> None:
        """Add graph-specific children to the root container if function provided."""
        ...

    def get_create_operation(self) -> Any:
        """Get the CREATE operation for this graph type."""
        ...

    def get_update_operation(self) -> Any:
        """Get the UPDATE operation for this graph type."""
        ...

    def get_delete_operation(self) -> Any:
        """Get the DELETE operation for this graph type."""
        ...


T_CHANGE = TypeVar("T_CHANGE")


@dataclass(frozen=True)
class FieldChange:
    """
    Lightweight descriptor for a single field-level change.

    This keeps the generic diff layer decoupled from the canonical ChangeDelta
    history model. Graph-specific change builders can translate these into
    typed ChangeDelta instances (or other envelopes) as needed.
    """

    property: str
    old_value: Any
    new_value: Any


class GraphChangeProtocol(Protocol, Generic[T_Kind, T_CHANGE]):
    """
    Protocol for materializing domain change objects from diff nodes.

    This is intentionally separate from GraphMember so that membership remains a
    pure view (identity/path/content) and change construction lives at the
    graph/protocol layer.
    """

    def build_node_change(
        self,
        member: GraphMember[T_Kind],
        stable_id: UUID,
        operation: ChangeType,
        child_changes: Mapping[T_Kind, list[Any]],
        field_changes: list[FieldChange],
    ) -> T_CHANGE | None:
        """
        Build a change object for a single node.

        Args:
            member:   The GraphMember representing the node.
            stable_id: Stable UUID as determined by the reconciler.
            operation: CREATE / UPDATE / DELETE.
            child_changes: Already-materialized child changes grouped by kind.
            field_diffs: Field-level diffs for this node.

        Returns:
            A domain-specific change object, or None if this node should not
            emit a change at this level.
        """
        ...


__all__ = ["GraphDiffProtocol", "GraphChangeProtocol", "FieldChange", "T_CHANGE"]
