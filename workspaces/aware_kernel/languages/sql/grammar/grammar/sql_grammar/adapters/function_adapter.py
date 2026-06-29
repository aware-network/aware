"""SQL implementation of the CodeSectionFunctionAdapter."""

from collections.abc import Iterable

# Tree-sitter
from tree_sitter import Node, Query
from typing_extensions import override

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.function.adapter import CodeSectionFunctionAdapter

from sql_grammar._tree_sitter_sql import SQL_LANGUAGE

# Aware SQL
from sql_grammar.primitive_codec import PRIMITIVE_TYPE_NODES


class SQLFunctionAdapter(CodeSectionFunctionAdapter[Node]):
    """
    Implementation of CodeSectionFunctionAdapter for SQL using Tree-sitter.

    Extracts function definitions from SQL parse trees.
    """

    # Pre-compiled queries based on the actual SQL tree structure
    FUNCTION_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_function) @function
    """
    )

    FUNCTION_NAME_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_function
          (object_reference
            (identifier) @schema_name
            .
            (identifier) @function_name))
    """
    )

    FUNCTION_NAME_QUERY_NO_SCHEMA: Query = SQL_LANGUAGE.query(
        """
        (create_function
          (object_reference) @function_name)
    """
    )

    FUNCTION_ARGS_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_function
          (function_arguments) @params)
    """
    )

    FUNCTION_BODY_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_function
          (function_body) @body)
    """
    )

    RETURN_TYPE_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_function
          (keyword_returns)
          (_) @return_type)
        """
    )

    PARAM_QUERY: Query = SQL_LANGUAGE.query(
        """
        (function_argument) @param
    """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all CREATE FUNCTION statements in the SQL.

        Args:
            root: The root node of the parse tree
            source: The SQL source code as bytes

        Returns:
            Iterable of nodes representing function definitions
        """
        captures = self.FUNCTION_QUERY.captures(root)
        if "function" in captures:
            for function_node in captures["function"]:
                yield CodeNode(node=function_node, byte_start=function_node.start_byte, byte_end=function_node.end_byte)

    @override
    def get_name(self, function_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the function name from a CREATE FUNCTION statement.
        Returns only the function name part (without schema).

        Args:
            function_node: Node representing a CREATE FUNCTION statement

        Returns:
            Node representing the function name
        """
        captures = self.FUNCTION_NAME_QUERY.captures(function_node.node)
        if "function_name" in captures and captures["function_name"]:
            name_node = captures["function_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # Fallback for cases where the function might not have a schema
        obj_captures = self.FUNCTION_NAME_QUERY_NO_SCHEMA.captures(function_node.node)
        if "function_name" in obj_captures and obj_captures["function_name"]:
            obj_ref_node = obj_captures["function_name"][0]
            # Try to find the last identifier in the object reference (the function name)
            for child in reversed(list(obj_ref_node.children)):
                if child.type == "identifier":
                    return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
            # If no identifier is found, return the whole object reference
            return CodeNode(node=obj_ref_node, byte_start=obj_ref_node.start_byte, byte_end=obj_ref_node.end_byte)

        # Last resort fallback
        return CodeNode(node=function_node.node, byte_start=function_node.byte_start, byte_end=function_node.byte_start)

    @override
    def get_signature(self, function_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the parameter list from a CREATE FUNCTION statement.

        Args:
            function_node: Node representing a CREATE FUNCTION statement

        Returns:
            Node representing the parameter list
        """
        captures = self.FUNCTION_ARGS_QUERY.captures(function_node.node)
        if "params" in captures and captures["params"]:
            params_node = captures["params"][0]
            return CodeNode(node=params_node, byte_start=params_node.start_byte, byte_end=params_node.end_byte)

        # Fallback - empty params
        name_node = self.get_name(function_node)
        return CodeNode(
            node=function_node.node,
            byte_start=name_node.byte_end,
            byte_end=name_node.byte_end + 2,  # Assuming "()" would be right after name
        )

    @override
    def get_body(self, function_node: CodeNode[Node]) -> CodeNode[Node] | None:
        """
        Extract the body from a CREATE FUNCTION statement.

        Args:
            function_node: Node representing a CREATE FUNCTION statement

        Returns:
            Node representing the start of the function body
        """
        captures = self.FUNCTION_BODY_QUERY.captures(function_node.node)
        if "body" in captures and captures["body"]:
            body_node = captures["body"][0]
            return CodeNode(node=body_node, byte_start=body_node.start_byte, byte_end=body_node.end_byte)
        return None

    @override
    def get_parameters(self, function_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract parameter nodes from a CREATE FUNCTION statement.

        Args:
            function_node: Node representing a CREATE FUNCTION statement

        Returns:
            Iterable of nodes representing function parameters
        """
        signature_node = self.get_signature(function_node)

        captures = self.PARAM_QUERY.captures(signature_node.node)
        if "param" in captures:
            for param_node in captures["param"]:
                yield CodeNode(node=param_node, byte_start=param_node.start_byte, byte_end=param_node.end_byte)

    @override
    def get_return_type(self, function_node: CodeNode[Node]) -> CodeNode[Node] | None:
        """
        Extract the return type from a CREATE FUNCTION statement.

        Args:
            function_node: Node representing a CREATE FUNCTION statement

        Returns:
            Node representing the return type
        """
        captures = self.RETURN_TYPE_QUERY.captures(function_node.node)
        if captures and "return_type" in captures and captures["return_type"]:
            return_type_node = captures["return_type"][0]
            if return_type_node.type in PRIMITIVE_TYPE_NODES:
                return CodeNode(
                    node=return_type_node, byte_start=return_type_node.start_byte, byte_end=return_type_node.end_byte
                )

        return None

    @override
    def is_async(self, function_node: CodeNode[Node]) -> bool:
        """
        SQL functions are not async in the same way as Python functions.

        Args:
            function_node: Node representing a CREATE FUNCTION statement

        Returns:
            False for SQL functions
        """
        return False

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a fully-qualified name for a SQL function.

        For SQL functions, this is typically schema.function_name(arg_types)

        Args:
            node: The function node to get the qualified name for
            parent: Optional parent name (unused for SQL functions)

        Returns:
            Qualified name string for the function
        """
        return self._get_full_function_name(node)

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for a SQL function.

        This strips comments and normalizes whitespace to create a consistent
        hash regardless of formatting changes.

        Args:
            node: The function node to get body bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        import re

        # Extract the node's bytes
        node_bytes = source[node.byte_start:node.byte_end]

        # Remove SQL comments
        normalized = re.sub(
            b"--.*?$|/\\*.*?\\*/",  # Remove single-line and multi-line comments
            b"",  # Replace with empty string
            node_bytes,  # Input
            flags=re.MULTILINE | re.DOTALL,  # Multi-line mode
        )

        # Normalize whitespace
        normalized = re.sub(b"\\s+", b" ", normalized)

        # Remove trailing/leading whitespace
        normalized = normalized.strip()

        return normalized

    def _get_full_function_name(self, function_node: CodeNode[Node]) -> str:
        """
        Helper method to extract the full function name including schema.

        Args:
            function_node: Node representing a CREATE FUNCTION statement

        Returns:
            Full function name as string
        """
        # Try to get schema name
        schema = "public"  # Default schema
        captures = self.FUNCTION_NAME_QUERY.captures(function_node.node)
        if "schema_name" in captures and captures["schema_name"]:
            schema_text = captures["schema_name"][0].text
            if schema_text is not None:
                schema = schema_text.decode("utf-8")

        if "function_name" in captures and captures["function_name"]:
            name_text = captures["function_name"][0].text
            if name_text is not None:
                return f"{schema}.{name_text.decode('utf-8')}"

        # Try fallback for cases where the function might not have a schema qualifier
        obj_captures = self.FUNCTION_NAME_QUERY_NO_SCHEMA.captures(function_node.node)
        if "function_name" in obj_captures and obj_captures["function_name"]:
            obj_ref_node = obj_captures["function_name"][0]
            # For simple identifiers
            if obj_ref_node.type == "identifier":
                obj_ref_text = obj_ref_node.text
                if obj_ref_text is not None:
                    return f"{schema}.{obj_ref_text.decode('utf-8')}"

            # For object_reference nodes, extract the identifier
            for child in obj_ref_node.children:
                if child.type == "identifier":
                    child_text = child.text
                    if child_text is not None:
                        return f"{schema}.{child_text.decode('utf-8')}"

        # Scan directly for the function name after "FUNCTION" keyword
        for child in function_node.node.children:
            if child.type == "object_reference":
                # Handle both cases - with schema qualifier and without
                identifiers = [c for c in child.children if c.type == "identifier"]
                if len(identifiers) > 1:
                    # Has schema qualifier: schema.function
                    schema = identifiers[0].text.decode("utf-8") if identifiers[0].text else ""
                    name = identifiers[1].text.decode("utf-8") if identifiers[1].text else ""
                    return f"{schema}.{name}"
                elif len(identifiers) == 1:
                    # Just function name without schema
                    name = identifiers[0].text.decode("utf-8") if identifiers[0].text else ""
                    return f"{schema}.{name}"

        # If we reach here, we couldn't find a function name
        raise ValueError(f"No function name found in CREATE FUNCTION statement. Node: {function_node.node_text()}")

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        return self._get_full_function_name(node)
