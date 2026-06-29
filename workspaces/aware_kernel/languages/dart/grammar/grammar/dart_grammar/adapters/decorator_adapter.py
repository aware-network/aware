"""Dart implementation of the CodeSectionDecoratorAdapter (annotations)."""

from collections.abc import Iterable
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query

# Aware Kernel Graph Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.decorator.adapter import CodeSectionDecoratorAdapter

# Dart Grammar
from dart_grammar._tree_sitter_dart import DART_LANGUAGE


class DartDecoratorAdapter(CodeSectionDecoratorAdapter[Node]):
    """Extract Dart annotations (e.g., @freezed, @JsonSerializable)."""

    DECORATOR_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (annotation) @decorator
        """
    )

    NAME_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (annotation
          name: (identifier) @name)
        (annotation
          name: (scoped_identifier (identifier) @name))
        """
    )

    # arguments are present as a direct child node; not labeled as a field in grammar
    ARGS_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (annotation (arguments) @args)
        """
    )

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.decorator

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        return source[node.byte_start:node.byte_end]

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        caps = self.DECORATOR_QUERY.captures(root)
        for dec in caps.get("decorator", []):
            yield CodeNode(node=dec, byte_start=dec.start_byte, byte_end=dec.end_byte)

    @override
    def get_name(self, decorator_node: CodeNode[Node]) -> CodeNode[Node]:
        caps = self.NAME_QUERY.captures(decorator_node.node)
        vals = caps.get("name", [])
        if vals:
            n = vals[0]
            return CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)
        return decorator_node

    @override
    def get_arguments(self, decorator_node: CodeNode[Node]) -> Iterable[tuple[CodeNode[Node] | None, CodeNode[Node]]]:
        caps = self.ARGS_QUERY.captures(decorator_node.node)
        for a in caps.get("args", []):
            yield None, CodeNode(node=a, byte_start=a.start_byte, byte_end=a.end_byte)

    @override
    def get_target(self, decorator_node: CodeNode[Node]) -> CodeNode[Node] | None:
        # Target association is not modeled in grammar; return None
        return None

    @override
    def get_target_type(self, decorator_node: CodeNode[Node]) -> str | None:
        return None

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        name_node = self.get_name(node)
        text = name_node.node_text()
        return (f"{parent}." if parent else "") + text
