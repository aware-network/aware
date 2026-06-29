"""Python implementation of the CodeSectionFunctionAdapter."""

from __future__ import annotations
from collections.abc import Iterable
import re
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query
from python_grammar._tree_sitter_python import PYTHON_LANGUAGE

# Aware Primitive Code
from aware_code.section.function.adapter import CodeSectionFunctionAdapter
from aware_code.node.node import CodeNode


class PythonFunctionAdapter(CodeSectionFunctionAdapter[Node]):
    """
    Implementation of CodeSectionFunctionAdapter for Python using Tree-sitter.

    Extracts function definitions from Python parse trees.
    """

    # Pre-compiled queries for finding functions
    FUNCTION_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (function_definition) @function
        """
    )

    FUNCTION_NAME_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (function_definition
          name: (identifier) @function_name)
        """
    )

    FUNCTION_ASYNC_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (function_definition
          "async" @async_keyword)
        """
    )

    FUNCTION_PARAMETERS_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (function_definition
          parameters: (parameters) @parameters)
        """
    )

    PARAMETER_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (parameters
          (_) @param)
        """
    )

    # Use a more specific query to get individual parameters
    # Exclude parentheses, commas, etc.
    PARAMETER_DETAILED_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (parameters
            [(identifier) @param
            (typed_parameter) @param
            (default_parameter) @param
            (typed_default_parameter) @param
            (list_splat_pattern) @param
            (dictionary_splat_pattern) @param
            (positional_separator) @param
            (keyword_separator) @param])
        """
    )

    FUNCTION_BODY_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (function_definition
          body: (block) @body)
        """
    )

    FUNCTION_DOCSTRING_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (function_definition
          body: (block
            (expression_statement
              (string) @docstring)))
        """
    )

    FUNCTION_RETURN_TYPE_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (function_definition
          return_type: (type) @return_type)
        """
    )

    @staticmethod
    def _decode_node_text(node: Node) -> str:
        text = node.text
        if text is None:
            return ""
        return text.decode("utf-8")

    def is_method(self, function_node: CodeNode[Node]) -> bool:
        """
        Check if a function is a method (defined inside a class).

        Args:
            function_node: Node representing a function definition

        Returns:
            True if the function is a method, False otherwise
        """
        # Robust ancestry check to handle decorated methods as well
        current = function_node.node.parent
        while current is not None:
            if current.type == "class_definition":
                return True
            current = current.parent
        return False

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all module-level function definitions in the parse tree.

        This method specifically targets functions defined at the module level,
        excluding methods (functions inside classes) and nested functions
        (functions defined inside other functions).

        Args:
            root: The root node of the parse tree
            source: The source code as bytes

        Returns:
            Iterable of nodes representing module-level function definitions
        """
        captures = self.FUNCTION_QUERY.captures(root)
        if "function" in captures:
            for function_node in captures["function"]:
                # Check if this is a module-level function
                if self._is_module_level_function(function_node):
                    yield CodeNode(
                        node=function_node, byte_start=function_node.start_byte, byte_end=function_node.end_byte
                    )

    def _is_module_level_function(self, node: Node) -> bool:
        """
        Determine if a function node is defined at the module level.

        A module-level function is one that:
        1. Is not inside a class (not a method)
        2. Is not inside another function (not a nested function)
        3. Is typically inside a module node or other top-level container

        Args:
            node: The function node to check

        Returns:
            True if the function is a module-level function, False otherwise
        """
        if not node or not node.parent:
            return False

        # Get the parent of the function
        parent = node.parent

        # If the function is directly under the module or a direct child of the root
        # This is the typical case for module-level functions
        if parent.type == "module" or parent.type == "program":
            return True

        # For functions inside blocks, we need to check the ancestry
        if parent.type == "block":
            # Check if parent's parent is a class - if so, this is a method
            if parent.parent and parent.parent.type == "class_definition":
                return False

            # Check if parent's parent is another function - if so, this is a nested function
            if parent.parent and parent.parent.type == "function_definition":
                return False

            # If we're inside a block that's directly under the module,
            # this is still a module-level function
            if parent.parent and (parent.parent.type == "module" or parent.parent.type == "program"):
                return True

        # For any other case, we check the full ancestry to make sure we're not
        # inside a class or another function
        current: Node | None = parent
        while current:
            if current.type == "class_definition" or current.type == "function_definition":
                return False
            current = current.parent

        # If we didn't find any class or function in the ancestry,
        # this is likely a module-level function
        return True

    @override
    def get_name(self, function_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the name from a function definition.

        Args:
            function_node: Node representing a function definition

        Returns:
            Node representing the function name
        """
        captures = self.FUNCTION_NAME_QUERY.captures(function_node.node)
        if "function_name" in captures and captures["function_name"]:
            name_node = captures["function_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # Fallback if query fails
        for child in function_node.node.children:
            if child.type == "identifier":
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

        raise ValueError("No function name found in function definition")

    @override
    def get_signature(self, function_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the parameter list from a function definition.

        Args:
            function_node: Node representing a function definition

        Returns:
            Node representing the parameter list
        """
        captures = self.FUNCTION_PARAMETERS_QUERY.captures(function_node.node)
        if "parameters" in captures and captures["parameters"]:
            params_node = captures["parameters"][0]
            return CodeNode(node=params_node, byte_start=params_node.start_byte, byte_end=params_node.end_byte)

        # Fallback if query fails - try to find parameters node manually
        for child in function_node.node.children:
            if child.type == "parameters":
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

        # If no parameters are found, return an empty signature node
        name_node = self.get_name(function_node)
        return CodeNode(
            node=function_node.node,
            byte_start=name_node.byte_end,
            byte_end=name_node.byte_end + 2,  # Assuming "()" would be right after name
        )

    @override
    def get_parameters(self, function_node: CodeNode[Node], exclude_self: bool = True) -> Iterable[CodeNode[Node]]:
        """
        Extract parameter nodes from a function definition.

        Args:
            function_node: Node representing a function definition
            exclude_self: If True, exclude the 'self' parameter for methods

        Returns:
            Iterable of nodes representing function parameters
        """
        sig_node = self.get_signature(function_node)
        captures = self.PARAMETER_DETAILED_QUERY.captures(sig_node.node)

        # If we need to exclude implicit receiver in methods (self/cls)
        should_skip_first = exclude_self and self.is_method(function_node)

        if "param" in captures:
            # Ensure deterministic left-to-right order by byte_start
            ordered = sorted(captures["param"], key=lambda n: n.start_byte)
            first_param = True
            for param_node in ordered:
                # Skip parameters that aren't actual parameters (like commas)
                if param_node.type not in [
                    "identifier",
                    "typed_parameter",
                    "default_parameter",
                    "typed_default_parameter",
                ]:
                    continue

                # Skip first parameter if it's a method and we're excluding implicit receiver
                if should_skip_first and first_param:
                    # Check if it's actually 'self' or 'cls'
                    param_text = self._decode_node_text(param_node)
                    if (
                        param_text in ("self", "cls")
                        or self._is_self_param(param_node)
                        or self._is_cls_param(param_node)
                    ):
                        first_param = False
                        continue

                first_param = False
                yield CodeNode(node=param_node, byte_start=param_node.start_byte, byte_end=param_node.end_byte)

    def _is_self_param(self, param_node: Node) -> bool:
        """
        Check if a parameter node is the 'self' parameter.

        Args:
            param_node: Node representing a parameter

        Returns:
            True if it's the self parameter, False otherwise
        """
        # For simple identifier parameters
        if param_node.type == "identifier":
            return param_node.text == b"self"

        # For typed parameters
        if param_node.type == "typed_parameter":
            for child in param_node.children:
                if child.type == "identifier" and child.text == b"self":
                    return True

        return False

    def _is_cls_param(self, param_node: Node) -> bool:
        """
        Check if a parameter node is the 'cls' parameter.

        Args:
            param_node: Node representing a parameter

        Returns:
            True if it's the cls parameter, False otherwise
        """
        if param_node.type == "identifier":
            return param_node.text == b"cls"

        if param_node.type == "typed_parameter":
            for child in param_node.children:
                if child.type == "identifier" and child.text == b"cls":
                    return True

        return False

    @override
    def get_return_type(self, function_node: CodeNode[Node]) -> CodeNode[Node] | None:
        """
        Extract the return type from a function definition if present.

        Args:
            function_node: Node representing a function definition

        Returns:
            Node representing the return type if present, None otherwise
        """
        captures = self.FUNCTION_RETURN_TYPE_QUERY.captures(function_node.node)
        if "return_type" in captures and captures["return_type"]:
            type_node = captures["return_type"][0]
            return CodeNode(node=type_node, byte_start=type_node.start_byte, byte_end=type_node.end_byte)

        # Manually search for return type
        for i, child in enumerate(function_node.node.children):
            if child.type == "->":
                if i + 1 < len(function_node.node.children):
                    type_node = function_node.node.children[i + 1]
                    return CodeNode(node=type_node, byte_start=type_node.start_byte, byte_end=type_node.end_byte)

        return None

    @override
    def get_body(self, function_node: CodeNode[Node]) -> CodeNode[Node] | None:
        """
        Extract the body from a function definition.

        Args:
            function_node: Node representing a function definition

        Returns:
            Node representing the function body
        """
        captures = self.FUNCTION_BODY_QUERY.captures(function_node.node)
        if "body" in captures and captures["body"]:
            body_node = captures["body"][0]
            return CodeNode(node=body_node, byte_start=body_node.start_byte, byte_end=body_node.end_byte)

        # Fallback - manual search for body
        for child in function_node.node.children:
            if child.type == "block":
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

        return None

    @override
    def is_async(self, function_node: CodeNode[Node]) -> bool:
        """
        Check if a function is asynchronous.

        Args:
            function_node: Node representing a function definition

        Returns:
            True if the function is marked with 'async', False otherwise
        """
        captures = self.FUNCTION_ASYNC_QUERY.captures(function_node.node)
        return bool(captures.get("async_keyword"))

    @override
    def is_public(self, function_node: CodeNode[Node]) -> bool:
        name_node = self.get_name(function_node)
        name = name_node.node_text()
        return not name.startswith("_")

    @override
    def is_classmethod(self, function_node: CodeNode[Node]) -> bool:
        """
        Return whether the function is a class method.
        Default: False. Language adapters can override for accuracy.
        """
        first_param = self.get_first_parameter(function_node)
        if first_param is None:
            return False
        return self._is_cls_param(first_param)

    @override
    def is_staticmethod(self, function_node: CodeNode[Node]) -> bool:
        """
        Return whether the function is a static method.
        Default: False. Language adapters can override for accuracy.
        """
        # Module-level functions → static
        if not self.is_method(function_node):
            return True

        first_param = self.get_first_parameter(function_node)
        if first_param is None:
            # No params on a method likely indicates a staticmethod
            return True

        if not self._is_cls_param(first_param) and not self._is_self_param(first_param):
            return True
        return False

    def get_first_parameter(self, function_node: CodeNode[Node]) -> Node | None:
        """
        Get the first parameter of a function.

        Args:
            function_node: Node representing a function definition

        Returns:
            Node representing the first parameter, None if no parameter is found
        """
        # For methods, infer by first raw parameter
        sig_node = self.get_signature(function_node)
        captures = self.PARAMETER_DETAILED_QUERY.captures(sig_node.node)
        for param_node in captures.get("param", []):
            if param_node.type in [
                "identifier",
                "typed_parameter",
                "default_parameter",
                "typed_default_parameter",
            ]:
                return param_node
        return None

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a fully-qualified name for a Python function.

        For methods, this includes the class name.
        For module functions, this includes the module name.

        Args:
            node: The function node to get the qualified name for
            parent: Optional parent name (class name for methods)

        Returns:
            Qualified name string
        """
        name_node = self.get_name(node)
        function_name = name_node.node_text()

        # Combine with parent if available
        if parent:
            return f"{parent}.{function_name}"

        # Detect method robustly: function_definition can be wrapped (e.g., async, decorators)
        # so we walk ancestors until we find a class_definition, but abort if we hit another
        # function_definition first (nested function).
        current = node.node.parent
        while current is not None:
            if current.type == "function_definition":
                # Nested function: don't qualify with class name
                break
            if current.type == "class_definition":
                cls_node = current
                parent_name: str | None = None
                for ch in cls_node.children:
                    if ch.type == "identifier" and ch.text:
                        parent_name = self._decode_node_text(ch)
                        break
                if parent_name:
                    return f"{parent_name}.{function_name}"
                # If class name can't be extracted, fall back to unqualified
                break
            current = current.parent
        # Default to just the function name if no module info is available
        return function_name

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for a Python function definition.

        This strips comments and normalizes whitespace to ensure consistent hashing
        regardless of formatting changes.

        Args:
            node: The function node to get body bytes for
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
        """
        Return a reference string for this function that can be used to match comments.

        Args:
            node: The function node
            parent: Optional parent context (e.g., type name for methods)

        Returns:
            Reference string for comment matching
        """
        # Delegate to qualname method for consistent lookup keys
        return self.qualname(node, parent)
