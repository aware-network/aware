"""Interface for adapters that extract decorators from parsed code."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import override

# Kernel Graph Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter


class CodeSectionDecoratorAdapter(CodeNodeAdapter[T_Node], ABC):
    """
    Interface for decorator section adapters.

    Implementations will extract decorator-related information from language-specific
    parse trees while maintaining consistent positional information.
    """

    @property
    @override
    def section_type(self) -> CodeSectionType:
        """Return the type of section."""
        return CodeSectionType.decorator

    @abstractmethod
    def get_name(self, decorator_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        """
        Extract the name node from a decorator.

        Args:
            decorator_node: A node representing a decorator

        Returns:
            Node representing the decorator name
        """
        pass

    @abstractmethod
    def get_arguments(
        self, decorator_node: CodeNode[T_Node]
    ) -> Iterable[tuple[CodeNode[T_Node] | None, CodeNode[T_Node]]]:
        """
        Extract argument nodes from a decorator.

        Args:
            decorator_node: A node representing a decorator

        Returns:
            Iterable of nodes representing decorator arguments
        """
        pass

    @abstractmethod
    def get_target(self, decorator_node: CodeNode[T_Node]) -> CodeNode[T_Node] | None:
        """
        Extract the target node that the decorator is applied to.

        Args:
            decorator_node: A node representing a decorator

        Returns:
            Node representing the decorated entity or None if not found
        """
        pass

    @abstractmethod
    def get_target_type(self, decorator_node: CodeNode[T_Node]) -> str | None:
        """
        Determine the type of entity the decorator is applied to.

        Args:
            decorator_node: A node representing a decorator

        Returns:
            String representing the target type ("class", "function", etc.) or None if unknown
        """
        pass
