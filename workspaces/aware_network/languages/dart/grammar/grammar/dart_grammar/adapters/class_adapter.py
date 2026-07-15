"""Dart implementation of the CodeSectionClassAdapter."""

from collections.abc import Iterable
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query

# Aware Kernel Graph Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.class_.adapter import CodeSectionClassAdapter

# Dart Grammar
from dart_grammar._tree_sitter_dart import DART_LANGUAGE


class DartClassAdapter(CodeSectionClassAdapter[Node]):
    """Extract Dart class definitions, names, bases, attributes, and methods."""

    CLASS_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (class_definition) @class
        """
    )

    CLASS_NAME_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (class_definition
          name: (identifier) @class_name)
        """
    )

    CLASS_BASES_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (class_definition
          superclass: (superclass) @bases)
        """
    )

    CLASS_METHODS_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (class_definition
          body: (class_body
            (method_signature) @method
          )
        )
        """
    )

    # Capture actual field declarations via initialized_identifier within class body declarations
    CLASS_FIELD_IDS_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (class_definition
          body: (class_body
            (declaration
              (initialized_identifier_list (initialized_identifier) @field)
            )
          )
        )
        """
    )

    # NEW: Query for factory constructor parameters (freezed pattern)
    # Note: Both factory_constructor_signature and redirecting_factory_constructor_signature
    # can contain parameters. The latter is used for freezed factory constructors.
    # Parameters can be directly in formal_parameter_list or wrapped in optional_formal_parameters
    FACTORY_PARAMS_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (class_definition
          body: (class_body
            (declaration
              [
                (factory_constructor_signature
                  (formal_parameter_list) @plist
                )
                (redirecting_factory_constructor_signature
                  (formal_parameter_list) @plist
                )
              ]
            )
          )
        )
        """
    )

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.class_

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        return source[node.byte_start:node.byte_end]

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        captures = self.CLASS_QUERY.captures(root)
        for cls in captures.get("class", []):
            yield CodeNode(node=cls, byte_start=cls.start_byte, byte_end=cls.end_byte)

    @override
    def get_name(self, class_node: CodeNode[Node]) -> CodeNode[Node]:
        captures = self.CLASS_NAME_QUERY.captures(class_node.node)
        name = captures.get("class_name", [])
        if name:
            n = name[0]
            return CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)
        # Fallback: first identifier child
        for child in class_node.node.children:
            if child.type == "identifier":
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
        return class_node

    @override
    def get_attributes(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        # First, get traditional field declarations
        captures = self.CLASS_FIELD_IDS_QUERY.captures(class_node.node)
        for field in captures.get("field", []):
            yield CodeNode(node=field, byte_start=field.start_byte, byte_end=field.end_byte)

        # NEW: Also get factory constructor parameters (for freezed models)
        factory_captures = self.FACTORY_PARAMS_QUERY.captures(class_node.node)
        for plist in factory_captures.get("plist", []):
            # Traverse parameter list subtree to collect parameters
            stack = [plist]
            while stack:
                cur = stack.pop()
                # Unwrap named_parameter to formal_parameter
                if cur.type == "named_parameter":
                    for ch in cur.children:
                        if ch.type == "formal_parameter":
                            yield CodeNode(node=ch, byte_start=ch.start_byte, byte_end=ch.end_byte)
                            break
                    continue
                if cur.type == "formal_parameter":
                    yield CodeNode(node=cur, byte_start=cur.start_byte, byte_end=cur.end_byte)
                    continue
                # Descend further
                for ch in cur.children:
                    stack.append(ch)

    @override
    def get_methods(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        captures = self.CLASS_METHODS_QUERY.captures(class_node.node)
        for method in captures.get("method", []):
            yield CodeNode(node=method, byte_start=method.start_byte, byte_end=method.end_byte)

    @override
    def get_modifiers(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        return []

    @override
    def get_keyword(self, class_node: CodeNode[Node]) -> CodeNode[Node] | None:
        # Return the 'class' keyword if present among children
        for child in class_node.node.children:
            if child.text == b"class":
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
        return None

    @override
    def get_bases(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        captures = self.CLASS_BASES_QUERY.captures(class_node.node)
        for base_list in captures.get("bases", []):
            for ch in base_list.children:
                if ch.is_named:
                    yield CodeNode(node=ch, byte_start=ch.start_byte, byte_end=ch.end_byte)

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        name = self.get_name(node)
        text = name.node_text()
        if text:
            return (f"{parent}." if parent else "") + text
        return parent or ""

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        """Return a reference string for a Dart class."""
        return self.qualname(node, parent)
