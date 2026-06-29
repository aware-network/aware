"""Aware implementation of the CodeSectionEnumValueAdapter."""

from __future__ import annotations

from collections.abc import Iterable
import re
from typing_extensions import override
from typing import final

# Tree-sitter
from tree_sitter import Node
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.enum_value.adapter import CodeSectionEnumValueAdapter


@final
class AwareEnumValueAdapter(CodeSectionEnumValueAdapter[Node]):
    """
    Implementation of CodeSectionEnumValueAdapter for Aware language using Tree-sitter.

    Maps `enum_value_def` nodes to enum value CodeSections.
    """

    ENUM_VALUE_QUERY = AWARE_LANGUAGE.query(
        """
        (enum_value_def) @enum_value
        """
    )

    ENUM_VALUE_NAME_QUERY = AWARE_LANGUAGE.query(
        """
        (enum_value_def
          name: (ident) @value_name)
        """
    )

    ENUM_NAME_QUERY = AWARE_LANGUAGE.query(
        """
        (enum_def
          name: (ident) @enum_name)
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        captures = self.ENUM_VALUE_QUERY.captures(root)
        if "enum_value" not in captures:
            return
        for n in captures["enum_value"]:
            yield CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)

    @override
    def get_name(self, enum_value_node: CodeNode[Node]) -> CodeNode[Node]:
        captures = self.ENUM_VALUE_NAME_QUERY.captures(enum_value_node.node)
        if "value_name" in captures and captures["value_name"]:
            name_node = captures["value_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)
        raise ValueError("No enum value name found in enum_value_def")

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        value_name = self.get_name(node).node_text()
        if parent:
            return f"{parent}.{value_name}"

        # Fallback: try to resolve parent enum name by walking ancestors.
        current = node.node.parent
        while current is not None:
            if current.type == "enum_def":
                caps = self.ENUM_NAME_QUERY.captures(current)
                if "enum_name" in caps and caps["enum_name"]:
                    enum_name_node = caps["enum_name"][0]
                    enum_name = enum_name_node.text.decode("utf-8") if enum_name_node.text else ""
                    if enum_name:
                        return f"{enum_name}.{value_name}"
                break
            current = current.parent

        return value_name

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        node_bytes = source[node.byte_start:node.byte_end]
        normalized = re.sub(b"//[^\n]*", b"", node_bytes, flags=re.MULTILINE)
        normalized = re.sub(b"\\s+", b" ", normalized).strip()
        return normalized

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        return self.qualname(node, parent)
