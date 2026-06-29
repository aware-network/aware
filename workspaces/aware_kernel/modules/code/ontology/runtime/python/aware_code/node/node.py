"""Abstract representation of parsed code nodes."""

from __future__ import annotations

from typing import Generic, TypeVar, cast

T_Node = TypeVar("T_Node")  # concrete CST node type (LibCST.CSTNode, TSNode, etc.)


class CodeNode(Generic[T_Node]):
    """
    Abstraction over different parser node implementations.

    Provides a consistent interface regardless of whether the underlying
    parser is Tree-sitter, LibCST, or something else.
    """

    # The wrapped native node from the parser
    node: T_Node

    # Positional information guaranteed by all adapters
    byte_start: int
    byte_end: int

    def __init__(self, node: T_Node, byte_start: int, byte_end: int) -> None:
        """
        Initialize a CodeNode.

        Args:
            node: The native parser node
            byte_start: The starting byte position in the source
            byte_end: The ending byte position in the source
        """
        self.node = node
        self.byte_start = byte_start
        self.byte_end = byte_end

    def node_text(self) -> str:
        """
        Get the text represented by this node.
        """
        from tree_sitter import Node

        if isinstance(self.node, Node):
            if not self.node.text:
                raise ValueError(f"Node {self.node} has no text")
            return self.node.text.decode("utf-8")
        raise ValueError(f"Node type {type(self.node)} does not support text attribute")

    def text(self, source: bytes) -> bytes:
        """
        Extract the text represented by this node from the source.

        Args:
            source: The complete source code as bytes

        Returns:
            The bytes representing this node
        """
        return source[self.byte_start : self.byte_end]

    def detach_node(self) -> T_Node:
        """
        Temporarily detach the parser node for safe copying.

        Returns:
            The detached parser node, or None if no node was attached
        """
        node = self.node
        self.node = cast(T_Node, None)
        return node

    def restore_node(self, node: T_Node) -> None:
        """
        Restore a previously detached parser node.

        Args:
            node: The parser node to restore
        """
        self.node = node
