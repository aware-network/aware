"""SQL implementation of the CodeSectionEnumValueAdapter."""

from collections.abc import Iterable
import re

# Tree-sitter
from tree_sitter import Node, Query
from typing_extensions import override

# Kernel Graph Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.enum_value.adapter import CodeSectionEnumValueAdapter

# SQL Grammar
from sql_grammar._tree_sitter_sql import SQL_LANGUAGE


class SQLEnumValueAdapter(CodeSectionEnumValueAdapter[Node]):
    """
    Extract SQL enum values from `CREATE TYPE ... AS ENUM (...)` definitions.

    For Postgres-style enums, the values are string literals inside `enum_elements`.
    We model each literal as a first-class CodeSection (CodeSectionType.enum_value).
    """

    ENUM_VALUE_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_type
          (enum_elements
            (literal) @enum_value))
        """
    )

    ENUM_NAME_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_type
          (object_reference) @enum_name)
        """
    )

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.enum_value

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        captures = self.ENUM_VALUE_QUERY.captures(root)
        for n in captures.get("enum_value", []):
            yield CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)

    @override
    def get_name(self, enum_value_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Return the literal content node for the enum value.

        We strip the outer quotes for string literals so SSOT values don't include `'...'`.
        """
        text_b = enum_value_node.node.text
        if text_b is None:
            return enum_value_node

        if len(text_b) >= 2 and text_b[:1] in (b"'", b'"') and text_b[-1:] == text_b[:1]:
            # Adjust byte range to exclude outer quotes.
            start = enum_value_node.byte_start + 1
            end = enum_value_node.byte_end - 1
            if start < end:
                return CodeNode(node=enum_value_node.node, byte_start=start, byte_end=end)

        return enum_value_node

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        value_name = self.get_name(node).node_text()
        if parent:
            return f"{parent}.{value_name}"

        # Fallback: resolve containing enum name from the nearest create_type ancestor.
        cur = node.node.parent
        while cur is not None:
            if cur.type == "create_type":
                caps = self.ENUM_NAME_QUERY.captures(cur).get("enum_name", [])
                if caps:
                    enum_ref = caps[0].text.decode("utf-8") if caps[0].text is not None else ""
                    enum_ref = enum_ref.strip()
                    if enum_ref:
                        return f"{enum_ref}.{value_name}"
                break
            cur = cur.parent

        return value_name

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        node_bytes = source[node.byte_start:node.byte_end]
        # Strip SQL comments and normalize whitespace.
        normalized = re.sub(rb"--.*?$|/\\*.*?\\*/", b"", node_bytes, flags=re.MULTILINE | re.DOTALL)
        normalized = re.sub(rb"\\s+", b" ", normalized).strip()
        return normalized
