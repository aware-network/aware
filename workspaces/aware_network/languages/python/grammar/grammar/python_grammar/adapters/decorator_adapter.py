"""Python implementation of the CodeSectionDecoratorAdapter."""

from __future__ import annotations
from collections.abc import Iterable
import re
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query
from python_grammar._tree_sitter_python import PYTHON_LANGUAGE

# Aware Primitive Code
from aware_code.section.decorator.adapter import CodeSectionDecoratorAdapter
from aware_code.node.node import CodeNode


class PythonDecoratorAdapter(CodeSectionDecoratorAdapter[Node]):
    """
    Implementation of CodeSectionDecoratorAdapter for Python using Tree-sitter.

    Extracts decorators from Python parse trees.
    """

    # Pre-compiled queries for finding decorators
    DECORATOR_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (decorator) @decorator
        """
    )

    # Query to find decorator expression (the part after @)
    DECORATOR_EXPR_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (decorator
          (expression) @decorator_expr)
        """
    )

    # Query to find call expressions in decorators
    DECORATOR_CALL_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (decorator
          (call
            function: (_) @decorator_name
            arguments: (argument_list) @decorator_args))
        """
    )

    # Query to find simple name (non-call) decorators
    DECORATOR_SIMPLE_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (decorator
          [(identifier) (attribute)] @decorator_name)
        """
    )

    # Query to find the target of a decorator
    DECORATED_CLASS_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (decorated_definition
          (decorator) @decorator
          definition: (class_definition) @target)
        """
    )

    DECORATED_FUNCTION_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (decorated_definition
          (decorator) @decorator
          definition: (function_definition) @target)
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all decorators in the Python source code.

        Args:
            root: The root node of the parse tree
            source: The Python source code as bytes

        Returns:
            Iterable of nodes representing decorators
        """
        captures = self.DECORATOR_QUERY.captures(root)
        if "decorator" in captures:
            for decorator_node in captures["decorator"]:
                yield CodeNode(
                    node=decorator_node, byte_start=decorator_node.start_byte, byte_end=decorator_node.end_byte
                )

    @override
    def get_name(self, decorator_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the name from a decorator.

        For decorators like @name or @module.name, extracts the name part.
        For decorator calls like @name(args), extracts the name part.

        Args:
            decorator_node: Node representing a decorator

        Returns:
            Node representing the decorator name
        """
        # Try to find call expression first (for decorators with arguments)
        captures = self.DECORATOR_CALL_QUERY.captures(decorator_node.node)
        if "decorator_name" in captures and captures["decorator_name"]:
            name_node = captures["decorator_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # Try to find simple decorators (without arguments)
        captures = self.DECORATOR_SIMPLE_QUERY.captures(decorator_node.node)
        if "decorator_name" in captures and captures["decorator_name"]:
            name_node = captures["decorator_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # Fallback method: navigate the node structure
        for child in decorator_node.node.children:
            if child.type in ["identifier", "attribute", "call"]:
                if child.type == "call":
                    # For call expressions, get the function name
                    for call_child in child.children:
                        if call_child.type in ["identifier", "attribute"]:
                            return CodeNode(
                                node=call_child, byte_start=call_child.start_byte, byte_end=call_child.end_byte
                            )
                else:
                    return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

        # If we reach here, we couldn't find a name
        raise ValueError(f"Could not find name in decorator node: {decorator_node.node.type}")

    @override
    def get_arguments(
        self, decorator_node: CodeNode[Node]
    ) -> Iterable[tuple[CodeNode[Node] | None, CodeNode[Node]]]:
        """
        Extract arguments from a decorator.

        For decorators with arguments like @name(arg1, arg2, kwarg=value),
        extracts the argument nodes as (name_node, value_node) tuples.

        Args:
            decorator_node: Node representing a decorator

        Returns:
            Iterable of tuples (name_node, value_node) where:
            - name_node is None for positional arguments
            - name_node contains the keyword name for keyword arguments
            - value_node contains the argument value
        """
        # Look for call expression with arguments
        captures = self.DECORATOR_CALL_QUERY.captures(decorator_node.node)
        if "decorator_args" in captures and captures["decorator_args"]:
            args_node = captures["decorator_args"][0]

            # Extract individual arguments
            for child in args_node.children:
                # Skip parentheses and commas
                if child.type not in ["(", ")", ","]:
                    if child.type == "keyword_argument":
                        # For keyword arguments, extract both name and value
                        name_node = None
                        value_node = None

                        for kwarg_child in child.children:
                            if kwarg_child.type == "identifier":
                                name_node = CodeNode(
                                    node=kwarg_child, byte_start=kwarg_child.start_byte, byte_end=kwarg_child.end_byte
                                )
                            elif kwarg_child.is_named and kwarg_child.type not in ["identifier", "="]:
                                # This is the value part of the keyword argument
                                value_node = CodeNode(
                                    node=kwarg_child, byte_start=kwarg_child.start_byte, byte_end=kwarg_child.end_byte
                                )

                        if value_node:
                            yield (name_node, value_node)
                    else:
                        # For positional arguments, name is None
                        yield (None, CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte))

    @override
    def get_target(self, decorator_node: CodeNode[Node]) -> CodeNode[Node] | None:
        """
        Find the target that this decorator is applied to.

        Args:
            decorator_node: Node representing a decorator

        Returns:
            Node representing the decorated entity or None if not found
        """
        # Check for decorated class
        root = self._get_root_node(decorator_node.node)

        for captures_query in [self.DECORATED_CLASS_QUERY, self.DECORATED_FUNCTION_QUERY]:
            captures = captures_query.captures(root)
            if "decorator" in captures and "target" in captures:
                # Match the decorator node with our current decorator
                for i, dec_node in enumerate(captures["decorator"]):
                    if dec_node.id == decorator_node.node.id and i < len(captures["target"]):
                        target_node = captures["target"][i]
                        return CodeNode(
                            node=target_node, byte_start=target_node.start_byte, byte_end=target_node.end_byte
                        )

        # Try a more direct approach - check if parent is a decorated_definition
        parent = decorator_node.node.parent
        if parent and parent.type == "decorated_definition":
            for child in parent.children:
                if child.type in ["class_definition", "function_definition"]:
                    return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

        return None

    def _get_root_node(self, node: Node) -> Node:
        """
        Get the root node from any node in the tree.

        Args:
            node: Any node in the parse tree

        Returns:
            The root node of the parse tree
        """
        current = node
        while current.parent:
            current = current.parent
        return current

    @override
    def get_target_type(self, decorator_node: CodeNode[Node]) -> str | None:
        """
        Determine the type of entity the decorator is applied to.

        Args:
            decorator_node: Node representing a decorator

        Returns:
            String representing the target type ("class", "function", etc.) or None if unknown
        """
        target = self.get_target(decorator_node)
        if not target:
            return None

        if target.node.type == "class_definition":
            return "class"
        elif target.node.type == "function_definition":
            return "function"

        return None

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a fully-qualified name for a Python decorator.

        Args:
            node: The decorator node to get the qualified name for
            parent: Optional parent name to prepend

        Returns:
            Qualified name string
        """
        try:
            name_node = self.get_name(node)
            name = name_node.node_text()

            # If we have arguments, include a placeholder
            has_args = False
            for _ in self.get_arguments(node):
                has_args = True
                break

            # Create a representation of the decorator
            decorator_repr = f"@{name}{'(...)' if has_args else ''}"

            # If we have a parent, prepend it
            if parent:
                return f"{parent}.{decorator_repr}"

            # Try to get the target
            target = self.get_target(node)
            if target:
                target_type = self.get_target_type(node)
                if target_type and hasattr(target.node, "children"):
                    # Find the name of the target
                    for child in target.node.children:
                        if child.type == "identifier":
                            target_name = child.text.decode("utf-8") if child.text else ""
                            return f"{target_type}[{target_name}].{decorator_repr}"

            return decorator_repr
        except ValueError:
            return f"decorator@{node.byte_start}"

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for a Python decorator.

        This normalizes whitespace and strips the @ symbol.

        Args:
            node: The decorator node to get bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """

        # Extract the node's bytes
        node_bytes = source[node.byte_start:node.byte_end]

        # Remove the leading @ and normalize whitespace
        normalized = re.sub(
            b"^\\s*@\\s*",  # Remove leading @ and whitespace
            b"",  # Replace with empty string
            node_bytes,  # Input
            flags=re.MULTILINE,  # Multi-line mode
        )

        # Remove Python comments
        normalized = re.sub(
            b"#.*?$",  # Remove comments
            b"",  # Replace with empty string
            normalized,  # Input
            flags=re.MULTILINE,  # Multi-line mode
        )

        # Normalize whitespace
        normalized = re.sub(b"\\s+", b" ", normalized)

        # Remove trailing/leading whitespace
        normalized = normalized.strip()

        return normalized
