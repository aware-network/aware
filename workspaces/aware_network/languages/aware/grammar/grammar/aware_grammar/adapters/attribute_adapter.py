"""Aware implementation of the CodeSectionAttributeAdapter (attributes + function input attrs)."""

from collections.abc import Iterable
import re
from typing_extensions import override
from typing import final

# Tree-sitter
from tree_sitter import Node
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

# Aware Primitive Code
from aware_code.section.attribute.adapter import CodeSectionAttributeAdapter
from aware_code.node.node import CodeNode


@final
class AwareAttributeAdapter(CodeSectionAttributeAdapter[Node]):
    """
    Implementation of CodeSectionAttributeAdapter for Aware language using Tree-sitter.

    Maps `attr_def` definitions in Aware to attribute sections, and `input_attr` nodes to parameter attributes.
    """

    # Pre-compiled queries
    ATTR_NAME_QUERY = AWARE_LANGUAGE.query(
        """
        (attr_def
          name: (ident) @attr_name)
        """
    )

    ATTR_TYPE_QUERY = AWARE_LANGUAGE.query(
        """
        (attr_def
          type: (type_ref) @attr_type)
        """
    )

    ATTR_DEFAULT_QUERY = AWARE_LANGUAGE.query(
        """
        (attr_def "="
          default: (default_value) @default_value)
        """
    )

    PARAM_DEFAULT_QUERY = AWARE_LANGUAGE.query(
        """
        (input_attr "="
          default: (default_value) @param_default)
        """
    )

    UNIQUE_QUERY = AWARE_LANGUAGE.query(
        """
        (attr_def
          cardinality: (unique_kw) @unique)
        """
    )

    TYPE_BASE_QUERY = AWARE_LANGUAGE.query(
        """
        (type_ref
          base: (qualified_name) @base_type)
        """
    )

    TYPE_OPTIONAL_QUERY = AWARE_LANGUAGE.query(
        """
        (type_ref "?" @optional)
        """
    )

    LIST_MARKER_QUERY = AWARE_LANGUAGE.query(
        """
        (type_ref "[" @list_open "]" @list_close)
        """
    )

    PARAM_NAME_QUERY = AWARE_LANGUAGE.query(
        """
        (input_attr
          name: (ident) @param_name)
        """
    )

    PARAM_TYPE_QUERY = AWARE_LANGUAGE.query(
        """
        (input_attr
          type: (type_ref) @param_type)
        """
    )

    OUTPUT_NAME_QUERY = AWARE_LANGUAGE.query(
        """
        (output_attr
          name: (ident) @out_name)
        """
    )

    OUTPUT_TYPE_QUERY = AWARE_LANGUAGE.query(
        """
        (output_attr
          type: (type_ref) @out_type)
        """
    )

    # Add queries for edge specification
    EDGE_SPEC_NAME_QUERY = AWARE_LANGUAGE.query(
        """
        (edge_spec_ref
          edge_name: (qualified_name) @edge_name)
        """
    )

    MANY_QUERY = AWARE_LANGUAGE.query(
        """
        (attr_def
          cardinality: (many_kw) @many)
        """
    )

    IDENTITY_KEY_QUERY = AWARE_LANGUAGE.query(
        """
        (attr_def
          identity_key: (identity_key_marker) @identity_key)
        (input_attr
          identity_key: "key" @identity_key)
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all field definitions that are at the top level (not in a type or edge).

        Args:
            root: The root node of the parse tree
            source: The source code as bytes

        Returns:
            Iterable of nodes representing field definitions
        """
        # In Aware grammar, fields should be inside types or edges
        # So this might be empty at the root level
        return []

    @override
    def get_name(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node]:
        """
        Extract the name from a field definition or parameter.

        Args:
            attribute_node: Node representing a field definition or parameter
            is_parameter: Flag indicating if this is a parameter (vs field)

        Returns:
            Node representing the field/parameter name
        """
        if is_parameter:
            # For parameters, use a different query
            captures = self.PARAM_NAME_QUERY.captures(attribute_node.node)
            if "param_name" in captures and captures["param_name"]:
                name_node = captures["param_name"][0]
                return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)
            # Named return parameters (outputs) reuse the attribute adapter path with is_parameter=True.
            out = self.OUTPUT_NAME_QUERY.captures(attribute_node.node)
            if "out_name" in out and out["out_name"]:
                name_node = out["out_name"][0]
                return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)
        else:
            # For regular fields, use the existing query
            captures = self.ATTR_NAME_QUERY.captures(attribute_node.node)
            if "attr_name" in captures and captures["attr_name"]:
                name_node = captures["attr_name"][0]
                return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # Fallback - should not happen with valid syntax
        raise ValueError(
            f"No {'parameter' if is_parameter else 'field'} name found in definition {attribute_node.node_text()}"
        )

    @override
    def get_type(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node]:
        """
        Extract the type from a field definition or parameter.

        Args:
            attribute_node: Node representing a field definition or parameter
            is_parameter: Flag indicating if this is a parameter (vs field)

        Returns:
            Node representing the field/parameter type
        """
        if is_parameter:
            # For parameters, get the type field directly
            captures = self.PARAM_TYPE_QUERY.captures(attribute_node.node)
            if "param_type" in captures and captures["param_type"]:
                type_node = captures["param_type"][0]  # Use first (only) match
                return CodeNode(node=type_node, byte_start=type_node.start_byte, byte_end=type_node.end_byte)
            out = self.OUTPUT_TYPE_QUERY.captures(attribute_node.node)
            if "out_type" in out and out["out_type"]:
                type_node = out["out_type"][0]
                return CodeNode(node=type_node, byte_start=type_node.start_byte, byte_end=type_node.end_byte)
        else:
            # For regular fields, use the existing logic
            captures = self.ATTR_TYPE_QUERY.captures(attribute_node.node)
            if "attr_type" in captures and captures["attr_type"]:
                type_ref_node = captures["attr_type"][0]
                # If we didn't get the base type, just return the whole type_ref
                return CodeNode(
                    node=type_ref_node, byte_start=type_ref_node.start_byte, byte_end=type_ref_node.end_byte
                )
        # Canonical Aware: fields/params must have an explicit type. If we can't capture it,
        # that's either invalid syntax or a query mismatch and should hard-fail.
        raise ValueError(
            f"No type found in {'parameter' if is_parameter else 'field'} definition: {attribute_node.node_text()}"
        )

    def get_base_type(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node] | None:
        """
        Extract the base type from a field definition.
        """
        type_ref_node = self.get_type(attribute_node, is_parameter)
        if not type_ref_node:
            return None

        # Then get the base type from the type_ref
        base_captures = self.TYPE_BASE_QUERY.captures(type_ref_node.node)
        if "base_type" in base_captures and base_captures["base_type"]:
            base_node = base_captures["base_type"][0]
            # `base_node` is a `qualified_name` (may include dots). For canonical "base type" we expose the leaf symbol
            # to keep adapter semantics stable (e.g., "attribute.Attribute" -> "Attribute").
            last_ident = None
            for ch in reversed(base_node.children):
                if ch.type == "ident":
                    last_ident = ch
                    break
            if last_ident is not None:
                return CodeNode(node=last_ident, byte_start=last_ident.start_byte, byte_end=last_ident.end_byte)
            return CodeNode(node=base_node, byte_start=base_node.start_byte, byte_end=base_node.end_byte)
        return None

    # !! TODO: REMOVE get qualified name instead directly from grammar.
    def get_schema(self, attribute_node: CodeNode[Node], is_parameter: bool) -> str | None:
        """
        Namespace is now encoded in `qualified_name` and interpreted by the resolver.
        Grammar does not expose a dedicated schema field anymore.
        """
        _ = (attribute_node, is_parameter)
        return None

    @override
    def get_edge_spec(self, attribute_node: CodeNode[Node], is_parameter: bool = False) -> str | None:
        """
        Extract the edge specification from a field definition if present.

        For a field like: attributes attribute.Attribute[] @FunctionCallArgument
        This would return "FunctionCallArgument"

        For a field like: attributes attribute.Attribute[] @schema.FunctionCallArgument
        This would return "schema.FunctionCallArgument"

        Canonical behavior (required for strict FQN resolution):
        - Preserve the full `qualified_name` string from the grammar, including any namespace qualifiers.
        - Meta uses the FQN resolver to interpret `Name`, `schema.Name`, or `domain.schema.Name` deterministically.

        Args:
            attribute_node: Node representing a field definition or parameter
            is_parameter: Flag indicating if this is a parameter (vs field)

        Returns:
            Edge specification name if present, None otherwise
        """
        type_ref_node = self.get_type(attribute_node, is_parameter)
        if not type_ref_node:
            return None

        # Query for edge_spec in the type_ref
        captures = self.EDGE_SPEC_NAME_QUERY.captures(type_ref_node.node)
        if "edge_name" in captures and captures["edge_name"]:
            edge_name_node = captures["edge_name"][0]
            if not edge_name_node.text:
                raise ValueError(f"Edge name node {edge_name_node} has no text")
            edge_name = edge_name_node.text.decode("utf-8")
            # Preserve qualified name (schema.Name / domain.schema.Name), so strict mode can resolve.
            return edge_name.strip()

        return None

    def get_edge_spec_schema(self, attribute_node: CodeNode[Node], is_parameter: bool = False) -> str | None:
        """
        Extract the edge schema from a field definition if present.

        For a field like: attributes attribute.Attribute[] @schema.FunctionCallArgument
        This would return "schema"

        Args:
            attribute_node: Node representing a field definition or parameter
            is_parameter: Flag indicating if this is a parameter (vs field)

        Returns:
            Edge schema if present, None otherwise
        """
        type_ref_node = self.get_type(attribute_node, is_parameter)
        if not type_ref_node:
            return None

        # Namespace is now encoded in `qualified_name`; return its prefix (if any) for legacy callers.
        captures = self.EDGE_SPEC_NAME_QUERY.captures(type_ref_node.node)
        if "edge_name" in captures and captures["edge_name"]:
            node = captures["edge_name"][0]
            if not node.text:
                return None
            text = node.text.decode("utf-8")
            parts = [p for p in text.split(".") if p]
            if len(parts) <= 1:
                return None
            return ".".join(parts[:-1])
        return None

    @override
    def get_default_value(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node] | None:
        """
        Extract the default value from a field definition or parameter if present.

        Args:
            attribute_node: Node representing a field definition or parameter
            is_parameter: Flag indicating if this is a parameter (vs field)

        Returns:
            Node representing the default value if present, None otherwise
        """
        if is_parameter:
            # Use parameter-specific query
            captures = self.PARAM_DEFAULT_QUERY.captures(attribute_node.node)
            if "param_default" in captures and captures["param_default"]:
                default_node = captures["param_default"][0]
                return CodeNode(node=default_node, byte_start=default_node.start_byte, byte_end=default_node.end_byte)
            return None
        else:
            # Use field-specific query
            captures = self.ATTR_DEFAULT_QUERY.captures(attribute_node.node)
            if "default_value" in captures and captures["default_value"]:
                default_node = captures["default_value"][0]
                return CodeNode(node=default_node, byte_start=default_node.start_byte, byte_end=default_node.end_byte)
            return None

    def has_list(self, attribute_node: CodeNode[Node], is_parameter: bool = False) -> bool:
        """Return True when the type_ref contains list markers `[]`.

        Uses structural capture instead of raw node text to tolerate partial parses.
        """
        type_ref_node = self.get_type(attribute_node, is_parameter=is_parameter)
        if not type_ref_node:
            return False
        captures = self.LIST_MARKER_QUERY.captures(type_ref_node.node)
        return ("list_open" in captures and bool(captures["list_open"])) or (
            "list_close" in captures and bool(captures["list_close"])
        )

    @override
    def has_unique(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        """
        Check if a field is marked as unique.

        Args:
            attribute_node: Node representing a field definition

        Returns:
            True if the field is marked as unique, False otherwise
        """
        if is_parameter:
            # Parameters don't participate in field cardinality/relationship semantics.
            return False

        # Special case -> has_list + not many = unique (ONE_TO_MANY)
        if self.has_list(attribute_node, is_parameter=False) and not self.is_many_to_many(attribute_node):
            return True

        captures = self.UNIQUE_QUERY.captures(attribute_node.node)
        return "unique" in captures and bool(captures["unique"])

    def is_optional(self, attribute_node: CodeNode[Node], is_parameter: bool = False) -> bool:
        """
        Check if a field type or parameter type is marked as optional with ?.

        Args:
            attribute_node: Node representing a field definition or parameter
            is_parameter: Flag indicating if this is a parameter (vs field)

        Returns:
            True if the field/parameter type is marked as optional, False otherwise
        """
        # For both fields and parameters: type is a type_ref, look for ? marker in the structure
        type_ref_node = self.get_type(attribute_node, is_parameter=is_parameter)
        if not type_ref_node:
            return False
        optional_captures = self.TYPE_OPTIONAL_QUERY.captures(type_ref_node.node)
        return "optional" in optional_captures and bool(optional_captures["optional"])

    @override
    def is_primary(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        """
        Check if a field is marked as primary key.

        Args:
            attribute_node: Node representing a field definition

        Returns:
            True if the field is marked as primary key, False otherwise
        """
        captures = self.IDENTITY_KEY_QUERY.captures(attribute_node.node)
        return "identity_key" in captures and bool(captures["identity_key"])

    @override
    def is_required(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        """
        Check if a field or parameter is required (not optional).

        Args:
            attribute_node: Node representing a field definition or parameter
            is_parameter: Flag indicating if this is a parameter (vs field)

        Returns:
            True if the field/parameter is required, False otherwise
        """
        # A field/parameter is required if it's not optional
        return not self.is_optional(attribute_node, is_parameter)

    @override
    def qualname_for_role(self, node: CodeNode[Node], is_parameter: bool, parent: str | None = None) -> str:
        """
        Return a fully-qualified name for an Aware field.

        Args:
            node: The attribute node to get the qualified name for
            is_parameter: Flag indicating if this is a parameter (vs field)
            parent: Optional parent type name

        Returns:
            Qualified name string
        """
        # Get field - or parameter name
        name_node = self.get_name(node, is_parameter)
        name_text = name_node.node_text()

        # If we have a parent type, prepend it
        if parent:
            return f"{parent}.{name_text}"

        return name_text

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for an Aware field definition.

        This strips comments and normalizes whitespace.

        Args:
            node: The field node to get body bytes for
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
    def is_many_to_many(self, attribute_node: CodeNode[Node], is_parameter: bool = False) -> bool:
        """
        Check if a field is marked as many-to-many with the 'many' modifier.

        Args:
            attribute_node: Node representing a field definition

        Returns:
            True if the field has the 'many' modifier, False otherwise
        """
        if is_parameter:
            return False
        captures = self.MANY_QUERY.captures(attribute_node.node)
        return "many" in captures and bool(captures["many"])

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

    @override
    def get_annotations(self, attribute_node: CodeNode[Node], is_parameter: bool) -> list[str] | None:
        """
        Return annotations associated with this field or parameter, if any.

        Annotation collection will be implemented once the Aware grammar
        and object graph builders are wired for `ann` statements.
        """
        return None
