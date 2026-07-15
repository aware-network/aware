"""Interface for adapters that extract class information from parsed code."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import override

# Kernel Graph Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter


class CodeSectionClassAdapter(CodeNodeAdapter[T_Node], ABC):
    """
    Interface for class section adapters.

    Implementations will extract class-related information from language-specific
    parse trees while maintaining consistent positional information.
    """

    @property
    @override
    def section_type(self) -> CodeSectionType:
        """Return the type of section."""
        return CodeSectionType.class_

    @abstractmethod
    def get_name(self, class_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        """
        Extract the name node from a class definition.

        Args:
            class_node: A node representing a class definition

        Returns:
            Node representing the class name
        """
        pass

    @abstractmethod
    def get_attributes(self, class_node: CodeNode[T_Node]) -> Iterable[CodeNode[T_Node]]:
        """
        Extract attribute nodes from a class definition.

        Args:
            class_node: A node representing a class definition

        Returns:
            Iterable of nodes representing class attributes
        """
        pass

    @abstractmethod
    def get_methods(self, class_node: CodeNode[T_Node]) -> Iterable[CodeNode[T_Node]]:
        """
        Extract method nodes from a class definition.

        Args:
            class_node: A node representing a class definition

        Returns:
            Iterable of nodes representing class methods
        """
        pass

    def get_modifiers(self, _class_node: CodeNode[T_Node]) -> Iterable[CodeNode[T_Node]]:
        """
        Extract modifiers nodes from a class definition.

        Args:
            class_node: A node representing a class definition

        Returns:
            Iterable of nodes representing class modifiers
        """
        return []

    def get_keyword(self, _class_node: CodeNode[T_Node]) -> CodeNode[T_Node] | None:
        """
        Extract the keyword node from a class definition (e.g., 'class', 'type', 'edge').

        Args:
            class_node: A node representing a class definition

        Returns:
            Node representing the class keyword, or None if not present
        """
        return None

    def get_bases(self, _class_node: CodeNode[T_Node]) -> Iterable[CodeNode[T_Node]]:
        """
        Extract the base class nodes from a class definition.

        Args:
            class_node: A node representing a class definition

        Returns:
            Iterable of nodes representing the base classes
        """
        return []

    def get_annotations(self, _class_node: CodeNode[T_Node]) -> list[str] | None:
        """
        Return annotations associated with this class definition, if any.

        Default implementation returns None (no annotations).
        """
        return None

    def get_verb(self, _class_node: CodeNode[T_Node]) -> CodeNode[T_Node] | None:
        """
        Extract the verb/operator node (e.g., 'augment') from a class definition, if present.

        Args:
            class_node: A node representing a class definition

        Returns:
            Node representing the verb/operator or None if absent
        """
        return None

    def get_verb_target(self, _class_node: CodeNode[T_Node]) -> CodeNode[T_Node] | None:
        """Return the verb target (e.g., class being augmented), if any.

        Args:
            class_node: A node representing a class definition

        Returns:
            The verb target or None if absent
        """
        return None

    def is_augment(self, _class_node: CodeNode[T_Node]) -> bool:
        """
        Return True if this class definition should be treated as an augment/overlay.

        Default: False. Language adapters may override (e.g., Aware `augment`, Python mixins, etc.).
        """
        return False

    def is_edge(self, _class_node: CodeNode[T_Node]) -> bool:
        """
        Return True if this class definition should be treated as an edge object.

        Default: False. Language adapters may override (e.g., Aware `edge`, Python mixins, etc.).
        """
        return False

    def is_inline_value(self, _class_node: CodeNode[T_Node]) -> bool:
        """
        Return True if this class definition should be treated as an inline value type.

        Inline-value classes are SSOT type nodes but do not participate in the Object Instance Graph.
        They are serialized as inline payloads (e.g., function args/returns).

        Default: False. Language adapters may override (e.g., Aware `: inline_value`).
        """
        return False
