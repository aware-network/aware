"""Python implementation of the CodeSectionImportAdapter."""

from __future__ import annotations
from collections.abc import Iterable
import re
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query
from python_grammar._tree_sitter_python import PYTHON_LANGUAGE

# Aware Primitive Code
from aware_code.section.import_.adapter import CodeSectionImportAdapter
from aware_code.node.node import CodeNode

# Logging
from aware_utils.logging import logger


def debug_node(node: Node, depth: int = 0) -> None:
    indent = " " * (2 * depth)
    logger.info(f"{indent}{node.text.decode('utf-8') if node.text else ''}:{node.type}")
    for child in node.children:
        debug_node(child, depth + 1)


class PythonImportAdapter(CodeSectionImportAdapter[Node]):
    """
    Implementation of CodeSectionImportAdapter for Python using Tree-sitter.

    Extracts imports from Python parse trees.
    """

    # Pre-compiled query for finding imports, including the specific future_import_statement node
    IMPORT_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (import_statement) @import
        (import_from_statement) @from_import
        (future_import_statement) @future_import
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all import statements in the Python source code.

        Args:
            root: The root node of the parse tree
            source: The Python source code as bytes

        Returns:
            Iterable of nodes representing imports
        """
        captures = self.IMPORT_QUERY.captures(root)

        # Regular imports
        for import_node in captures.get("import", []):
            yield CodeNode(node=import_node, byte_start=import_node.start_byte, byte_end=import_node.end_byte)

        # From imports
        for from_import_node in captures.get("from_import", []):
            yield CodeNode(
                node=from_import_node, byte_start=from_import_node.start_byte, byte_end=from_import_node.end_byte
            )

        # Future imports
        for future_import_node in captures.get("future_import", []):
            yield CodeNode(
                node=future_import_node, byte_start=future_import_node.start_byte, byte_end=future_import_node.end_byte
            )

    @override
    def is_from_import(self, import_node: CodeNode[Node]) -> bool:
        """
        Determine if this is a 'from X import Y' style import.

        Args:
            import_node: Node representing an import statement

        Returns:
            True if this is a from-import, False for regular import
        """
        return import_node.node.type in ["import_from_statement", "future_import_statement"]

    @override
    def is_star_import(self, import_node: CodeNode[Node]) -> bool:
        """
        Determine if this is a star import (from X import *).

        Args:
            import_node: Node representing an import statement

        Returns:
            True if this is a star import
        """
        if not self.is_from_import(import_node):
            return False

        # Check for wildcard import node
        for child in import_node.node.children:
            if child.type == "wildcard_import":
                return True

        return False

    @override
    def get_module_name(self, import_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the module name from an import statement.

        Args:
            import_node: Node representing an import statement

        Returns:
            Node representing the module name
        """
        # Store the text for debug purposes
        node_text = import_node.node_text()

        # Special case for future imports
        if import_node.node.type == "future_import_statement":
            # For future imports we know the module is __future__
            for child in import_node.node.children:
                if child.type == "__future__":  # The literal token in the grammar
                    return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

            # If for some reason we don't find the token, create a synthetic node
            return CodeNode(
                node=import_node.node,
                byte_start=import_node.byte_start + node_text.find("__future__"),
                byte_end=import_node.byte_start + node_text.find("__future__") + len("__future__"),
            )

        if self.is_from_import(import_node):
            # For from imports, find the module name
            for child in import_node.node.children:
                if child.type in ["dotted_name", "identifier"]:
                    return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

            # Handle pure relative imports like "from . import x" where no module name is provided.
            # In this case, the import tree contains a `relative_import` node that represents the dot
            # (or series of dots) indicating the level. We treat this node as the module name so that
            # callers have something to work with instead of raising an error.
            for child in import_node.node.children:
                if child.type == "relative_import":
                    return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
        else:
            # For regular imports, check if there's an aliased_import node
            for child in import_node.node.children:
                if child.type == "aliased_import":
                    # The module name is the first dotted_name in an aliased_import
                    for grandchild in child.children:
                        if grandchild.type == "dotted_name":
                            return CodeNode(
                                node=grandchild, byte_start=grandchild.start_byte, byte_end=grandchild.end_byte
                            )
                elif child.type in ["dotted_name", "identifier"]:
                    # Direct module name as child (for non-aliased imports)
                    return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

        # If we reach here, we couldn't find the module name with the expected structure
        debug_node(import_node.node)
        raise ValueError(f"Could not find module name in import: {node_text}")

    @override
    def get_import_names(
        self, import_node: CodeNode[Node]
    ) -> Iterable[tuple[CodeNode[Node], CodeNode[Node] | None]]:
        """
        Extract the imported names and their aliases.

        Args:
            import_node: Node representing an import statement

        Returns:
            Iterable of tuples containing (name_node, alias_node or None)
        """
        # Special handling for future imports
        if import_node.node.type == "future_import_statement":
            found_name = False
            # Direct extraction of the 'annotations' or other identifier
            for child in import_node.node.children:
                # Based on the log output, annotations is a dotted_name node right after 'import'
                if child.type == "dotted_name":
                    found_name = True
                    yield CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte), None

            if not found_name:
                # Fallback if we didn't find the name directly
                logger.error("Could not find import names in future import")
                # Create a synthetic node for "annotations"
                text = import_node.node_text()
                if "annotations" in text:
                    start_idx = text.find("annotations")
                    yield CodeNode(
                        node=import_node.node,
                        byte_start=import_node.byte_start + start_idx,
                        byte_end=import_node.byte_start + start_idx + len("annotations"),
                    ), None

        elif self.is_from_import(import_node):
            # For from imports, the imported names are direct children after the `import` token.
            after_import = False
            for child in import_node.node.children:
                if child.type == "import":
                    after_import = True
                    continue
                if not after_import:
                    continue

                if child.type == "wildcard_import":
                    yield CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte), None
                    continue

                if child.type == "aliased_import":
                    name_child = next(
                        (gc for gc in child.children if gc.type in ["dotted_name", "identifier"]),
                        None,
                    )
                    alias_child = None
                    # Pattern: <name> as <alias>
                    for i, gc in enumerate(child.children):
                        if gc.type == "identifier" and i > 0 and child.children[i - 1].type == "as":
                            alias_child = gc
                            break
                    if name_child is None:
                        continue
                    name_node = CodeNode(
                        node=name_child,
                        byte_start=name_child.start_byte,
                        byte_end=name_child.end_byte,
                    )
                    alias_node = (
                        CodeNode(node=alias_child, byte_start=alias_child.start_byte, byte_end=alias_child.end_byte)
                        if alias_child is not None
                        else None
                    )
                    yield name_node, alias_node
                    continue

                if child.type in ["dotted_name", "identifier"]:
                    # Handles `from x import Name` and comma-separated lists.
                    yield CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte), None
        else:
            # For regular imports
            for child in import_node.node.children:
                if child.type == "aliased_import":
                    # Handle aliased imports: import module as alias
                    module_node = None
                    alias_node = None

                    for i, grandchild in enumerate(child.children):
                        if grandchild.type == "dotted_name":
                            module_node = CodeNode(
                                node=grandchild, byte_start=grandchild.start_byte, byte_end=grandchild.end_byte
                            )
                        elif grandchild.type == "identifier" and i > 0 and child.children[i - 1].type == "as":
                            alias_node = CodeNode(
                                node=grandchild, byte_start=grandchild.start_byte, byte_end=grandchild.end_byte
                            )

                    if module_node:
                        yield module_node, alias_node
                elif child.type in ["dotted_name", "identifier"]:
                    # Direct module import without alias
                    yield CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte), None

    @override
    def get_relative_level(self, import_node: CodeNode[Node]) -> int:
        """
        Get the relative import level (number of dots in a relative import).

        Args:
            import_node: Node representing an import statement

        Returns:
            Number of dots in a relative import, or 0 for absolute imports
        """
        if not self.is_from_import(import_node):
            return 0

        # Look for the relative_import node
        for child in import_node.node.children:
            if child.type == "relative_import":
                # Count dots in the import_prefix
                for prefix_node in child.children:
                    if prefix_node.type == "import_prefix":
                        # Count the number of . nodes
                        dot_count = sum(1 for dot_node in prefix_node.children if dot_node.type == ".")
                        return dot_count

        # Fallback: count dots in the text
        text = import_node.node_text()
        if "from " in text and " import" in text:
            module_part = text[text.find("from ") + 5:text.find(" import")].strip()
            if module_part.startswith("."):
                return len(module_part)

        return 0

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a unique identifier for the Python import.

        For regular imports, use format: "import.module"
        For from imports, use format: "from.module.import.names"
        Include aliases if present.

        Args:
            node: The import node to get the identifier for
            parent: Optional parent name to prepend

        Returns:
            Unique identifier for this import
        """
        # Define prefix outside the try block so it's available in the except block
        prefix = f"{parent}:" if parent else ""

        try:
            # Get the module text directly from the node if possible
            module_node = self.get_module_name(node)
            module_text = module_node.node_text()

            if self.is_from_import(node):
                if self.is_star_import(node):
                    return f"{prefix}from.{module_text}.import.*"

                # Collect imported names
                from_names: list[str] = []
                for name_node, alias_node in self.get_import_names(node):
                    if hasattr(name_node.node, "text"):
                        name = name_node.node_text()
                        if alias_node and hasattr(alias_node.node, "text"):
                            alias = alias_node.node_text()
                            from_names.append(f"{name}:as:{alias}")
                        else:
                            from_names.append(name)

                return f"{prefix}from.{module_text}.import.{','.join(from_names)}"
            else:
                # Regular import
                import_names: list[str] = []
                for name_node, alias_node in self.get_import_names(node):
                    if hasattr(name_node.node, "text"):
                        name = name_node.node_text()
                        if alias_node and hasattr(alias_node.node, "text"):
                            alias = alias_node.node_text()
                            import_names.append(f"{name}:as:{alias}")
                        else:
                            import_names.append(name)

                return f"{prefix}import.{','.join(import_names) if import_names else module_text}"
        except Exception:
            # Fallback: use position-based ID
            return f"{prefix}import@{node.byte_start}"

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized import statement for hashing.

        This normalizes whitespace and creates a consistent representation.

        Args:
            node: The import node to get content for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        # Extract the node's content
        content = source[node.byte_start:node.byte_end]

        # Normalize whitespace
        normalized = re.sub(rb"\s+", b" ", content)

        # Remove comments within the import statement
        normalized = re.sub(rb"#.*?(?=\n|$)", b"", normalized)

        # Strip leading/trailing whitespace
        normalized = normalized.strip()

        return normalized

    @override
    def get_alias_bindings(self, import_node: CodeNode[Node]) -> Iterable[tuple[str, str]]:
        """
        Extract alias-to-fully-qualified-name bindings from an import statement.

        Args:
            import_node: Node representing an import statement

        Returns:
            Iterable of tuples containing (alias, fully_qualified_name)
            For 'import module as alias' -> ('alias', 'module')
            For 'from module import name as alias' -> ('alias', 'module.name')
            For 'import module' -> ('module', 'module') or ('module_basename', 'module')
            For 'from module import name' -> ('name', 'module.name')
            Star imports return empty iterable
        """
        if self.is_star_import(import_node):
            # Star imports don't create specific bindings we can track
            return

        if self.is_from_import(import_node):
            # For from imports: from module import name [as alias]
            try:
                module_node = self.get_module_name(import_node)
                module_name = module_node.node_text()

                for name_node, alias_node in self.get_import_names(import_node):
                    name = name_node.node_text()
                    alias = alias_node.node_text() if alias_node else name
                    fully_qualified = f"{module_name}.{name}" if module_name != "__future__" else name
                    yield alias, fully_qualified
            except (ValueError, AttributeError):
                # Skip imports we can't parse properly
                pass
        else:
            # For regular imports: import module [as alias]
            try:
                for name_node, alias_node in self.get_import_names(import_node):
                    module_name = name_node.node_text()
                    alias = alias_node.node_text() if alias_node else module_name.split(".")[0]
                    yield alias, module_name
            except (ValueError, AttributeError):
                # Skip imports we can't parse properly
                pass
