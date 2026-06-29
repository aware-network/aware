"""Dart implementation of the CodeSectionEnumAdapter."""

from collections.abc import Iterable
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query

# Aware Kernel Graph Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.enum.adapter import CodeSectionEnumAdapter

# Dart Grammar
from dart_grammar._tree_sitter_dart import DART_LANGUAGE


class DartEnumAdapter(CodeSectionEnumAdapter[Node]):
    """Extract Dart enum declarations and values."""

    ENUM_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (enum_declaration) @enum
        """
    )

    ENUM_NAME_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (enum_declaration
          name: (identifier) @name)
        """
    )

    ENUM_VALUES_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (enum_declaration
          body: (enum_body
            (enum_constant
              name: (identifier) @val)
          )
        )
        """
    )

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.enum

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        return source[node.byte_start:node.byte_end]

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        captures = self.ENUM_QUERY.captures(root)
        for en in captures.get("enum", []):
            yield CodeNode(node=en, byte_start=en.start_byte, byte_end=en.end_byte)

    @override
    def get_name(self, enum_node: CodeNode[Node]) -> CodeNode[Node]:
        captures = self.ENUM_NAME_QUERY.captures(enum_node.node)
        vals = captures.get("name", [])
        if vals:
            n = vals[0]
            return CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)
        return enum_node

    @override
    def get_values(self, enum_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        captures = self.ENUM_VALUES_QUERY.captures(enum_node.node)
        for v in captures.get("val", []):
            yield CodeNode(node=v, byte_start=v.start_byte, byte_end=v.end_byte)

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        name_node = self.get_name(node)
        text = name_node.node_text()
        return (f"{parent}." if parent else "") + text

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        """Return a reference string for a Dart enum."""
        return self.qualname(node, parent)
