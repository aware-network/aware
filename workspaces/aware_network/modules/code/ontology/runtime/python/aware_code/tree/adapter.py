"""Tree adapter interface for parsing source code files."""

from abc import ABC, abstractmethod
from typing import Generic

from aware_code.node.node import T_Node
from aware_code.tree.tree import CodeTree


class CodeTreeAdapter(Generic[T_Node], ABC):
    """
    Abstract interface for language-specific tree parsing.

    Each language implements its own TreeAdapter to handle the specifics of
    parsing that language while presenting a uniform interface.
    """

    @abstractmethod
    def parse(self, file_path: str) -> CodeTree[T_Node] | None:
        """
        Parse a source code file and return a CodeTree.

        Args:
            file_path: Path to the source file

        Returns:
            CodeTree containing the parse tree and source bytes, or None if parsing fails
        """
        pass

    def parse_content(self, content: str | bytes, file_path: str | None = None) -> CodeTree[T_Node] | None:
        """
        Parse content directly and return a CodeTree.

        Adapters may override this for in-memory parsing workflows (LSP, tests).
        Default implementation returns None when unsupported.
        """
        _ = (content, file_path)
        return None

    def is_empty_file_allowed(self, file_path: str) -> bool:
        """
        Return whether an empty file path is allowed for this adapter.

        Default implementation is strict and disallows empty files.
        """
        _ = file_path
        return False
