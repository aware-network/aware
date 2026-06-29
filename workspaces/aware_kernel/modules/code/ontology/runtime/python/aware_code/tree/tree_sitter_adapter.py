"""Tree-sitter adapter for code trees."""

from __future__ import annotations

import os
from typing import final, override

# Tree-sitter
from tree_sitter import Language, Node, Parser

# Code Runtime Primitive
from aware_code.node.node import CodeNode
from aware_code.tree.tree import CodeTree
from aware_code.tree.adapter import CodeTreeAdapter

# Logging
from aware_utils.logging import logger


@final
class CodeTreeSitterAdapter(CodeTreeAdapter[Node]):
    """Code tree adapter implementation for using Tree-sitter specific languages."""

    def __init__(self, language: Language, allowed_empty_files: list[str] | None = None):
        self._parser: Parser = Parser(language=language)
        self._allowed_empty_files: list[str] = allowed_empty_files or []

    @override
    def parse(self, file_path: str) -> CodeTree[Node] | None:
        """Parse a file and return a CodeTree."""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return None

            with open(file_path, "rb") as f:
                source_bytes = f.read()

            if not source_bytes.strip():
                if self.is_empty_file_allowed(file_path):
                    logger.debug(f"File is empty: {file_path}")
                    return None
                else:
                    logger.warning(f"File is empty: {file_path}")
                    return None

            tree = self._parser.parse(source_bytes)
            root_node = CodeNode(
                node=tree.root_node,
                byte_start=tree.root_node.start_byte,
                byte_end=tree.root_node.end_byte,
            )

            return CodeTree(root=root_node, source_bytes=source_bytes)

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return None

    @override
    def parse_content(self, content: str | bytes, file_path: str | None = None) -> CodeTree[Node] | None:
        """
        Parse content directly and return a CodeTree.

        Args:
            content: Source code content (string or bytes)
            file_path: Optional file path for context (used for empty file checking)

        Returns:
            CodeTree if parsing succeeds, None otherwise
        """
        try:
            # Convert string to bytes if needed
            if isinstance(content, str):
                source_bytes = content.encode("utf-8")
            else:
                source_bytes = content

            # Check for empty content
            if not source_bytes.strip():
                # Empty content is common during editor/LSP operations (new files, clear buffer, etc.).
                # Treat this as a non-fatal parse miss and avoid warning spam.
                if file_path and self.is_empty_file_allowed(file_path):
                    logger.debug(f"Content is empty: {file_path}")
                    return None
                logger.debug(f"Content is empty: {file_path or 'direct content'}")
                return None

            # Parse using tree-sitter
            tree = self._parser.parse(source_bytes)
            root_node = CodeNode(
                node=tree.root_node,
                byte_start=tree.root_node.start_byte,
                byte_end=tree.root_node.end_byte,
            )

            return CodeTree(root=root_node, source_bytes=source_bytes)

        except Exception as e:
            logger.error(f"Error parsing content {file_path or 'direct content'}: {e}")
            return None

    @override
    def is_empty_file_allowed(self, file_path: str) -> bool:
        """Check if a file is allowed to be empty."""
        basename = os.path.basename(file_path)
        return basename in self._allowed_empty_files
