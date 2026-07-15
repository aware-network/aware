"""Interface for adapters that extract enum information from parsed code."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import override

from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter


class CodeSectionEnumAdapter(CodeNodeAdapter[T_Node], ABC):
    """
    Interface for enum adapters.

    Implementations will extract enum-related information from language-specific
    parse trees while maintaining consistent positional information.
    """

    @property
    @override
    def section_type(self) -> CodeSectionType:
        """Return the type of section."""
        return CodeSectionType.enum

    @abstractmethod
    def get_name(self, enum_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        """
        Extract the name node from an enum definition.

        Args:
            enum_node: A node representing an enum definition

        Returns:
            Node representing the enum name
        """
        pass

    @abstractmethod
    def get_values(self, enum_node: CodeNode[T_Node]) -> Iterable[CodeNode[T_Node]]:
        """
        Extract value nodes from an enum definition.

        Args:
            enum_node: A node representing an enum definition

        Returns:
            Iterable of nodes representing enum values
        """
        pass
