"""Dart implementation of the CodeSectionExpressionAdapter."""

import re
from collections.abc import Iterable
from typing_extensions import override

from tree_sitter import Node

from aware_code_ontology.expression.code_section_expression_enums import (
    CodeSectionExpressionType,
)

from aware_code.node.node import CodeNode
from aware_code.section.expression.adapter import CodeSectionExpressionAdapter


class DartExpressionAdapter(CodeSectionExpressionAdapter[Node]):
    """
    Minimal, honest expression adapter for Dart.

    Used primarily for decorator/annotation argument capture. We keep classification conservative
    (LITERAL/IDENTIFIER/CALL) and normalize bytes for deterministic identity hashing.
    """

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        # Expressions are typically extracted by other adapters (decorators, assignments, etc.)
        return iter([])

    @override
    def classify(self, expression_node: CodeNode[Node]) -> CodeSectionExpressionType:
        node_type = expression_node.node.type

        # Literal-ish types in tree-sitter-dart
        if node_type in {
            "string_literal",
            "number_literal",
            "integer_literal",
            "double_literal",
            "boolean_literal",
            "null_literal",
            "list_literal",
            "map_literal",
            "set_or_map_literal",
        }:
            return CodeSectionExpressionType.literal

        # Identifiers and member access
        if node_type in {
            "identifier",
            "scoped_identifier",
            "prefixed_identifier",
            "qualified_identifier",
        }:
            return CodeSectionExpressionType.identifier

        # Invocation / call-ish
        if node_type in {
            "invocation",
            "arguments",
            "argument",
        }:
            return CodeSectionExpressionType.call

        return CodeSectionExpressionType.literal

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        node_bytes = source[node.byte_start:node.byte_end]
        # Dart has // and /* */ comments. Strip both and normalize whitespace.
        normalized = re.sub(b"//.*?$|/\\*.*?\\*/", b"", node_bytes, flags=re.MULTILINE | re.DOTALL)
        normalized = re.sub(b"\\s+", b" ", normalized).strip()
        return normalized

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        expr_type = self.classify(node)
        base_name = f"{expr_type.value}@{node.byte_start}"
        return f"{parent}.{base_name}" if parent else base_name
