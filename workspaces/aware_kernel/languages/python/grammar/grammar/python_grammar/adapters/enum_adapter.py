"""Python implementation of the CodeSectionEnumAdapter."""

from __future__ import annotations
from collections.abc import Iterable
import re
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query
from python_grammar._tree_sitter_python import PYTHON_LANGUAGE

# Aware Primitive Code
from aware_code.section.enum.adapter import CodeSectionEnumAdapter
from aware_code.node.node import CodeNode

CaptureMap = dict[str, list[Node]]


def _node_key(node: Node) -> tuple[int, int, str]:
    return (node.start_byte, node.end_byte, node.type)


class PythonEnumAdapter(CodeSectionEnumAdapter[Node]):
    """
    Implementation of CodeSectionEnumAdapter for Python using Tree-sitter.

    Extracts enum definitions from Python parse trees, specifically classes
    that inherit from Enum.
    """

    # Pre-compiled queries for finding enums
    ENUM_CLASS_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          superclasses: (argument_list
            (identifier) @superclass)) @class
        """
    )

    ENUM_NAME_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          name: (identifier) @enum_name)
        """
    )

    ENUM_VALUE_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          body: (block
            (expression_statement
              (assignment
                left: (identifier) @value_name)))) @enum_class
        """
    )

    # Additional pre-compiled queries that were previously inline
    ENUM_IMPORT_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (module
          (import_from_statement
            module_name: (dotted_name) @module
            name: (dotted_name) @name)) @import_stmt
        """
    )

    POTENTIAL_ENUM_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          superclasses: (argument_list)) @potential_enum
        """
    )

    ENUM_VALUES_SPECIFIC_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          body: (block
            (expression_statement
              (assignment
                left: (identifier) @value_name))))
        """
    )

    # New class-level queries for is_enum method
    DIRECT_SUPERCLASS_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          superclasses: (argument_list
            (identifier) @superclass))
        """
    )

    DOTTED_SUPERCLASS_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          superclasses: (argument_list
            (attribute
              object: (identifier) @module
              attribute: (identifier) @class)))
        """
    )

    # Query for all class definitions
    ALL_CLASSES_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition) @class
        """
    )

    @staticmethod
    def _decode_node_text(node: Node) -> str:
        text = node.text
        if text is None:
            return ""
        return text.decode("utf-8")

    def is_enum(self, class_node: Node) -> bool:
        """
        Determine if a class node represents an enum.

        A class is considered an enum if it inherits from Enum or a class with 'Enum' in its name.

        Args:
            class_node: The class definition node to check

        Returns:
            True if the class is an enum, False otherwise
        """
        # Method 1: Check direct superclass names
        captures = self.DIRECT_SUPERCLASS_QUERY.captures(class_node)
        if "superclass" in captures:
            for node in captures["superclass"]:
                superclass_text = self._decode_node_text(node)
                if "Enum" in superclass_text:
                    return True

        # Method 2: Check for dotted superclass names like "enum.Enum"
        captures = self.DOTTED_SUPERCLASS_QUERY.captures(class_node)
        if "module" in captures and "class" in captures:
            for i, module_node in enumerate(captures["module"]):
                module_text = self._decode_node_text(module_node)
                if i < len(captures["class"]):
                    class_text = self._decode_node_text(captures["class"][i])
                    if module_text == "enum" and "Enum" in class_text:
                        return True

        return False

    def _find_enum_classes_from_captures(self, captures: CaptureMap) -> list[Node]:
        """
        Identify enum classes from tree-sitter query captures.

        Args:
            captures: Dictionary of capture results from tree-sitter query

        Returns:
            List of enum class nodes
        """
        enum_classes: list[Node] = []

        # Dictionary to store matches by node ID
        class_nodes: dict[tuple[int, int, str], Node] = {}
        superclass_nodes: dict[tuple[int, int, str], Node] = {}

        # Process captures to separate class nodes and superclass nodes
        if "class" in captures:
            for node in captures["class"]:
                class_nodes[_node_key(node)] = node

        if "superclass" in captures:
            for node in captures["superclass"]:
                superclass_nodes[_node_key(node)] = node

        # Check each superclass to see if it's an Enum
        for superclass_node in superclass_nodes.values():
            superclass_text = self._decode_node_text(superclass_node)
            if "Enum" in superclass_text:  # Simple check for Enum in name
                # Find the parent class node
                for class_node in class_nodes.values():
                    # Simple check: if the superclass is within the byte range of the class
                    if (
                        class_node.start_byte <= superclass_node.start_byte
                        and class_node.end_byte >= superclass_node.end_byte
                    ):
                        enum_classes.append(class_node)
                        break

        return enum_classes

    def _has_enum_import(self, root: Node) -> bool:
        """
        Check if the file imports the enum module.

        Args:
            root: The root node of the parse tree

        Returns:
            True if enum is imported, False otherwise
        """
        import_captures = self.ENUM_IMPORT_QUERY.captures(root)

        if "module" in import_captures:
            for node in import_captures["module"]:
                module_text = self._decode_node_text(node)
                if module_text == "enum":
                    return True

        return False

    def _find_enum_classes_from_imports(self, root: Node) -> list[Node]:
        """
        Find enum classes based on imports and class inheritance.

        Args:
            root: The root node of the parse tree

        Returns:
            List of enum class nodes
        """
        enum_classes: list[Node] = []

        # Skip if no enum import
        if not self._has_enum_import(root):
            return enum_classes

        # Get all classes that might be enums
        potential_captures = self.POTENTIAL_ENUM_QUERY.captures(root)

        if "potential_enum" in potential_captures:
            for node in potential_captures["potential_enum"]:
                # Skip if already identified as enum
                if node in enum_classes:
                    continue

                # Get the parent class node (potential_enum points to argument_list)
                parent_class = node.parent
                while parent_class and parent_class.type != "class_definition":
                    parent_class = parent_class.parent

                if parent_class and self.is_enum(parent_class):
                    enum_classes.append(parent_class)
                    continue

                # Fallback: check superclasses manually
                for child in node.children:
                    if child.type == "identifier":
                        arg_text = self._decode_node_text(child)
                        if "Enum" in arg_text:
                            if parent_class:
                                enum_classes.append(parent_class)
                            break

        return enum_classes

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all enum definitions in the parse tree.

        In Python, enums are classes that inherit from enum.Enum or similar.

        Args:
            root: The root node of the parse tree
            source: The source code as bytes

        Returns:
            Iterable of nodes representing enum definitions
        """
        # First approach: Find enum classes using captures directly
        captures = self.ENUM_CLASS_QUERY.captures(root)
        enum_classes = self._find_enum_classes_from_captures(captures)

        # Second approach: Find enum classes based on imports
        import_enum_classes = self._find_enum_classes_from_imports(root)

        # Third approach: Scan all class definitions directly
        all_classes_captures = self.ALL_CLASSES_QUERY.captures(root)
        if "class" in all_classes_captures:
            for class_node in all_classes_captures["class"]:
                if self.is_enum(class_node) and class_node not in enum_classes:
                    enum_classes.append(class_node)

        # Combine all found enum classes, avoiding duplicates
        seen_ids: set[tuple[int, int, str]] = set()
        for enum_class in enum_classes + import_enum_classes:
            node_key = _node_key(enum_class)
            if node_key not in seen_ids:
                seen_ids.add(node_key)
                yield CodeNode(node=enum_class, byte_start=enum_class.start_byte, byte_end=enum_class.end_byte)

    @override
    def get_name(self, enum_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the name from an enum definition.

        Args:
            enum_node: Node representing an enum definition

        Returns:
            Node representing the enum name
        """
        captures = self.ENUM_NAME_QUERY.captures(enum_node.node)

        if "enum_name" in captures and captures["enum_name"]:
            name_node = captures["enum_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # Fallback if query fails
        for child in enum_node.node.children:
            if child.type == "identifier":
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

        raise ValueError("No enum name found in enum definition")

    @override
    def get_values(self, enum_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract enum values from an enum definition.

        Args:
            enum_node: Node representing an enum definition

        Returns:
            Iterable of nodes representing enum values
        """
        captures = self.ENUM_VALUES_SPECIFIC_QUERY.captures(enum_node.node)
        if "value_name" in captures:
            for value_node in captures["value_name"]:
                yield CodeNode(node=value_node, byte_start=value_node.start_byte, byte_end=value_node.end_byte)

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a fully-qualified name for a Python enum.

        For nested enums, this includes the parent name.

        Args:
            node: The enum node to get the qualified name for
            parent: Optional parent name

        Returns:
            Qualified name string
        """
        name_node = self.get_name(node)
        name_text = name_node.node_text()

        # If we have a parent class or namespace, prepend it
        if parent:
            return f"{parent}.{name_text}"

        # Try to determine module name
        root = node.node
        while root.parent:
            root = root.parent

        module_name = ""
        # In a real implementation, we would try to determine the module name
        # from the file path or imports

        if module_name:
            return f"{module_name}.{name_text}"

        return name_text

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for a Python enum definition.

        This strips comments and normalizes whitespace to ensure consistent hashing
        regardless of formatting changes.

        Args:
            node: The enum node to get body bytes for
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
        """Return a reference string for a Python enum."""
        return self.qualname(node, parent)
