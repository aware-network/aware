"""Python implementation of the CodeSectionEnumValueAdapter."""

from collections.abc import Iterable
import re
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query
from python_grammar._tree_sitter_python import PYTHON_LANGUAGE

# Kernel Graph Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.enum_value.adapter import CodeSectionEnumValueAdapter


class PythonEnumValueAdapter(CodeSectionEnumValueAdapter[Node]):
    """
    Extract enum value assignments from Python Enum class definitions.

    In Python, enum values are usually class-level assignments inside an Enum subclass:
      class Status(Enum):
          active = "active"
    """

    ENUM_VALUE_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          body: (block
            (expression_statement
              (assignment) @enum_value)))
        """
    )

    ENUM_VALUE_NAME_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (assignment
          left: (identifier) @name)
        """
    )

    ENUM_NAME_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          name: (identifier) @enum_name)
        """
    )

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.enum_value

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        captures = self.ENUM_VALUE_QUERY.captures(root)
        nodes = list(captures.get("enum_value", []))
        nodes.sort(key=lambda n: (n.start_byte, n.end_byte))
        for n in nodes:
            yield CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)

    @override
    def get_name(self, enum_value_node: CodeNode[Node]) -> CodeNode[Node]:
        captures = self.ENUM_VALUE_NAME_QUERY.captures(enum_value_node.node)
        vals = captures.get("name", [])
        if not vals:
            raise ValueError("No enum value name found in assignment")
        n = vals[0]
        return CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        value_name = self.get_name(node).node_text()
        if parent:
            return f"{parent}.{value_name}"

        # Fallback: walk up to class_definition and use its name.
        cur = node.node.parent
        while cur is not None:
            if cur.type == "class_definition":
                caps = self.ENUM_NAME_QUERY.captures(cur).get("enum_name", [])
                if caps:
                    enum_name = caps[0].text.decode("utf-8") if caps[0].text is not None else ""
                    if enum_name:
                        return f"{enum_name}.{value_name}"
                break
            cur = cur.parent
        return value_name

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        node_bytes = source[node.byte_start:node.byte_end]
        # Remove line comments and normalize whitespace for stable identity hashes.
        normalized = re.sub(rb"#.*?$", b"", node_bytes, flags=re.MULTILINE)
        normalized = re.sub(rb"\\s+", b" ", normalized).strip()
        return normalized
