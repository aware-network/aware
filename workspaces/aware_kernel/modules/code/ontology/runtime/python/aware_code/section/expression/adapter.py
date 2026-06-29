"""Interface for adapters that extract expression information from parsed code."""

from abc import ABC, abstractmethod
from typing import override

from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.expression.code_section_expression_enums import (
    CodeSectionExpressionType,
)

from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter


class CodeSectionExpressionAdapter(CodeNodeAdapter[T_Node], ABC):
    """
    Interface for expression adapters.

    Implementations will extract expression-related information from language-specific
    parse trees while maintaining consistent positional information.
    """

    @property
    @override
    def section_type(self) -> CodeSectionType:
        """Return the type of section."""
        return CodeSectionType.expression

    @abstractmethod
    def classify(self, expression_node: CodeNode[T_Node]) -> CodeSectionExpressionType:
        """
        Classify the type of expression.

        Args:
            expression_node: A node representing an expression

        Returns:
            The type of expression (literal, identifier, call, etc.)
        """
        pass

    @override
    @abstractmethod
    def body_bytes(self, node: CodeNode[T_Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for the expression.

        This normalizes the expression to ensure consistent hashing
        regardless of whitespace or comment differences.

        Args:
            node: The expression node to get bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        pass
