"""Python implementation of the CodeSectionExpressionAdapter."""

from __future__ import annotations
import re
from collections.abc import Iterable
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node

# Aware Kernel Graph Ontology
from aware_code_ontology.expression.code_section_expression_enums import (
    CodeSectionExpressionType,
)

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.expression.adapter import CodeSectionExpressionAdapter


class PythonExpressionAdapter(CodeSectionExpressionAdapter[Node]):
    """
    Implementation of CodeSectionExpressionAdapter for Python using Tree-sitter.

    Classifies Python expressions and extracts their normalized bytes.
    """

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find expression nodes in the Python source code.

        Note: This is typically not called directly since expressions are usually
        extracted by other adapters (decorators, assignments, etc.) and passed
        to the expression builder.

        Args:
            root: The root node of the parse tree
            source: The Python source code as bytes

        Returns:
            Empty iterable since expressions are handled by other adapters
        """
        # Expressions are typically extracted by other adapters (decorators, etc.)
        # so this method returns nothing when called directly
        return iter([])

    @override
    def classify(self, expression_node: CodeNode[Node]) -> CodeSectionExpressionType:
        """
        Classify the type of Python expression.

        Args:
            expression_node: A node representing a Python expression

        Returns:
            The type of expression (literal, identifier, call)
        """
        node_type = expression_node.node.type

        # Literal types
        if node_type in {"string", "integer", "float", "true", "false", "none", "list", "dictionary", "set"}:
            return CodeSectionExpressionType.literal

        # Identifier types (names and attribute access)
        if node_type in {"identifier", "attribute"}:
            return CodeSectionExpressionType.identifier

        # Call expressions
        if node_type == "call":
            return CodeSectionExpressionType.call

        # Default fallback for other expression types
        # (binary_operator, unary_operator, lambda, comprehensions, etc.)
        return CodeSectionExpressionType.literal

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for a Python expression.

        This normalizes the expression to ensure consistent hashing
        regardless of whitespace or comment differences.

        Args:
            node: The expression node to get bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        # Extract the node's bytes
        node_bytes = source[node.byte_start:node.byte_end]

        # Remove Python comments
        normalized = re.sub(
            b"#.*?$",  # Remove single-line comments
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
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a qualified name for a Python expression.

        Args:
            node: The expression node to get the qualified name for
            parent: Optional parent name to prepend

        Returns:
            Qualified name string
        """
        # For expressions, we use a simple naming scheme based on type and position
        expr_type = self.classify(node)
        base_name = f"{expr_type.value}@{node.byte_start}"

        if parent:
            return f"{parent}.{base_name}"

        return base_name
