"""Interface for adapters that extract attribute information from parsed code."""

from abc import ABC, abstractmethod
from typing import override

from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter


class CodeSectionAttributeAdapter(CodeNodeAdapter[T_Node], ABC):
    """
    Interface for attribute section adapters.

    Implementations will extract attribute-related information from language-specific
    parse trees while maintaining consistent positional information.
    """

    @property
    @override
    def section_type(self) -> CodeSectionType:
        """Return the type of section."""
        return CodeSectionType.attribute

    @override
    def qualname(self, node: CodeNode[T_Node], parent: str | None = None) -> str:
        """
        Return a fully-qualified name for non-parameter attributes.

        This keeps compatibility with the generic CodeNodeAdapter contract while
        attribute builders can use `qualname_for_role` when parameter context matters.
        """
        return self.qualname_for_role(node, is_parameter=False, parent=parent)

    @abstractmethod
    def qualname_for_role(self, node: CodeNode[T_Node], is_parameter: bool, parent: str | None = None) -> str:
        """
        Return a fully-qualified name for an attribute or parameter.

        Args:
            node: The node to get the qualified name for
            is_parameter: Flag indicating if this is a parameter (vs attribute)
            parent: Optional parent name to prepend
        """
        pass

    @override
    def reference_string(self, node: CodeNode[T_Node], parent: str | None = None) -> str | None:
        """
        Return a reference string for non-parameter attributes.
        """
        return self.reference_string_for_role(node, is_parameter=False, parent=parent)

    def reference_string_for_role(
        self,
        node: CodeNode[T_Node],
        is_parameter: bool,
        parent: str | None = None,
    ) -> str | None:
        """
        Return a reference string for an attribute or parameter.
        """
        _ = (node, is_parameter, parent)
        return None

    @abstractmethod
    def get_name(self, attribute_node: CodeNode[T_Node], is_parameter: bool) -> CodeNode[T_Node]:
        """
        Extract the name node from an attribute definition.

        Args:
            attribute_node: A node representing an attribute definition
            is_parameter: Flag indicating if this is a parameter (vs column)

        Returns:
            Node representing the attribute name
        """
        pass

    @abstractmethod
    def get_type(self, attribute_node: CodeNode[T_Node], is_parameter: bool) -> CodeNode[T_Node] | None:
        """
        Extract the type node from an attribute definition.

        Args:
            attribute_node: A node representing an attribute definition
            is_parameter: Flag indicating if this is a parameter (vs column)

        Returns:
            Node representing the attribute type
        """
        pass

    @abstractmethod
    def get_default_value(self, attribute_node: CodeNode[T_Node], is_parameter: bool) -> CodeNode[T_Node] | None:
        """
        Extract the default value node from an attribute definition if present.

        Args:
            attribute_node: A node representing an attribute definition
            is_parameter: Flag indicating if this is a parameter (vs column)

        Returns:
            Node representing the default value if present, None otherwise
        """
        pass

    @abstractmethod
    def is_required(self, attribute_node: CodeNode[T_Node], is_parameter: bool) -> bool:
        """
        Check if an attribute is required (not nullable).

        Args:
            attribute_node: A node representing an attribute definition
            is_parameter: Flag indicating if this is a parameter (vs column)

        Returns:
            True if the attribute is required, False otherwise
        """
        pass

    @abstractmethod
    def has_unique(self, attribute_node: CodeNode[T_Node], is_parameter: bool) -> bool:
        """
        Check if an attribute has a unique constraint.

        Args:
            attribute_node: A node representing an attribute definition
            is_parameter: Flag indicating if this is a parameter (vs column)

        Returns:
            True if the attribute has a unique constraint, False otherwise
        """
        pass

    @abstractmethod
    def is_primary(self, attribute_node: CodeNode[T_Node], is_parameter: bool) -> bool:
        """
        Check if an attribute is a primary key.

        Args:
            attribute_node: A node representing an attribute definition
            is_parameter: Flag indicating if this is a parameter (vs column)

        Returns:
            True if the attribute is a primary key, False otherwise
        """
        pass

    def is_public(self, _attribute_node: CodeNode[T_Node], _is_parameter: bool) -> bool:
        """
        Check if an attribute is public (vs private/protected).

        NOTE: By default returns True as some programming languages do not have a concept of public/private attributes.

        Args:
            attribute_node: A node representing an attribute definition
            is_parameter: Flag indicating if this is a parameter (vs column)

        Returns:
            True if the attribute is public, False if private/protected
        """
        return True

    def get_annotations(self, _attribute_node: CodeNode[T_Node], _is_parameter: bool) -> list[str] | None:
        """
        Return annotations associated with this attribute or parameter, if any.

        Default implementation returns None (no annotations).
        """
        return None

    def get_edge_spec(self, _attribute_node: CodeNode[T_Node], _is_parameter: bool) -> str | None:
        """
        Return the edge spec name for this attribute or parameter, if any.
        """
        return None

    def is_many_to_many(self, _attribute_node: CodeNode[T_Node], _is_parameter: bool) -> bool:
        """
        Return True if this attribute is a many-to-many relationship, False otherwise.
        """
        return False
