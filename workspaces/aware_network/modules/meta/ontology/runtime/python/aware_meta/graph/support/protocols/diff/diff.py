"""Generic tree-based diff implementation."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Mapping, Optional, TypeVar, Union

# History operations
from aware_history_ontology.change.change_enums import ChangeType

# Index
from aware_meta.graph.support.index import GraphIndex, build_index

# Node
from aware_meta.graph.support.node import GraphNode

# Member
from aware_meta.graph.support.member import GraphMember, T_Kind
from aware_meta.graph.support.topology import GraphTopology

# Diff
from aware_meta.graph.support.protocols.diff.container import TreeContainer
from aware_meta.graph.support.protocols.diff.protocol import (
    FieldChange,
    GraphChangeProtocol,
    GraphDiffProtocol,
)

# Reconciler
from aware_meta.graph.support.protocols.reconcile.index_builder import build_reconciler
from aware_meta.graph.support.protocols.reconcile.reconciler import (
    GraphReconciler,
    FingerprintContext,
)

# Logging
from aware_utils.logging import logger


# Type parameters
T_CHANGE = TypeVar("T_CHANGE")  # Change type

Normalizer = Callable[
    [GraphMember[T_Kind], GraphMember[T_Kind]],
    tuple[GraphMember[T_Kind], GraphReconciler[T_Kind]],
]


def diff(
    old_graph: GraphMember[T_Kind],
    new_graph: GraphMember[T_Kind],
    protocol: GraphDiffProtocol,
    topology: GraphTopology[T_Kind],
    change_protocol: GraphChangeProtocol[T_Kind, T_CHANGE],
) -> list[T_CHANGE]:
    """
    Perform the tree-based diff and return a list of change objects.
    """
    # !! TODO: Optionally maintain indexes externally to avoid recomputing.
    old_index = build_index(old_graph, topology)
    new_index = build_index(new_graph, topology)

    reconciler_index = build_reconciler(old_index, new_index)
    reconciler = GraphReconciler[T_Kind](reconciler_index)

    # Build trees from both graphs
    old_tree = build_tree_from_graph(old_index, old_graph, protocol)
    new_tree = build_tree_from_graph(new_index, new_graph, protocol)

    # Annotate the new tree with operations
    annotate_children_with_operations(old_tree.children, new_tree, reconciler, protocol)

    # Build changes from the annotated tree
    changes = build_changes_from_tree(old_index, reconciler, new_tree, change_protocol)

    return changes


def materialize_change(
    old_index: GraphIndex[T_Kind],
    reconciler: GraphReconciler[T_Kind],
    node: GraphNode,
    change_protocol: GraphChangeProtocol[T_Kind, T_CHANGE],
) -> Optional[T_CHANGE]:
    """Materialize a change object for a node using depth-first traversal."""
    member = node.entity
    stable_id = reconciler.get_stable_id(member)

    # ---- Recurse first (depth-first) to gather child changes ----
    grouped_children: Mapping[Any, list[Any]] = defaultdict(list)
    for child in node.children:
        child_change = materialize_change(old_index, reconciler, child, change_protocol)
        if child_change:
            grouped_children[child.kind].append(child_change)

    # If no explicit operation but children changed, treat as UPDATE
    if node.operation is None:
        if any(grouped_children.values()):
            operation = ChangeType.update
        else:
            return None
    else:
        # Node.operation is already a ChangeType (set during annotation).
        if node.operation not in (
            ChangeType.create,
            ChangeType.update,
            ChangeType.delete,
        ):
            return None
        operation = node.operation

    # ---- Field-level diffs ----
    field_changes: list[FieldChange] = []
    if operation in (ChangeType.create, ChangeType.update):
        old_member: GraphMember[T_Kind] | None = None
        if operation == ChangeType.update:
            # Prefer fast lookup via stable ID / primary ID when available.
            # This avoids O(N^2) scans over the old index for large graphs.
            if stable_id is not None:
                old_member = old_index.get_entity_by_id(stable_id)  # type: ignore[attr-defined]
            # Fallback to fingerprint-based scan only when direct lookup fails.
            if old_member is None:
                for path, (entity, kind) in old_index.get_all_paths().items():
                    if reconciler.same(entity, member):
                        old_member = entity  # type: ignore[assignment]
                        break

        # content fields are defined by GraphMember implementations
        new_content = member.get_content_fields()
        old_content: Mapping[str, Any] = old_member.get_content_fields() if old_member else {}

        for field_name, new_value in new_content.items():
            old_value = old_content.get(field_name)
            if old_value != new_value:
                field_changes.append(
                    FieldChange(
                        property=field_name,
                        old_value=old_value,
                        new_value=new_value,
                    )
                )

    # ---- Delegate to domain object via change protocol ----
    entity_change = change_protocol.build_node_change(
        member=member,
        stable_id=stable_id,
        operation=operation,
        child_changes=grouped_children,
        field_changes=field_changes,
    )

    return entity_change


def build_tree_from_graph(
    index: GraphIndex[T_Kind],
    graph: GraphMember[T_Kind],
    protocol: GraphDiffProtocol,
) -> TreeContainer[T_Kind]:
    """Build a tree representation from a graph."""

    # Create a root container - no specific node kind needed
    root = TreeContainer(entity=graph, name="root")

    # Create a mapping from entity ID to node for efficient lookups
    entity_id_to_node: dict[str, GraphNode] = {}

    # Get all paths and build nodes
    for path, (entity, kind) in index.get_all_paths().items():
        if not path:  # Skip empty path (root)
            # Skip empty path (root)
            continue

        # Create node for this entity
        node = GraphNode.from_entity(entity=entity, kind=kind, name=path[-1])
        entity_id = str(id(entity))
        entity_id_to_node[entity_id] = node

        # Find parent node and add this node as a child
        if len(path) == 1:
            # Direct child of root container
            # Direct child of root container
            root.children.append(node)
        else:
            # Find parent by traversing the path
            parent_path = path[:-1]
            parent_entity = index.get_entity_at_path(parent_path)
            if parent_entity:
                parent_id = str(id(parent_entity))
                if parent_id in entity_id_to_node:
                    # Add as child of parent
                    entity_id_to_node[parent_id].children.append(node)
                else:
                    logger.error(f"Parent node not found in mapping: {parent_id} for {parent_path}")
            else:
                logger.error(f"Parent entity not found: {parent_path}")

    # Add graph-specific children (e.g., relationships for ObjectConfigGraph)
    protocol.add_graph_specific_children_fn(graph, root)

    return root


def annotate_children_with_operations(
    old_children: list[GraphNode],
    new_parent: Union[TreeContainer[T_Kind], GraphNode],
    reconciler: GraphReconciler[T_Kind],
    protocol: GraphDiffProtocol,
) -> bool:
    """
    Annotate children with operations by comparing old and new children.
    Works for both TreeContainer and GraphNode parents.
    """
    has_changes = False

    # Get new children based on parent type
    if isinstance(new_parent, TreeContainer):
        new_children = new_parent.children
    else:
        new_children = new_parent.children

    # Create mappings of old children by kind and entity for efficient lookup
    old_children_by_kind: dict[Any, list[GraphNode]] = {}
    for child in old_children:
        old_children_by_kind.setdefault(child.kind, []).append(child)

    # Process each child in the new tree
    for new_child in new_children:
        old_child = None

        # Find matching child in old tree
        candidates = old_children_by_kind.get(new_child.kind, [])

        for candidate in candidates:
            if reconciler.same(candidate.entity, new_child.entity, FingerprintContext.RECONCILIATION):
                old_child = candidate
                old_children_by_kind[new_child.kind].remove(candidate)
                break

        if old_child:
            # Entity exists in both trees, check for changes
            # Use content comparison to check if entities have actually changed
            entities_are_same = reconciler.same(old_child.entity, new_child.entity, FingerprintContext.CONTENT)

            if entities_are_same:
                # Entity hasn't changed at this level, but check children
                child_has_changes = annotate_children_with_operations(
                    old_child.children,
                    new_child,
                    reconciler,
                    protocol,
                )
                if child_has_changes:
                    new_child.operation = ChangeType.update
                    has_changes = True
                else:
                    new_child.operation = None  # No operation needed
            else:
                # Entity has changed
                new_child.operation = ChangeType.update
                has_changes = True
                # Still need to check children
                annotate_children_with_operations(old_child.children, new_child, reconciler, protocol)
        else:
            # New entity, mark as CREATE
            new_child.operation = ChangeType.create
            has_changes = True
            # Mark all descendants as CREATE
            mark_all_descendants(new_child, ChangeType.create)

    # Handle deleted entities (exist in old but not in new)
    for kind_children in old_children_by_kind.values():
        for old_child in kind_children:
            # Create a ghost node for the deleted entity
            ghost_node = GraphNode.from_entity(
                entity=old_child.entity,
                kind=old_child.kind,
                name=old_child.name,
                operation=ChangeType.delete,
            )
            # Copy the structure for proper deletion handling
            copy_tree_structure(old_child, ghost_node)
            mark_all_descendants(ghost_node, ChangeType.delete)

            # Add to appropriate parent
            if isinstance(new_parent, TreeContainer):
                new_parent.add_child(ghost_node)
            else:
                new_parent.add_child(ghost_node)
            has_changes = True

    # If any descendant changed and parent is a concrete graph node, mark parent as UPDATE
    if has_changes and isinstance(new_parent, GraphNode):
        if new_parent.operation is None:
            new_parent.operation = ChangeType.update

    return has_changes


def mark_all_descendants(node: GraphNode, operation: Any) -> None:
    """Mark a node and all its descendants with the given operation."""
    node.operation = operation
    for child in node.children:
        mark_all_descendants(child, operation)


def copy_tree_structure(source: GraphNode, target: GraphNode) -> None:
    """Copy the tree structure from source to target."""
    for child in source.children:
        child_copy = GraphNode.from_entity(
            entity=child.entity,
            kind=child.kind,
            name=child.name,
            operation=child.operation,
        )
        target.add_child(child_copy)
        copy_tree_structure(child, child_copy)


def build_changes_from_tree(
    old_index: GraphIndex[T_Kind],
    reconciler: GraphReconciler[T_Kind],
    tree: TreeContainer[T_Kind],
    change_protocol: GraphChangeProtocol[T_Kind, T_CHANGE],
) -> list[T_CHANGE]:
    """Build change objects from the annotated tree."""
    changes: list[T_CHANGE] = []

    # Process only root-level entities that have changes
    for child in tree.children:
        if child.operation is not None:
            change = materialize_change(old_index, reconciler, child, change_protocol)
            if change:
                changes.append(change)

    return changes
