"""Interface for adapters that extract information from parsed code nodes."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic

# Core Code Node
from aware_code.node.node import CodeNode, T_Node

# Primitive Code Section
from aware_code_ontology.code.code_section_enums import CodeSectionType


class CodeNodeAdapter(Generic[T_Node], ABC):
    """
    Interface for code node adapters.

    Implementations extract relevant information from language-specific parse trees.
    """

    @abstractmethod
    def match_nodes(self, root: T_Node, source: bytes) -> Iterable[CodeNode[T_Node]]:
        """Return an iterable of nodes that match the adapter's criteria."""
        pass

    @property
    @abstractmethod
    def section_type(self) -> CodeSectionType:
        """Return the type of section this adapter processes."""
        pass

    @abstractmethod
    def qualname(self, node: CodeNode[T_Node], parent: str | None = None) -> str:
        """
        Return a fully-qualified name for the node within the file.

        Args:
            node: The node to get the qualified name for
            parent: Optional parent name to prepend
        Returns:
            Fully qualified name (e.g., "schema.table_name", "class.method", etc.)
        """
        pass

    @abstractmethod
    def body_bytes(self, node: CodeNode[T_Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for hashing.

        This should strip comments and normalize whitespace to ensure
        formatting changes don't affect the hash.

        Args:
            node: The node to get body bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        pass

    def reference_string(self, node: CodeNode[T_Node], parent: str | None = None) -> str | None:
        """Return a language-specific reference like 'public.permission' or None."""
        _ = (node, parent)
        return None
