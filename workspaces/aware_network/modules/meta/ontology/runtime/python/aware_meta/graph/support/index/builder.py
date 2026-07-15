from aware_meta.graph.support.member import GraphMember, T_Kind
from aware_meta.graph.support.index.index import GraphIndex
from aware_meta.graph.support.topology import GraphTopology


def build_index(root: GraphMember[T_Kind], topology: GraphTopology[T_Kind]) -> GraphIndex[T_Kind]:
    """
    Build the index for the graph.
    """
    index = GraphIndex[T_Kind]()
    walk(index, topology, root, ())
    return index


def walk(
    index: GraphIndex[T_Kind],
    topology: GraphTopology[T_Kind],
    node: GraphMember[T_Kind],
    parent_path: tuple[str, ...],
) -> None:
    """
    Recursively walk the graph building the index.

    Uses GraphMember protocol methods for traversal.
    """
    local = node.get_path_key()
    path = parent_path + (local,)
    index.add(node, path, node.node_kind())

    # Recursively index children via topology
    for kind, children in topology.get_children(node).items():
        for child in children:
            walk(index, topology, child, path)
