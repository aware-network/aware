"""Aware implementation of the CodeSectionEnumAdapter."""

from collections.abc import Iterable
import re
from typing_extensions import override
from typing import final

# Tree-sitter
from tree_sitter import Node
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

# Aware Primitive Code
from aware_code.section.enum.adapter import CodeSectionEnumAdapter
from aware_code.node.node import CodeNode


@final
class AwareEnumAdapter(CodeSectionEnumAdapter[Node]):
    """
    Implementation of CodeSectionEnumAdapter for Aware language using Tree-sitter.

    Maps 'enum' definitions in Aware to enum sections.
    """

    # Pre-compiled queries
    ENUM_QUERY = AWARE_LANGUAGE.query(
        """
        (enum_def) @enum
        """
    )

    ENUM_NAME_QUERY = AWARE_LANGUAGE.query(
        """
        (enum_def
          name: (ident) @enum_name)
        """
    )

    ENUM_VALUE_QUERY = AWARE_LANGUAGE.query(
        """
        (enum_value_def
          name: (ident) @value_name
          value: (literal)? @value)
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all enum definitions in the Aware source.

        Args:
            root: The root node of the parse tree
            source: The source code as bytes

        Returns:
            Iterable of nodes representing enum definitions
        """
        captures = self.ENUM_QUERY.captures(root)
        if "enum" in captures:
            for enum_node in captures["enum"]:
                yield CodeNode(node=enum_node, byte_start=enum_node.start_byte, byte_end=enum_node.end_byte)

    @override
    def get_name(self, enum_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the enum name from an enum definition.

        Args:
            enum_node: Node representing an enum definition

        Returns:
            Node representing the enum name
        """
        captures = self.ENUM_NAME_QUERY.captures(enum_node.node)
        if "enum_name" in captures and captures["enum_name"]:
            name_node = captures["enum_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # Fallback - should not happen with valid syntax
        raise ValueError("No enum name found in enum definition")

    @override
    def get_values(self, enum_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract enum values from an enum definition.

        Args:
            enum_node: Node representing an enum definition

        Returns:
            Iterable of nodes representing enum values
        """
        captures = self.ENUM_VALUE_QUERY.captures(enum_node.node)
        if "value_name" in captures:
            for value_node in captures["value_name"]:
                yield CodeNode(node=value_node, byte_start=value_node.start_byte, byte_end=value_node.end_byte)

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a fully-qualified name for an Aware enum.

        Args:
            node: The enum node to get the qualified name for

        Returns:
            Qualified name string
        """
        name_node = self.get_name(node)
        name_text = name_node.node_text()
        return name_text

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for an Aware enum definition.

        This strips comments and normalizes whitespace.

        Args:
            node: The enum node to get body bytes for
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
        Return a reference string for this enum that can be used to match comments.

        Args:
            node: The enum node
            parent: Optional parent context

        Returns:
            Reference string for comment matching
        """
        # Delegate to qualname method for consistent lookup keys
        return self.qualname(node, parent)
