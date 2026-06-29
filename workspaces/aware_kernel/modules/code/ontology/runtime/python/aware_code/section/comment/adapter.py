"""Interface for adapters that extract comments from parsed code."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import override

# Kernel Graph Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.comment.code_section_comment_enums import (
    CodeSectionCommentType,
)

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter


class CodeSectionCommentAdapter(CodeNodeAdapter[T_Node], ABC):
    """
    Interface for comment section adapters.

    Implementations will extract comment information from language-specific
    parse trees while maintaining consistent positional information.
    """

    @property
    @override
    def section_type(self) -> CodeSectionType:
        """Return the type of section."""
        return CodeSectionType.comment

    @abstractmethod
    def get_content_segments(self, comment_node: CodeNode[T_Node], source: bytes) -> Iterable[CodeNode[T_Node]]:
        """
        Extract comment content as multiple segments for multiline comments.

        This allows proper handling of comments that span multiple lines where each
        line should be stored as a separate content segment to preserve exact byte
        positioning and enable lossless round-trip transformations.

        Args:
            comment_node: Node representing a comment (may span multiple lines)
            source: The source code as bytes

        Returns:
            Iterable of nodes representing individual content segments
        """
        pass

    @abstractmethod
    def get_comment_type(self, comment_node: CodeNode[T_Node]) -> CodeSectionCommentType:
        """
        Determine the type of comment.

        Args:
            comment_node: Node representing a comment

        Returns:
            The comment type (line, block, doc, metadata)
        """
        pass

    @abstractmethod
    def get_associated_node(self, comment_node: CodeNode[T_Node], source: bytes) -> CodeNode[T_Node] | None:
        """
        Find the node that this comment is associated with, if any.

        Args:
            comment_node: Node representing a comment
            source: The source code as bytes

        Returns:
            Node that the comment is associated with, or None if standalone
        """
        pass

    def section_lookup_key(self, _associated_node: CodeNode[T_Node]) -> tuple[CodeSectionType, str] | None:
        """
        Return the key that should be used to retrieve the target section from
        the global section-index.

        If the adapter cannot determine a key, return **None** and the builder
        will fall back to the generic hash-based lookup.
        """
        return None
