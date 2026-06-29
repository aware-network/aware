"""Aware implementation of the CodeSectionFunctionAdapter."""

from collections.abc import Iterable, Iterator
import re
from typing_extensions import override
from typing import final

# Tree-sitter
from tree_sitter import Node
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

# Aware Primitive Code
from aware_code.section.function.adapter import CodeSectionFunctionAdapter
from aware_code.node.node import CodeNode


@final
class AwareFunctionAdapter(CodeSectionFunctionAdapter[Node]):
    """
    Implementation of CodeSectionFunctionAdapter for Aware language using Tree-sitter.

    Maps 'fn' definitions in Aware to function sections.
    """

    # Pre-compiled queries
    FN_QUERY = AWARE_LANGUAGE.query(
        """
        (fn_def) @function
        """
    )

    FN_NAME_QUERY = AWARE_LANGUAGE.query(
        """
        (fn_def
          name: (ident) @fn_name)
        """
    )

    FN_SIG_QUERY = AWARE_LANGUAGE.query(
        """
        (fn_def
          sig: (signature) @signature)
        """
    )

    FN_VERB_QUERY = AWARE_LANGUAGE.query(
        """
        (fn_def
          verb: (ident) @fn_verb)
        """
    )

    PARAM_QUERY = AWARE_LANGUAGE.query(
        """
        (signature
          (input_attr) @param)
        """
    )

    RETURN_TYPE_QUERY = AWARE_LANGUAGE.query(
        """
        (signature
          return_clause: (return_clause) @return_type)
        """
    )

    RETURN_PARAMS_QUERY = AWARE_LANGUAGE.query(
        """
        (signature
          return_clause: (return_clause
            (return_tuple
              (output_attr) @out_param)))
        """
    )

    BLOCK_QUERY = AWARE_LANGUAGE.query(
        """
        (fn_def
          (block) @block)
        """
    )

    ASYNC_QUERY = AWARE_LANGUAGE.query(
        """
        (fn_def
          "async" @async_kw)
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all function definitions in the Aware source.

        Args:
            root: The root node of the parse tree
            source: The source code as bytes

        Returns:
            Iterable of nodes representing function definitions
        """
        # Use pre-compiled query
        captures = self.FN_QUERY.captures(root)
        if "function" in captures:
            for fn_node in captures["function"]:
                # Only return top-level functions here, not methods inside types
                if fn_node.parent and fn_node.parent.type == "source_file":
                    yield CodeNode(node=fn_node, byte_start=fn_node.start_byte, byte_end=fn_node.end_byte)

    @override
    def get_name(self, function_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the function name from a function definition.

        Args:
            function_node: Node representing a function definition

        Returns:
            Node representing the function name
        """
        # Use pre-compiled query
        captures = self.FN_NAME_QUERY.captures(function_node.node)
        if "fn_name" in captures and captures["fn_name"]:
            name_node = captures["fn_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # Fallback - should not happen with valid syntax
        raise ValueError("No function name found in function definition")

    @override
    def get_signature(self, function_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the signature from a function definition.

        Args:
            function_node: Node representing a function definition

        Returns:
            Node representing the function signature
        """
        # Use pre-compiled query
        captures = self.FN_SIG_QUERY.captures(function_node.node)
        if "signature" in captures and captures["signature"]:
            sig_node = captures["signature"][0]
            return CodeNode(node=sig_node, byte_start=sig_node.start_byte, byte_end=sig_node.end_byte)

        # Fallback - should not happen with valid syntax
        raise ValueError("No signature found in function definition")

    @override
    def get_parameters(self, function_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract parameter nodes from a function definition.

        Args:
            function_node: Node representing a function definition

        Returns:
            Iterable of nodes representing function parameters
        """
        signature_node = self.get_signature(function_node)

        # Walk the signature subtree manually to avoid cross-function query bleed.
        def _walk(node: Node) -> Iterator[Node]:
            if node.type == "input_attr":
                yield node
            for child in node.children:
                yield from _walk(child)

        for param_node in _walk(signature_node.node):
            yield CodeNode(node=param_node, byte_start=param_node.start_byte, byte_end=param_node.end_byte)

    @override
    def get_return_type(self, function_node: CodeNode[Node]) -> CodeNode[Node] | None:
        """
        Extract the return type from a function definition.

        Args:
            function_node: Node representing a function definition

        Returns:
            Node representing the return type
        """
        signature_node = self.get_signature(function_node)

        # Use pre-compiled query
        captures = self.RETURN_TYPE_QUERY.captures(signature_node.node)
        if "return_type" in captures and captures["return_type"]:
            return_node = captures["return_type"][0]
            return CodeNode(node=return_node, byte_start=return_node.start_byte, byte_end=return_node.end_byte)

        return None

    @override
    def get_return_parameters(self, function_node: CodeNode[Node]) -> Iterable[CodeNode[Node]] | None:
        """
        Return named return parameters (output attributes) for functions that use tuple returns.

        For single return types (type_ref), returns None.
        """
        signature_node = self.get_signature(function_node)

        captures = self.RETURN_PARAMS_QUERY.captures(signature_node.node)
        out_nodes = captures.get("out_param", [])
        if not out_nodes:
            return None

        return [CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte) for n in out_nodes]

    @override
    def get_body(self, function_node: CodeNode[Node]) -> CodeNode[Node] | None:
        """
        Extract the body from a function definition if present.

        Args:
            function_node: Node representing a function definition

        Returns:
            Node representing the function body or None if not present
        """
        # Use pre-compiled query
        captures = self.BLOCK_QUERY.captures(function_node.node)
        if "block" in captures and captures["block"]:
            block_node = captures["block"][0]
            return CodeNode(node=block_node, byte_start=block_node.start_byte, byte_end=block_node.end_byte)

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
        captures = self.ASYNC_QUERY.captures(function_node.node)
        return "async_kw" in captures and len(captures["async_kw"]) > 0

    @override
    def get_verb(self, function_node: CodeNode[Node]) -> str | None:
        captures = self.FN_VERB_QUERY.captures(function_node.node)
        if "fn_verb" in captures and captures["fn_verb"]:
            verb_node = captures["fn_verb"][0]
            return verb_node.text.decode("utf-8") if verb_node.text is not None else None
        return None

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a fully-qualified name for an Aware function.

        Args:
            node: The function node to get the qualified name for
            parent: Optional parent type name

        Returns:
            Qualified name string
        """
        # Get function name
        name_node = self.get_name(node)
        name_text = name_node.node_text()

        # If we have a parent type, prepend it (for methods)
        if parent:
            return f"{parent}.{name_text}"

        return name_text

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for an Aware function definition.

        This strips comments and normalizes whitespace.

        Args:
            node: The function node to get body bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        # Extract the node's bytes
        node_bytes = source[node.byte_start:node.byte_end]

        # Remove comments
        normalized = re.sub(
            b"//[^\n]*",  # Remove single-line comments
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
