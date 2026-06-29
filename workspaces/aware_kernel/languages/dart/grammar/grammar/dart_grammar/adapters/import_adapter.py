"""Dart implementation of the CodeSectionImportAdapter."""

from collections.abc import Iterable
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query

# Aware Kernel Graph Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.import_.adapter import CodeSectionImportAdapter

# Dart Grammar
from dart_grammar._tree_sitter_dart import DART_LANGUAGE


class DartImportAdapter(CodeSectionImportAdapter[Node]):
    """Extract import/export/part directives from Dart code."""

    IMPORTS_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (import_or_export
          (library_import) @import
        )
        (import_or_export
          (library_export) @export
        )
        (part_directive) @part
        (part_of_directive) @part_of
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        captures = self.IMPORTS_QUERY.captures(root)
        for key in ("import", "export", "part", "part_of"):
            for node in captures.get(key, []):
                yield CodeNode(node=node, byte_start=node.start_byte, byte_end=node.end_byte)

    @override
    def is_from_import(self, import_node: CodeNode[Node]) -> bool:
        # Dart uses only URI-based imports, no 'from ... import ...' style
        return False

    @override
    def is_star_import(self, import_node: CodeNode[Node]) -> bool:
        return False

    @override
    def get_module_name(self, import_node: CodeNode[Node]) -> CodeNode[Node]:
        # Find the URI node under the directive
        for child in import_node.node.children:
            if child.type in {"uri"}:
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
        return import_node

    @override
    def get_import_names(self, import_node: CodeNode[Node]) -> Iterable[tuple[CodeNode[Node], CodeNode[Node] | None]]:
        # Dart imports specify a library; names are not listed like Python. Return the uri as name.
        yield self.get_module_name(import_node), None

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.import_

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        uri = self.get_module_name(node)
        text = uri.node_text()
        return (f"{parent}." if parent else "") + text

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        return source[node.byte_start:node.byte_end]

    @override
    def get_relative_level(self, import_node: CodeNode[Node]) -> int:
        # Dart has no relative dot-based imports; 'package:' or relative paths via URIs
        return 0

    @override
    def get_alias_bindings(self, import_node: CodeNode[Node]) -> Iterable[tuple[str, str]]:
        # Handle optional 'as identifier' in import_specification
        # Walk children to find alias after _as token
        module_node = self.get_module_name(import_node).node
        uri_text = module_node.text.decode("utf-8") if module_node.text is not None else ""
        children = list(import_node.node.children)
        for i, ch in enumerate(children):
            ch_text_b = ch.text
            if ch_text_b is not None and ch_text_b.decode("utf-8", errors="ignore") == "as" and i + 1 < len(children):
                alias_node = children[i + 1]
                alias_text_b = alias_node.text
                if alias_node.type == "identifier" and alias_text_b is not None:
                    yield alias_text_b.decode("utf-8"), uri_text
