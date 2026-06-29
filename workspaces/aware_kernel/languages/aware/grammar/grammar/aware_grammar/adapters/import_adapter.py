"""Aware implementation of the CodeSectionImportAdapter."""

from collections.abc import Iterable
import re
from typing_extensions import override
from typing import final

# Tree-sitter
from tree_sitter import Node
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

# Aware Primitive Code
from aware_code.section.import_.adapter import CodeSectionImportAdapter
from aware_code.node.node import CodeNode


@final
class AwareImportAdapter(CodeSectionImportAdapter[Node]):
    """
    Implementation of CodeSectionImportAdapter for Aware using Tree-sitter.

    Extracts imports from Aware parse trees.
    """

    # Pre-compiled query for finding imports
    IMPORT_QUERY = AWARE_LANGUAGE.query(
        """
        (import_stmt) @import
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all import statements in the Aware source code.

        Args:
            root: The root node of the parse tree
            source: The Aware source code as bytes

        Returns:
            Iterable of nodes representing imports
        """
        captures = self.IMPORT_QUERY.captures(root)

        # Regular imports - sort by start_byte to ensure source order
        import_nodes = captures.get("import", [])
        sorted_imports = sorted(import_nodes, key=lambda node: node.start_byte)

        for import_node in sorted_imports:
            yield CodeNode(node=import_node, byte_start=import_node.start_byte, byte_end=import_node.end_byte)

    @override
    def is_from_import(self, import_node: CodeNode[Node]) -> bool:
        """
        Determine if this is a 'from X import Y' style import.

        Args:
            import_node: Node representing an import statement

        Returns:
            False - Aware language doesn't have from-imports, only direct imports
        """
        return False

    @override
    def is_star_import(self, import_node: CodeNode[Node]) -> bool:
        """
        Determine if this is a star import (import module.*).

        Args:
            import_node: Node representing an import statement

        Returns:
            True if this is a star import
        """
        # Check if the import target contains a wildcard
        for child in import_node.node.children:
            if child.type == "import_target":
                for grandchild in child.children:
                    if grandchild.type == "*":
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
        # For Aware imports like "import module.submodule", we want "module.submodule"
        # For star imports like "import module.*", we want "module"

        for child in import_node.node.children:
            if child.type == "import_target":
                if self.is_star_import(import_node):
                    # Return just the module part for star imports.
                    # NOTE: tree-sitter nodes don't allow us to slice text, so we return the first ident node.
                    for grandchild in child.children:
                        if grandchild.type == "ident":
                            return CodeNode(
                                node=grandchild, byte_start=grandchild.start_byte, byte_end=grandchild.end_byte
                            )
                # Regular import: return the entire target
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

        # Fallback if we can't find the target
        node_text = import_node.node_text()
        raise ValueError(f"Could not find module name in import: {node_text}")

    @override
    def get_import_names(self, import_node: CodeNode[Node]) -> Iterable[tuple[CodeNode[Node], CodeNode[Node] | None]]:
        """
        Extract the imported names and their aliases.

        Args:
            import_node: Node representing an import statement

        Returns:
            Iterable of tuples containing (name_node, alias_node or None)
        """
        # Find alias - it's a direct child of import_stmt after "as"
        alias_node = None
        found_as = False
        for child in import_node.node.children:
            if child.type == "as":
                found_as = True
            elif found_as and child.type == "ident":
                alias_node = CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
                break

        if self.is_star_import(import_node):
            # For star imports, yield the star as the name
            for child in import_node.node.children:
                if child.type == "import_target":
                    for grandchild in child.children:
                        if grandchild.type == "*":
                            yield CodeNode(
                                node=grandchild, byte_start=grandchild.start_byte, byte_end=grandchild.end_byte
                            ), alias_node
                            return
        else:
            # For regular imports, the imported name is the target
            target_node = self.get_module_name(import_node)
            yield target_node, alias_node

    @override
    def get_relative_level(self, import_node: CodeNode[Node]) -> int:
        """
        Get the relative import level (number of dots in a relative import).

        Args:
            import_node: Node representing an import statement

        Returns:
            0 - Aware language doesn't support relative imports
        """
        return 0

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a unique identifier for the Aware import.

        For regular imports, use format: "import.module"
        For star imports, use format: "import.module.*"
        Include aliases if present.

        Args:
            node: The import node to get the identifier for
            parent: Optional parent name to prepend

        Returns:
            Unique identifier for this import
        """
        prefix = f"{parent}:" if parent else ""
        if self.is_star_import(node):
            # For star imports, get the module part and add .*
            module_node = self.get_module_name(node)
            module_text = module_node.node_text().removesuffix(".*")

            # Check for alias
            alias_text = ""
            for _name_node, alias_node in self.get_import_names(node):
                if alias_node and hasattr(alias_node.node, "text"):
                    alias_text = f":as:{alias_node.node_text()}"
                    break
            return f"{prefix}import.{module_text}.*{alias_text}"
        else:
            # Regular import
            module_node = self.get_module_name(node)
            module_text = module_node.node_text()

            # Check for alias
            alias_text = ""
            for _name_node, alias_node in self.get_import_names(node):
                if alias_node and hasattr(alias_node.node, "text"):
                    alias_text = f":as:{alias_node.node_text()}"
                    break
            return f"{prefix}import.{module_text}{alias_text}"

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
        normalized = re.sub(rb"//.*?(?=\n|$)", b"", normalized)

        # Strip leading/trailing whitespace
        normalized = normalized.strip()

        # Remove optional semicolon for consistency
        if normalized.endswith(b";"):
            normalized = normalized[:-1].strip()

        return normalized

    @override
    def get_alias_bindings(self, import_node: CodeNode[Node]) -> Iterable[tuple[str, str]]:
        """
        Extract alias-to-fully-qualified-name bindings from an import statement.

        Args:
            import_node: Node representing an import statement

        Returns:
            Iterable of tuples containing (alias, fully_qualified_name)
            For 'import module.submodule' -> ('module', 'module.submodule')
            For 'import module.submodule as alias' -> ('alias', 'module.submodule')
            For 'import module.*' -> no bindings (star imports don't create specific bindings)
            For 'import module.* as alias' -> ('alias', 'module.*')
        """
        if self.is_star_import(import_node):
            # For star imports, only create binding if there's an alias
            for _name_node, alias_node in self.get_import_names(import_node):
                if alias_node:
                    alias = alias_node.node_text()
                    module_node = self.get_module_name(import_node)
                    module_name = module_node.node_text().removesuffix(".*")
                    yield alias, f"{module_name}.*"
        else:
            # Get the full module name from import_target
            for child in import_node.node.children:
                if child.type == "import_target":
                    module_name = child.text.decode("utf-8") if child.text is not None else ""
                    break
            else:
                return  # No import_target found

            for _name_node, alias_node in self.get_import_names(import_node):
                if alias_node:
                    # Has explicit alias
                    alias = alias_node.node.text.decode("utf-8") if alias_node.node.text is not None else ""
                    yield alias, module_name
                else:
                    # No alias, use the first part of the module name
                    # For "import module.submodule", bind "module" to "module.submodule"
                    first_part = module_name.split(".")[0]
                    yield first_part, module_name
