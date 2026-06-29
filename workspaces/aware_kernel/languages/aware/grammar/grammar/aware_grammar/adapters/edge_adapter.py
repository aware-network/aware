"""Aware implementation of the CodeSectionClassAdapter for Edge"""

from collections.abc import Iterable
import re
from typing_extensions import override
from typing import final

# Tree-sitter
from tree_sitter import Node
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_code.node.node import CodeNode
from aware_code.section.class_.adapter import CodeSectionClassAdapter


@final
class AwareEdgeAdapter(CodeSectionClassAdapter[Node]):
    """
    Adapter for Aware edge definitions.

    Maps to a classical CodeSectionClass to allow relationships as first class members specializations.
    """

    # Pre-compiled queries
    EDGE_QUERY = AWARE_LANGUAGE.query(
        """
        (edge_def) @edge
        """
    )

    EDGE_NAME_QUERY = AWARE_LANGUAGE.query(
        """
        (edge_def
          name: (ident) @edge_name)
        """
    )

    ATTRIBUTE_QUERY = AWARE_LANGUAGE.query(
        """
        (edge_def
          (attr_def) @attr)
        """
    )

    # Add new query for edge modifiers
    EDGE_MODS_QUERY = AWARE_LANGUAGE.query(
        """
        (edge_def
          modifiers: (edge_mods
            (class_attr) @edge_attr))
        """
    )

    EDGE_FN_QUERY = AWARE_LANGUAGE.query(
        """
        (edge_def
          (fn_def) @function)
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all edge definitions in the Aware source.

        Args:
            root: The root node of the parse tree
            source: The source code as bytes

        Returns:
            Iterable of nodes representing edge definitions
        """
        # Use pre-compiled query
        captures = self.EDGE_QUERY.captures(root)
        if "edge" in captures:
            for edge_node in captures["edge"]:
                yield CodeNode(node=edge_node, byte_start=edge_node.start_byte, byte_end=edge_node.end_byte)

    @override
    def get_name(self, class_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the edge name from an edge definition.

        Args:
            class_node: Node representing an edge definition

        Returns:
            Node representing the edge name
        """
        # Use pre-compiled query
        captures = self.EDGE_NAME_QUERY.captures(class_node.node)
        if "edge_name" in captures and captures["edge_name"]:
            name_node = captures["edge_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # Fallback - should not happen with valid syntax
        raise ValueError("No edge name found in edge definition")

    @override
    def get_attributes(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract field definitions from an edge definition.

        Args:
            class_node: Node representing an edge definition

        Returns:
            Iterable of nodes representing field definitions
        """
        # Use pre-compiled query
        captures = self.ATTRIBUTE_QUERY.captures(class_node.node)
        for attr_node in captures.get("attr", []):
            yield CodeNode(node=attr_node, byte_start=attr_node.start_byte, byte_end=attr_node.end_byte)

    @override
    def get_methods(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract function definitions as methods.

        Args:
            class_node: Node representing a type definition

        Returns:
            Iterable of nodes representing function definitions
        """
        # Use pre-compiled query
        captures = self.EDGE_FN_QUERY.captures(class_node.node)
        if "function" in captures:
            for fn_node in captures["function"]:
                yield CodeNode(node=fn_node, byte_start=fn_node.start_byte, byte_end=fn_node.end_byte)

    @override
    def get_modifiers(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract modifiers from an edge definition.

        Args:
            class_node: Node representing an edge definition

        Returns:
            List of modifier strings
        """
        captures = self.EDGE_MODS_QUERY.captures(class_node.node)
        if "edge_attr" in captures:
            for mod_node in captures["edge_attr"]:
                yield CodeNode(node=mod_node, byte_start=mod_node.start_byte, byte_end=mod_node.end_byte)

    @override
    def get_keyword(self, class_node: CodeNode[Node]) -> CodeNode[Node] | None:
        """
        Extract the 'edge' keyword node from an edge definition.

        Args:
            class_node: Node representing an edge definition

        Returns:
            Node representing the 'edge' keyword
        """
        # The first child of an edge_def should be the 'edge' keyword
        for child in class_node.node.children:
            if child.type == "edge":
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
        return None

    @override
    def get_bases(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract base class nodes from an edge definition.

        Aware language doesn't support base classes.

        Args:
            class_node: Node representing an edge definition

        Returns:
            Empty iterable since Aware doesn't support base classes
        """
        return []

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a fully-qualified name for an Aware edge.

        Args:
            node: The edge node to get the qualified name for
            parent: Optional parent namespace

        Returns:
            Qualified name string
        """
        # Get edge name
        name_node = self.get_name(node)
        name_text = name_node.node_text()

        # If we have a parent namespace, prepend it
        if parent:
            return f"{parent}.{name_text}"

        return name_text

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for an Aware edge definition.

        This strips comments and normalizes whitespace.

        Args:
            node: The edge node to get body bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        # Extract the node's bytes
        node_bytes = source[node.byte_start:node.byte_end]

        # Remove comments
        normalized = re.sub(
            b"//[^\n]*",  # Remove single-line comments
            b"",  # Replace with empty string
            node_bytes,  # Input
            flags=re.MULTILINE,  # Multi-line mode
        )

        # Normalize whitespace
        normalized = re.sub(b"\\s+", b" ", normalized)

        # Remove trailing/leading whitespace
        normalized = normalized.strip()

        return normalized

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        """
        Return a reference string for this edge that can be used to match comments.

        Args:
            node: The edge node
            parent: Optional parent context

        Returns:
            Reference string for comment matching
        """
        # Delegate to qualname method for consistent lookup keys
        return self.qualname(node, parent)
