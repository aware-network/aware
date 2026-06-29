"""Python implementation of the CodeSectionClassAdapter."""

from __future__ import annotations
from collections.abc import Iterable
import re
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query
from python_grammar._tree_sitter_python import PYTHON_LANGUAGE

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.class_.adapter import CodeSectionClassAdapter

# Python Grammar
from python_grammar.adapters.enum_adapter import PythonEnumAdapter


class PythonClassAdapter(CodeSectionClassAdapter[Node]):
    """
    Implementation of CodeSectionClassAdapter for Python using Tree-sitter.

    Extracts class definitions and their attributes/methods from Python parse trees.
    """

    # Pre-compiled queries for finding classes
    CLASS_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition) @class
        """
    )

    CLASS_NAME_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          name: (identifier) @class_name)
        """
    )

    CLASS_ATTRIBUTES_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          body: (block
            (expression_statement
              (assignment
                left: (identifier) @attribute_name)))) @class
        """
    )

    CLASS_METHODS_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          body: (block
            [(function_definition) @method
             (decorated_definition
               (function_definition) @method)]))
        """
    )

    CLASS_BASE_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          superclasses: (argument_list) @base_classes)
        """
    )

    def __init__(self):
        """Initialize the adapter with required helpers."""
        self.enum_adapter: PythonEnumAdapter = PythonEnumAdapter()

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all class definitions in the parse tree, excluding enum classes.

        Args:
            root: The root node of the parse tree
            source: The source code as bytes

        Returns:
            Iterable of nodes representing class definitions that aren't enums
        """
        captures = self.CLASS_QUERY.captures(root)
        if "class" in captures:
            for class_node in captures["class"]:
                # Skip if this is an enum class
                if not self.enum_adapter.is_enum(class_node):
                    yield CodeNode(node=class_node, byte_start=class_node.start_byte, byte_end=class_node.end_byte)

    @override
    def get_name(self, class_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the name from a class definition.

        Args:
            class_node: Node representing a class definition

        Returns:
            Node representing the class name
        """
        captures = self.CLASS_NAME_QUERY.captures(class_node.node)
        if "class_name" in captures and captures["class_name"]:
            name_node = captures["class_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # Fallback if query fails - try to find name node by navigating children
        for child in class_node.node.children:
            if child.type == "identifier":
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

        raise ValueError("No class name found in class definition")

    @override
    def get_attributes(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract attribute nodes from a class definition.

        This includes both class attributes and instance attributes (from __init__).

        Args:
            class_node: Node representing a class definition

        Returns:
            Iterable of nodes representing class attributes
        """
        # Get class-level attributes
        captures = self.CLASS_ATTRIBUTES_QUERY.captures(class_node.node)
        seen_attrs: set[int] = set()

        if "class" in captures:
            for class_node_in_captures in captures["class"]:
                for attr_stmt in class_node_in_captures.children:
                    if attr_stmt.type == "block":
                        for stmt in attr_stmt.children:
                            if stmt.type == "expression_statement":
                                for expr in stmt.children:
                                    if expr.type == "assignment":
                                        attr_start = expr.start_byte
                                        if attr_start not in seen_attrs:
                                            seen_attrs.add(attr_start)
                                            yield CodeNode(
                                                node=expr, byte_start=expr.start_byte, byte_end=expr.end_byte
                                            )

    @override
    def get_methods(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract method nodes from a class definition.

        Args:
            class_node: Node representing a class definition

        Returns:
            Iterable of nodes representing class methods
        """
        captures = self.CLASS_METHODS_QUERY.captures(class_node.node)
        if "method" in captures:
            for method_node in captures["method"]:
                yield CodeNode(node=method_node, byte_start=method_node.start_byte, byte_end=method_node.end_byte)

    @override
    def get_modifiers(self, class_node: CodeNode[Node]) -> list[CodeNode[Node]]:
        """
        Extract modifiers nodes from a Python class definition.

        Args:
            class_node: Node representing a class definition

        Returns:
            Iterable of nodes representing class modifiers
        """
        # For now, return empty iterable as Python class modifiers are not implemented yet
        return []

    @override
    def get_keyword(self, class_node: CodeNode[Node]) -> CodeNode[Node] | None:
        """
        Extract the 'class' keyword node from a Python class definition.

        Args:
            class_node: Node representing a class definition

        Returns:
            Node representing the 'class' keyword
        """
        # The first child of a class_definition should be the 'class' keyword
        for child in class_node.node.children:
            if child.type == "class" or (hasattr(child, "text") and child.text == b"class"):
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
        return None

    @override
    def get_bases(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract the base class nodes from a Python class definition.

        Args:
            class_node: Node representing a class definition

        Returns:
            Iterable of nodes representing the base classes
        """
        captures = self.CLASS_BASE_QUERY.captures(class_node.node)
        if "base_classes" in captures and captures["base_classes"]:
            base_list_node = captures["base_classes"][0]
            # The argument_list contains individual base classes as children
            for child in base_list_node.children:
                if child.type in ["identifier", "attribute", "call"]:  # Valid base class node types
                    yield CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a fully-qualified name for a Python class.

        For nested classes, this includes the parent class name.

        Args:
            node: The class node to get the qualified name for
            parent: Optional parent name (for nested classes)

        Returns:
            Qualified name string
        """
        name_node = self.get_name(node)
        name_text = name_node.node_text()

        # If we have a parent class, prepend it
        if parent:
            return f"{parent}.{name_text}"

        # Look for module-level namespace (import statements)
        root = node.node
        while root.parent:
            root = root.parent

        module_name = ""

        # TODO: consider determine module name from file path

        if module_name:
            return f"{module_name}.{name_text}"

        return name_text

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for a Python class definition.

        This strips comments and normalizes whitespace to ensure consistent hashing
        regardless of formatting changes.

        Args:
            node: The class node to get body bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        # Extract the node's bytes
        node_bytes = source[node.byte_start:node.byte_end]

        # Remove Python comments
        normalized = re.sub(
            b"#.*?$",  # Remove single-line comments
            b"",  # Replace with empty string
            node_bytes,  # Input
            flags=re.MULTILINE,  # Multi-line mode
        )

        # Normalize whitespace
        normalized = re.sub(b"\\s+", b" ", normalized)

        # Remove trailing/leading whitespace
        normalized = normalized.strip()

        return normalized

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        """Return a reference string for a Python class."""
        return self.qualname(node, parent)
