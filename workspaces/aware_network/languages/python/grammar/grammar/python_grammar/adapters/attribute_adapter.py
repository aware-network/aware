"""Python implementation of the CodeSectionAttributeAdapter."""

from collections.abc import Iterable
from typing_extensions import override

# Aware Core
from aware_utils.logging import logger

# Tree-sitter
from tree_sitter import Node, Query
from python_grammar._tree_sitter_python import PYTHON_LANGUAGE

# Aware Primitive Code
from aware_code.node.node import CodeNode
from aware_code.section.attribute.adapter import CodeSectionAttributeAdapter

SKIP_PARAMETER_TYPES = ["self", "cls"]


def debug_node(node: Node, depth: int = 0) -> None:
    indent = " " * (2 * depth)
    if node.text:
        logger.info(f"{indent}{node.text.decode('utf-8'):<25}:{node.type}")
    else:
        logger.info(f"{indent}{node.type:<25}")
    for child in node.children:
        debug_node(child, depth + 1)


class PythonAttributeAdapter(CodeSectionAttributeAdapter[Node]):
    """
    Implementation of CodeSectionAttributeAdapter for Python using Tree-sitter.

    Extracts class attributes, instance attributes, and typed variables from Python parse trees.
    """

    # For typed attributes
    TYPED_ATTRIBUTE_TYPE_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (assignment
            type: (type) @attr_type)
        """
    )

    # For typed parameters
    TYPED_PARAMETER_TYPE_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (typed_parameter
            type: (type) @param_type)
        """
    )

    # For typed default parameters
    TYPED_DEFAULT_PARAM_TYPE_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (typed_default_parameter
          type: (type) @param_type)
        """
    )

    TYPED_DEFAULT_PARAMETER_VALUE_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (typed_default_parameter
            value: (_) @default_value)
        """
    )

    # For default parameters
    DEFAULT_PARAMETER_VALUE_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (default_parameter
            value: (_) @default_value)
        """
    )

    # For attributes (look for identifiers in assignments)
    ASSIGNMENT_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (assignment
            left: (identifier) @attr_name)
        """
    )

    # For attributes accessed via self (instance attributes)
    ASSIGNMENT_LEFT_ATTRIBUTE_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (assignment
            left: (attribute
            attribute: (identifier) @attr_name))
        """
    )

    ASSIGNMENT_RIGHT_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (assignment
            right: (_) @default_value)
        """
    )

    PARAMETER_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (parameter
            (identifier) @param_name)
        """
    )

    # Find module-level assignments (variables)
    MODULE_VAR_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (module
            (expression_statement
            (assignment
                left: (identifier) @var_name))) @module
        """
    )

    # Query to find Field() calls with keyword arguments
    FIELD_CALL_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (call
          function: (identifier) @func
          arguments: (argument_list) @args)
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all top-level attributes in Python.

        For Python, standalone attributes might be module-level variables.
        Most attributes in Python are class attributes and instance attributes.

        Args:
            root: The root node of the parse tree
            source: The Python source code as bytes

        Returns:
            Iterable of nodes representing top-level attributes
        """
        # Find module-level assignments (variables)
        captures = self.MODULE_VAR_QUERY.captures(root)
        if "var_name" in captures:
            for var_name_node in captures["var_name"]:
                if (
                    hasattr(var_name_node, "parent")
                    and var_name_node.parent
                    and hasattr(var_name_node.parent, "parent")
                ):
                    assignment_node = var_name_node.parent
                    yield CodeNode(
                        node=assignment_node,
                        byte_start=assignment_node.start_byte,
                        byte_end=assignment_node.end_byte,
                    )

    def _field_kwargs(self, node: Node) -> dict[str, str]:
        """
        Return the keyword arguments passed to a Pydantic Field(…) call on the right-hand side of an assignment.

        The Tree-sitter structure for a typed assignment like
            title: str = Field(unique=True)
        is roughly:
            (assignment
                (identifier)            ; left
                :
                (type
                  (identifier) …)
                =
                (call                    ; <── we are interested in this node
                  (identifier)           ; "Field"
                  (argument_list
                    (keyword_argument
                      (identifier)       ; kw name
                      =
                      (true))))          ; kw value

        Therefore we only need to:
        1. Make sure we're looking at an ``assignment`` node.
        2. Find the first direct child of type ``call`` whose first child identifier is ``Field``.
        3. Iterate over its ``argument_list`` children and collect any ``keyword_argument`` pairs.
        """
        kwargs: dict[str, str] = {}

        if node.type != "assignment":
            return kwargs

        # Step 1 ‑ locate the ``call`` node on the RHS.
        call_node: Node | None = None
        for child in node.children:
            if child.type == "call":
                call_node = child
                break
        if call_node is None:
            return kwargs

        # Step 2 ‑ ensure the call is to ``Field``.
        #   The first named child inside the call should be the identifier ``Field``.
        first_named_child = next((c for c in call_node.children if c.is_named), None)
        if (
            first_named_child is None
            or first_named_child.type != "identifier"
            or first_named_child.text
            and first_named_child.text.decode("utf-8") != "Field"
        ):
            return kwargs

        # Step 3 ‑ obtain the argument list.
        arg_list = next((c for c in call_node.children if c.type == "argument_list"), None)
        if arg_list is None:
            return kwargs

        # Step 4 ‑ iterate over keyword arguments.
        for kwarg in (c for c in arg_list.children if c.type == "keyword_argument"):
            # Expected structure: (keyword_argument (identifier) = <value_node>)
            # First named child is the identifier (keyword name)
            name_node = next((c for c in kwarg.children if c.type == "identifier"), None)
            if name_node is None:
                continue
            key_name = name_node.text.decode("utf-8") if name_node.text else ""

            # Value node is the last named child in the keyword_argument
            value_node = None
            for c in reversed(kwarg.children):
                if c.is_named and c.type not in {"identifier"}:  # skip the name part
                    value_node = c
                    break
            if value_node is None:
                continue
            kwargs[key_name] = value_node.text.decode("utf-8") if value_node.text else ""

        return kwargs

    @override
    def get_name(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node]:
        """
        Extract the name from an attribute or parameter.

        Args:
            attribute_node: Node representing an attribute or parameter
            is_parameter: Flag indicating if this is a parameter (vs attribute)

        Returns:
            Node representing the attribute name
        """
        if is_parameter:
            # For function parameters
            captures = self.PARAMETER_QUERY.captures(attribute_node.node)
            if "param_name" in captures and captures["param_name"]:
                name_node = captures["param_name"][0]
                return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

            # Add specific handling for typed_default_parameter
            if attribute_node.node.type == "typed_default_parameter":
                for child in attribute_node.node.children:
                    if child.type == "identifier":
                        return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
        else:
            # For attributes (look for identifiers in assignments)
            captures = self.ASSIGNMENT_QUERY.captures(attribute_node.node)
            if "attr_name" in captures and captures["attr_name"]:
                name_node = captures["attr_name"][0]
                return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

            # For attributes accessed via self (instance attributes)
            captures = self.ASSIGNMENT_LEFT_ATTRIBUTE_QUERY.captures(attribute_node.node)
            if "attr_name" in captures and captures["attr_name"]:
                name_node = captures["attr_name"][0]
                return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # If we can't find a name with the queries, try to navigate the nodes manually
        if attribute_node.node.type == "assignment":
            for child in attribute_node.node.children:
                if child.type == "identifier":
                    return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
                elif child.type == "attribute" and len(child.children) >= 3:
                    # Attribute node typically has: object, '.', attribute
                    attr_node = child.children[2]
                    return CodeNode(node=attr_node, byte_start=attr_node.start_byte, byte_end=attr_node.end_byte)
        if attribute_node.node.type == "identifier":
            return CodeNode(
                node=attribute_node.node,
                byte_start=attribute_node.node.start_byte,
                byte_end=attribute_node.node.end_byte,
            )

        debug_node(attribute_node.node)
        node_text = attribute_node.node.text.decode("utf-8") if attribute_node.node.text else ""
        raise ValueError(
            "Could not find name in "
            + f"{'parameter' if is_parameter else 'attribute'} node: "
            + f"{attribute_node.node.type}, text: {node_text}"
        )

    @override
    def get_type(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node] | None:
        """
        Extract the type from an attribute or parameter.

        Args:
            attribute_node: Node representing an attribute or parameter
            is_parameter: Flag indicating if this is a parameter (vs attribute)

        Returns:
            Node representing the attribute type
        """
        if is_parameter:
            if attribute_node.node_text() in SKIP_PARAMETER_TYPES:
                return None

            # For typed parameters
            captures = self.TYPED_PARAMETER_TYPE_QUERY.captures(attribute_node.node)
            if "param_type" in captures and captures["param_type"]:
                type_node = captures["param_type"][0]
                return CodeNode(node=type_node, byte_start=type_node.start_byte, byte_end=type_node.end_byte)

            # For typed default parameters (like those used in decorators)
            if attribute_node.node.type == "typed_default_parameter":
                captures = self.TYPED_DEFAULT_PARAM_TYPE_QUERY.captures(attribute_node.node)
                if "param_type" in captures and captures["param_type"]:
                    type_node = captures["param_type"][0]
                    return CodeNode(node=type_node, byte_start=type_node.start_byte, byte_end=type_node.end_byte)

                # Direct traversal approach as fallback
                for child in attribute_node.node.children:
                    if child.type == "type":
                        return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
        else:
            # For typed attributes
            captures = self.TYPED_ATTRIBUTE_TYPE_QUERY.captures(attribute_node.node)
            if "attr_type" in captures and captures["attr_type"]:
                type_node = captures["attr_type"][0]
                return CodeNode(node=type_node, byte_start=type_node.start_byte, byte_end=type_node.end_byte)

        # Return None if no type is found
        attr_text = attribute_node.node.text.decode("utf-8") if attribute_node.node.text else ""
        logger.debug(
            f"No explicit type found for {attribute_node.node.type}, attribute text: {attr_text}"
        )
        return None

    @override
    def get_default_value(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node] | None:
        """
        Extract the default value from an attribute or parameter if present.

        For attributes with Field() calls, this extracts the default= parameter.
        For other attributes, this returns the entire right-hand side.

        Args:
            attribute_node: Node representing an attribute or parameter
            is_parameter: Flag indicating if this is a parameter (vs attribute)

        Returns:
            Node representing the default value if present, None otherwise
        """
        if is_parameter:
            # For default parameters
            captures = self.DEFAULT_PARAMETER_VALUE_QUERY.captures(attribute_node.node)
            if "default_value" in captures and captures["default_value"]:
                default_node = captures["default_value"][0]
                return CodeNode(node=default_node, byte_start=default_node.start_byte, byte_end=default_node.end_byte)

            # For typed default parameters
            captures = self.TYPED_DEFAULT_PARAMETER_VALUE_QUERY.captures(attribute_node.node)
            if "default_value" in captures and captures["default_value"]:
                default_node = captures["default_value"][0]
                return CodeNode(node=default_node, byte_start=default_node.start_byte, byte_end=default_node.end_byte)
        else:
            # For attributes with default values
            captures = self.ASSIGNMENT_RIGHT_QUERY.captures(attribute_node.node)
            if "default_value" in captures and captures["default_value"]:
                default_node = captures["default_value"][0]

                # Check if this is a Field() call using the existing _field_kwargs method
                kwargs = self._field_kwargs(attribute_node.node)
                if kwargs and "default" in kwargs:
                    # This is a Field() call with a default parameter
                    # Find the actual node for the default value
                    return self._get_field_default_node(attribute_node.node)

                # Not a Field() call, return the entire right-hand side
                return CodeNode(node=default_node, byte_start=default_node.start_byte, byte_end=default_node.end_byte)

        return None

    def _get_field_default_node(self, assignment_node: Node) -> CodeNode[Node] | None:
        """
        Get the actual CST node for the default= parameter in a Field() call.

        This method assumes the assignment_node contains a Field() call and extracts
        the node representing the value of the default= parameter.

        Args:
            assignment_node: The assignment node containing a Field() call

        Returns:
            CodeNode for the default value, or None if not found
        """
        # Find the call node (Field() call)
        call_node = None
        for child in assignment_node.children:
            if child.type == "call":
                call_node = child
                break

        if not call_node:
            return None

        # Get the argument list
        arg_list = next((c for c in call_node.children if c.type == "argument_list"), None)
        if not arg_list:
            return None

        # Look for keyword_argument with name "default"
        for kwarg in (c for c in arg_list.children if c.type == "keyword_argument"):
            # Find the identifier (keyword name)
            name_node = next((c for c in kwarg.children if c.type == "identifier"), None)
            if name_node and name_node.text and name_node.text.decode("utf-8") == "default":
                # Find the value node (last named child that's not the identifier)
                value_node = None
                for c in reversed(kwarg.children):
                    if c.is_named and c.type != "identifier":
                        value_node = c
                        break
                if value_node:
                    return CodeNode(node=value_node, byte_start=value_node.start_byte, byte_end=value_node.end_byte)

        return None

    @override
    def is_required(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        """
        Check if an attribute is required (not optional).

        For Python parameters, this checks if there's no default value.
        For attributes, this is determined by type annotations or other factors.

        Args:
            attribute_node: Node representing an attribute or parameter
            is_parameter: Flag indicating if this is a parameter (vs attribute)

        Returns:
            True if the attribute is required, False otherwise
        """
        if is_parameter:
            # Parameters are required if they don't have a default value and aren't *args or **kwargs
            return self.get_default_value(attribute_node, is_parameter=True) is None and not (
                attribute_node.node.type in ["list_splat_pattern", "dictionary_splat_pattern"]
            )

        # !! TODO: Reconsider how to determine properly is required.
        try:
            type_node = self.get_type(attribute_node, is_parameter=False)
            if type_node is None:
                # !! Unknown type, default to required
                return True
            type_text = type_node.node_text()
            return "Optional" not in type_text and "Union" not in type_text
        except ValueError:
            # If no type is specified, default to not required
            return False

    @override
    def has_unique(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        """
        Check if an attribute has a unique constraint.

        In Python we don't have a deterministic way to determine if an attribute is unique via code introspection.
        We default to False.

        Args:
            attribute_node: Node representing an attribute or parameter
            is_parameter: Flag indicating if this is a parameter (vs attribute)

        Returns:
            True if the attribute has a unique constraint, False otherwise
        """
        # Default to False - most fields are not unique
        return False

    @override
    def is_primary(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        """
        Check if an attribute is a primary key.

        In Python, this is determined by Field(primary_key=True) or similar constructs.

        Args:
            attribute_node: Node representing an attribute or parameter
            is_parameter: Flag indicating if this is a parameter (vs attribute)

        Returns:
            True if the attribute is a primary key, False otherwise
        """
        if is_parameter:
            return False

        # Get Field(...) keyword arguments
        kwargs = self._field_kwargs(attribute_node.node)

        # Check for primary_key=True
        if "primary_key" in kwargs:
            # Convert string value to boolean
            primary_value = kwargs["primary_key"].lower()
            return primary_value not in ("false", "0", "none")

        # Default to False
        return False

    @override
    def is_public(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        """
        Check if an attribute is public (vs private/protected).

        In Python, attributes starting with underscore(s) are considered private:
        - _attribute = protected/private
        - __attribute = private (name mangling)
        - attribute = public

        Args:
            attribute_node: Node representing an attribute or parameter
            is_parameter: Flag indicating if this is a parameter (vs attribute)

        Returns:
            True if the attribute is public, False if private/protected
        """
        name_node = self.get_name(attribute_node, is_parameter)
        name = name_node.node_text()

        # In Python, names starting with underscore are considered private/protected
        return not name.startswith("_")

    def get_foreign_key_target(self, attribute_node: CodeNode[Node]) -> dict[str, str] | None:
        """
        Extract foreign key relationship information if present.

        Args:
            attribute_node: Node representing an attribute

        Returns:
            Dictionary with foreign key information or None
        """
        # Get Field(...) keyword arguments
        kwargs = self._field_kwargs(attribute_node.node)
        logger.debug(f"foreign key kwargs: {kwargs}")

        # Check for foreign_key attribute
        if "foreign_key" in kwargs:
            # Parse the string like "schema.table.column" or "table.column"
            fk_str = kwargs["foreign_key"].strip("\"'")
            parts = fk_str.split(".")

            if len(parts) == 3:
                return {"target_schema": parts[0], "target_table": parts[1], "target_column": parts[2]}
            elif len(parts) == 2:
                # Assume default schema if not specified
                return {"target_schema": "default", "target_table": parts[0], "target_column": parts[1]}

        # Default to None
        return None

    @override
    def qualname_for_role(self, node: CodeNode[Node], is_parameter: bool, parent: str | None = None) -> str:
        """
        Return a fully-qualified name for a Python attribute or parameter.

        For attributes: class.attribute_name
        For parameters: function_name.param_name

        Args:
            node: The attribute node to get the qualified name for
            is_parameter: Whether the node is a parameter (vs attribute)
            parent: Optional parent name (class/function name)

        Returns:
            Qualified name string
        """
        name_node = self.get_name(node, is_parameter=is_parameter)
        name = name_node.node_text()

        # Combine with parent if available
        if parent:
            return f"{parent}.{name}"

        # Fallback - just use name
        return name if name else f"attr@{node.byte_start}"

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for a Python attribute or parameter.

        This normalizes the definition to ensure consistent hashing
        regardless of whitespace or comment differences.

        Args:
            node: The attribute node to get bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        import re

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
    def reference_string_for_role(
        self,
        node: CodeNode[Node],
        is_parameter: bool,
        parent: str | None = None,
    ) -> str | None:
        """
        Return a reference string for this field/parameter that can be used to match comments.

        Args:
            node: The field/parameter node
            is_parameter: Whether this is a parameter (True) or field (False)
            parent: Optional parent context (e.g., type name for fields, function name for parameters)

        Returns:
            Reference string for comment matching
        """
        # Delegate to qualname method for consistent lookup keys
        return self.qualname_for_role(node, is_parameter, parent)
