"""Generic code tree representation."""

from dataclasses import dataclass
from typing import Generic

from aware_code.node.node import CodeNode, T_Node


@dataclass
class CodeTree(Generic[T_Node]):
    """
    Language-agnostic representation of a parsed source code tree.

    Wraps the underlying parser-specific tree structure (Tree-sitter, LibCST, etc.)
    while providing a generic interface.
    """

    root: CodeNode[T_Node]
    source_bytes: bytes

    @property
    def text(self) -> str:
        """Return the full source text."""
        return self.source_bytes.decode("utf-8", errors="replace")
