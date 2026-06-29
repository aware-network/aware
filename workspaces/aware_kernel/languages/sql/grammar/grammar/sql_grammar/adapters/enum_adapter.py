"""SQL implementation of the CodeSectionEnumAdapter."""

from collections.abc import Iterable
import re

# Tree-sitter
from tree_sitter import Node, Query
from typing_extensions import override

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.enum.adapter import CodeSectionEnumAdapter

# Kernel Graph Ontology
from sql_grammar._tree_sitter_sql import SQL_LANGUAGE


# Logging
from aware_utils.logging import logger


class SQLEnumAdapter(CodeSectionEnumAdapter[Node]):
    """
    Implementation of CodeSectionEnumAdapter for SQL using Tree-sitter.

    Extracts enum definitions (CREATE TYPE AS ENUM) from SQL parse trees.
    """

    # Pre-compiled queries for better performance
    ENUM_QUERY: Query = SQL_LANGUAGE.query(
        """
        ((create_type                ; parent
            (keyword_enum))          ; child we need to see
        @create_enum)               ; capture the *create_type* node
        """
    )

    # Query to extract schema.enum_name structure
    SCHEMA_ENUM_NAME_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_type
          (object_reference
            (identifier) @schema_name
            .
            (identifier) @enum_name))
        """
    )

    # Query to extract just object reference
    ENUM_NAME_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_type
          (object_reference) @enum_name)
        """
    )

    # Query to extract enum elements container
    ENUM_ELEMENTS_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_type
          (enum_elements) @elements)
        """
    )

    # Query to extract individual enum values
    ENUM_VALUES_QUERY: Query = SQL_LANGUAGE.query(
        """
        (literal) @value
        """
    )

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a fully-qualified name for an SQL enum type.

        For SQL enums, this is typically schema.type_name

        Args:
            node: The enum node to get the qualified name for
            parent: Optional parent name (unused for SQL enums)

        Returns:
            Qualified name string for the enum
        """
        # Get the enum name node
        name_node = self.get_name(node)

        # Parse the name from the node text
        name_text = name_node.node_text()

        # For SQL enums, the name may include schema.type_name
        # Check if it has a schema prefix
        if "." in name_text:
            return name_text  # Already qualified

        # Default to public schema if no schema specified
        return f"public.{name_text}" if name_text else f"enum@{node.byte_start}"

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for an SQL enum definition.

        This strips comments and normalizes whitespace to create a consistent
        hash regardless of formatting changes.

        Args:
            node: The enum node to get body bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        # Extract the node's bytes
        node_bytes = source[node.byte_start:node.byte_end]

        # Remove SQL comments
        normalized = re.sub(
            b"--.*?$|/\\*.*?\\*/",  # Remove single-line and multi-line comments
            b"",  # Replace with empty string
            node_bytes,  # Input
            flags=re.MULTILINE | re.DOTALL,  # Multi-line mode
        )

        # Normalize whitespace
        normalized = re.sub(b"\\s+", b" ", normalized)

        # Remove trailing/leading whitespace
        normalized = normalized.strip()

        return normalized

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        """Return a language-specific reference like 'public.permission' or None."""
        return self.qualname(node, parent)

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all CREATE TYPE AS ENUM statements in the SQL.

        Args:
            root: The root node of the parse tree
            source: The SQL source code as bytes

        Returns:
            Iterable of nodes representing enum definitions
        """
        captures = self.ENUM_QUERY.captures(root)
        if "create_enum" in captures:
            for enum_node in captures["create_enum"]:
                yield CodeNode(node=enum_node, byte_start=enum_node.start_byte, byte_end=enum_node.end_byte)

    @override
    def get_name(self, enum_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the enum name from a CREATE TYPE AS ENUM statement.
        Returns only the type name part (without schema).

        Args:
            enum_node: Node representing a CREATE TYPE AS ENUM statement

        Returns:
            Node representing the enum name
        """
        # Try to find schema.enum_name structure first
        schema_captures = self.SCHEMA_ENUM_NAME_QUERY.captures(enum_node.node)
        if "enum_name" in schema_captures and schema_captures["enum_name"]:
            name_node = schema_captures["enum_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # If no schema.enum_name structure, try to find just the object reference
        captures = self.ENUM_NAME_QUERY.captures(enum_node.node)
        if "enum_name" in captures and captures["enum_name"]:
            obj_ref_node = captures["enum_name"][0]

            # Try to find the last identifier in the object reference (the enum name)
            for child in reversed(list(obj_ref_node.children)):
                if child.type == "identifier":
                    return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

            # If no identifier children, return the whole object reference
            return CodeNode(node=obj_ref_node, byte_start=obj_ref_node.start_byte, byte_end=obj_ref_node.end_byte)

        # Fallback
        logger.warning(f"Could not find name in enum definition, raw text: {enum_node.node_text()}")
        return CodeNode(node=enum_node.node, byte_start=enum_node.byte_start, byte_end=enum_node.byte_start)

    @override
    def get_values(self, enum_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract enum values from a CREATE TYPE AS ENUM statement.

        Args:
            enum_node: Node representing a CREATE TYPE AS ENUM statement

        Returns:
            Iterable of nodes representing enum values
        """
        # Find the enum_elements node which contains the values
        captures = self.ENUM_ELEMENTS_QUERY.captures(enum_node.node)
        if "elements" not in captures or not captures["elements"]:
            return

        elements_node = captures["elements"][0]

        # Now get the individual literal values
        value_captures = self.ENUM_VALUES_QUERY.captures(elements_node)
        if "value" in value_captures:
            for value_node in value_captures["value"]:
                yield CodeNode(node=value_node, byte_start=value_node.start_byte, byte_end=value_node.end_byte)
