"""Interface for adapters that extract imports from parsed code."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import override

from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter


class CodeSectionImportAdapter(CodeNodeAdapter[T_Node], ABC):
    """
    Interface for import section adapters.

    Implementations will extract import-related information from language-specific
    parse trees while maintaining consistent positional information.
    """

    @property
    @override
    def section_type(self) -> CodeSectionType:
        """Return the type of section."""
        return CodeSectionType.import_

    @abstractmethod
    def is_from_import(self, import_node: CodeNode[T_Node]) -> bool:
        """
        Determine if this is a 'from X import Y' style import.

        Args:
            import_node: Node representing an import statement

        Returns:
            True if this is a from-import, False for regular import
        """
        pass

    @abstractmethod
    def is_star_import(self, import_node: CodeNode[T_Node]) -> bool:
        """
        Determine if this is a star import (from X import *).

        Args:
            import_node: Node representing an import statement

        Returns:
            True if this is a star import
        """
        pass

    @abstractmethod
    def get_module_name(self, import_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        """
        Extract the module name from an import statement.

        Args:
            import_node: Node representing an import statement

        Returns:
            Node representing the module name
        """
        pass

    @abstractmethod
    def get_import_names(
        self, import_node: CodeNode[T_Node]
    ) -> Iterable[tuple[CodeNode[T_Node], CodeNode[T_Node] | None]]:
        """
        Extract the imported names and their aliases.

        Args:
            import_node: Node representing an import statement

        Returns:
            Iterable of tuples containing (name_node, alias_node or None)
        """
        pass

    @abstractmethod
    def get_relative_level(self, import_node: CodeNode[T_Node]) -> int:
        """
        Get the relative import level (number of dots in a relative import).

        Args:
            import_node: Node representing an import statement

        Returns:
            Number of dots in a relative import, or 0 for absolute imports
        """
        pass

    @abstractmethod
    def get_alias_bindings(self, import_node: CodeNode[T_Node]) -> Iterable[tuple[str, str]]:
        """
        Extract alias-to-fully-qualified-name bindings from an import statement.

        Args:
            import_node: Node representing an import statement

        Returns:
            Iterable of tuples containing (alias, fully_qualified_name)
        """
        pass
