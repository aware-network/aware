"""Dart implementation of the CodeSectionAttributeAdapter."""

from collections.abc import Iterable
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query

# Aware Kernel Graph Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.attribute.adapter import CodeSectionAttributeAdapter

# Dart Grammar
from dart_grammar._tree_sitter_dart import DART_LANGUAGE


class DartAttributeAdapter(CodeSectionAttributeAdapter[Node]):
    """
    Extracts top-level and class-level attribute declarations from Dart code using Tree-sitter.

    Coverage goals:
    - Top-level variables: `final`, `const`, and typed declarations
    - Class fields via initialized_identifier within class body declarations
    - Default values when syntactically available
    """

    # Top-level declarations with initialized identifiers
    TOP_LEVEL_VAR_IDS_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (initialized_identifier) @decl
        """
    )

    # Class fields handled by class adapter; keep here for standalone matching when needed
    CLASS_FIELD_IDS_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (class_definition
          body: (class_body
            (declaration (initialized_identifier_list (initialized_identifier) @decl))
          )
        )
        """
    )

    CONSTRUCTOR_PARAM_FIELD_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (constructor_param
          (this)
          "."
          (identifier) @field_name
        ) @ctor_param
        """
    )

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.attribute

    # No queries needed; 'required' is a hidden token in grammar. We'll pair by sibling traversal.

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        # Return slice
        return source[node.byte_start:node.byte_end]

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        # Only yield initialized_identifier that are not inside class_definition
        for node in self.TOP_LEVEL_VAR_IDS_QUERY.captures(root).get("decl", []):
            parent = node.parent
            inside_class = False
            while parent is not None:
                if parent.type == "class_definition":
                    inside_class = True
                    break
                parent = parent.parent
            if inside_class:
                continue
            yield CodeNode(node=node, byte_start=node.start_byte, byte_end=node.end_byte)

        # Do not emit class fields here; class adapter handles class attributes

    @override
    def qualname_for_role(self, node: CodeNode[Node], is_parameter: bool, parent: str | None = None) -> str:
        name = self.get_name(node, is_parameter)
        text = name.node_text()
        if text:
            return (f"{parent}." if parent else "") + text
        return parent or ""

    @override
    def get_name(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node]:
        node = attribute_node.node

        # Handle formal_parameter nodes (from factory constructors)
        if node.type == "formal_parameter":
            # Look for identifier in formal_parameter structure
            for child in node.children:
                if child.type == "identifier":
                    return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
                # Handle nested _simple_formal_parameter
                elif child.type == "_simple_formal_parameter":
                    for subchild in child.children:
                        if subchild.type == "identifier":
                            return CodeNode(node=subchild, byte_start=subchild.start_byte, byte_end=subchild.end_byte)

        # Handle initialized_identifier → first child is identifier
        for child in node.children:
            if child.type == "identifier":
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
        return attribute_node

    @override
    def get_type(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node]:
        node = attribute_node.node

        # Handle formal_parameter nodes (from factory constructors)
        if node.type == "formal_parameter":
            # Extract complete type by finding the byte range of all type components
            # Type structure: type_identifier + type_arguments? + nullable_type?

            type_start_byte = None
            type_end_byte = None
            first_type_node = None

            for child in node.children:
                # Skip metadata/annotations (like @Default) and keywords
                if child.type in ["metadata", "annotation", "required"]:
                    continue

                # Track type-related nodes to get complete byte range
                if child.type in ["type_identifier", "type_arguments", "nullable_type"]:
                    if type_start_byte is None:
                        type_start_byte = child.start_byte
                        first_type_node = child
                    type_end_byte = child.end_byte

                # Stop when we hit the parameter name
                elif child.type == "identifier":
                    break

            # If we found type nodes, return a CodeNode with the complete byte range
            if first_type_node and type_end_byte:
                # Use the first type node as the base, but extend byte range to include all type parts
                return CodeNode(node=first_type_node, byte_start=type_start_byte or 0, byte_end=type_end_byte)

            # Fallback to old behavior if no type found
            for child in node.children:
                if child.type in ["metadata", "annotation", "required"]:
                    continue
                if child.type not in ["identifier", "_simple_formal_parameter", "metadata", "required"]:
                    return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

        # For class fields: climb to declaration and take the full type span immediately before the identifier list
        parent = node.parent
        if parent is not None and parent.type == "initialized_identifier_list":
            decl = parent.parent
            if decl is not None and decl.type == "declaration":
                named = [ch for ch in decl.children if ch.is_named]
                # Find the id list among named children
                try:
                    id_idx = named.index(parent)
                except ValueError:
                    id_idx = -1
                if id_idx > 0:
                    # Walk backwards to collect contiguous type-related nodes
                    TYPE_PARTS = {
                        "type_identifier",
                        "prefixed_identifier",
                        "qualified_identifier",
                        "type",
                        "type_arguments",
                        "_simple_type_argument_list",
                        "nullable_type",
                    }
                    start_idx = id_idx - 1
                    end_idx = id_idx - 1
                    # Expand left while previous named nodes are type parts
                    j = id_idx - 1
                    while j >= 0 and named[j].type in TYPE_PARTS:
                        start_idx = j
                        j -= 1
                    # Expand right in rare cases where type_arguments follow separately (defensive)
                    k = id_idx - 1
                    while k + 1 < len(named) and named[k + 1] is not parent and named[k + 1].type in TYPE_PARTS:
                        end_idx = k + 1
                        k += 1
                    type_start = named[start_idx].start_byte
                    type_end = named[end_idx].end_byte
                    return CodeNode(node=named[start_idx], byte_start=type_start, byte_end=type_end)
        # Fallback: return the declaration context as type when available
        return attribute_node

    @override
    def get_default_value(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node] | None:
        node = attribute_node.node

        # For formal parameters, check for @Default annotation
        if node.type == "formal_parameter":
            # Look for annotation child or sibling
            annotation_node = None

            # Check direct children for annotation
            for child in node.children:
                if child.type == "annotation":
                    annotation_node = child
                    break

            # If not found, check parent (named_parameter) for annotation sibling
            if not annotation_node and node.parent and node.parent.type == "named_parameter":
                for sibling in node.parent.children:
                    if sibling.type == "annotation":
                        annotation_node = sibling
                        break

            # Parse @Default annotation if found
            if annotation_node:
                # Look for Default identifier and arguments
                is_default = False
                for child in annotation_node.children:
                    if child.type == "identifier" and child.text == b"Default":
                        is_default = True
                    elif is_default and child.type == "arguments":
                        # Extract the argument inside the parentheses
                        for arg_child in child.children:
                            if arg_child.type == "argument":
                                # Get the actual value node
                                for val_child in arg_child.children:
                                    if val_child.type in [
                                        "list_literal",
                                        "string_literal",
                                        "number_literal",
                                        "boolean_literal",
                                        "null_literal",
                                        "identifier",
                                    ]:
                                        return CodeNode(
                                            node=val_child, byte_start=val_child.start_byte, byte_end=val_child.end_byte
                                        )
                                # If argument node has text directly
                                if arg_child.text:
                                    return CodeNode(
                                        node=arg_child, byte_start=arg_child.start_byte, byte_end=arg_child.end_byte
                                    )

        # Fallback to original logic for initialized_identifier
        children = attribute_node.node.children
        for idx, ch in enumerate(children):
            if ch.type == "identifier" and idx + 1 < len(children):
                nxt = children[idx + 1]
                # initializer can be an '=' token followed by expression
                if nxt.text == b"=":
                    if idx + 2 < len(children):
                        val = children[idx + 2]
                        return CodeNode(node=val, byte_start=val.start_byte, byte_end=val.end_byte)
        return None

    @override
    def is_required(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        node = attribute_node.node

        # For formal_parameter nodes, check for 'required' keyword
        if node.type == "formal_parameter":
            parent = node.parent
            if parent is not None and parent.type == "named_parameter":
                # Check required_kw field presence by scanning children for required token
                for ch in parent.children:
                    if ch.type == "required":
                        return True
        return False

    @override
    def has_unique(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        """
        Check if an attribute has a unique constraint.

        In Dart we don't have a deterministic way to determine if an attribute is unique via code introspection.
        We default to False.
        """
        return False

    @override
    def is_primary(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        return False

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
