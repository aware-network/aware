"""Interface for adapters that extract annotations from parsed code."""

from abc import ABC, abstractmethod
from typing import override

# Kernel Graph Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter


class CodeSectionAnnotationAdapter(CodeNodeAdapter[T_Node], ABC):
    """Interface for annotation section adapters.

    Implementations extract `ann` statements (or equivalent) from
    language-specific parse trees while maintaining consistent
    positional information.
    """

    @property
    @override
    def section_type(self) -> CodeSectionType:
        """Return the type of section."""
        return CodeSectionType.annotation

    @override
    @abstractmethod
    def qualname(self, node: CodeNode[T_Node], parent: str | None = None) -> str:
        """Return a qualified name for the annotation within the file."""
        raise NotImplementedError

    @override
    @abstractmethod
    def body_bytes(self, node: CodeNode[T_Node], source: bytes) -> bytes:
        """Return normalized body bytes for hashing."""
        raise NotImplementedError

    @abstractmethod
    def get_path(self, node: CodeNode[T_Node]) -> str:
        """Extract the annotation path token (e.g. schema.Type.attr)."""
        raise NotImplementedError

    @abstractmethod
    def get_verb(self, node: CodeNode[T_Node]) -> str:
        """Extract the annotation verb token (e.g. load, project)."""
        raise NotImplementedError

    @abstractmethod
    def get_args(self, node: CodeNode[T_Node]) -> list[str]:
        """Extract annotation arguments (tokens after the verb)."""
        raise NotImplementedError
