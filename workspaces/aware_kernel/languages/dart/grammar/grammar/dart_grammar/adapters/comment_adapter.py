"""Dart implementation of the CodeSectionCommentAdapter."""

from collections.abc import Iterable
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query

# Kernel Graph Ontology
from aware_code_ontology.comment.code_section_comment_enums import CodeSectionCommentType
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.comment.adapter import CodeSectionCommentAdapter

# Dart Grammar
from dart_grammar._tree_sitter_dart import DART_LANGUAGE


class DartCommentAdapter(CodeSectionCommentAdapter[Node]):
    """Extract comments and doc comments from Dart code."""

    CLASS_NAME_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (class_definition
          name: (identifier) @name)
        """
    )

    ENUM_NAME_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (enum_declaration
          name: (identifier) @name)
        """
    )

    FUNCTION_NAME_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (function_signature
          name: (identifier) @name)
        (method_signature
          (function_signature
            name: (identifier) @name))
        """
    )

    COMMENT_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (comment) @comment
        (documentation_comment) @doc
        """
    )

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.comment

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        return source[node.byte_start:node.byte_end]

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        caps = self.COMMENT_QUERY.captures(root)
        for key in ("comment", "doc"):
            for n in caps.get(key, []):
                yield CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)

    @override
    def get_content_segments(self, comment_node: CodeNode[Node], source: bytes) -> Iterable[CodeNode[Node]]:
        # Split by newlines in the source slice
        slice_b = source[comment_node.byte_start:comment_node.byte_end]
        start = comment_node.byte_start
        offset = 0
        for line in slice_b.splitlines(True):  # keepends
            seg_start = start + offset
            seg_end = seg_start + len(line)
            yield CodeNode(node=comment_node.node, byte_start=seg_start, byte_end=seg_end)
            offset += len(line)

    @override
    def get_comment_type(self, comment_node: CodeNode[Node]) -> CodeSectionCommentType:
        text_b = comment_node.node.text
        if text_b is None:
            return CodeSectionCommentType.line
        text = text_b.decode("utf-8")
        if text.startswith("///"):
            return CodeSectionCommentType.doc
        if text.startswith("/*"):
            return CodeSectionCommentType.block
        return CodeSectionCommentType.line

    @override
    def get_associated_node(self, comment_node: CodeNode[Node], source: bytes) -> CodeNode[Node] | None:
        # Canonical heuristic: documentation_comment applies to the next named sibling declaration.
        if comment_node.node.type != "documentation_comment":
            return None

        cur = comment_node.node
        sib = cur.next_named_sibling
        # Skip annotations/metadata that can appear between doc and declaration.
        while sib is not None and sib.type in {"annotation", "metadata"}:
            sib = sib.next_named_sibling

        if sib is None:
            return None

        # Tree-sitter-dart sometimes exposes the class/enum name identifier as the next named sibling
        # rather than the full declaration node.
        if sib.type == "identifier" and sib.parent is not None:
            if sib.parent.type in {"class_definition", "enum_declaration"}:
                parent = sib.parent
                return CodeNode(node=parent, byte_start=parent.start_byte, byte_end=parent.end_byte)

        # Supported associations for backfill + comment linkage.
        if sib.type in {
            "class_definition",
            "enum_declaration",
            "function_signature",
            "method_signature",
        }:
            return CodeNode(node=sib, byte_start=sib.start_byte, byte_end=sib.end_byte)
        return None

    @override
    def section_lookup_key(self, associated_node: CodeNode[Node]) -> tuple[CodeSectionType, str] | None:
        """
        Provide deterministic ref lookup for comment linkage so builder can attach comments by ref.
        """
        n = associated_node.node

        if n.type == "class_definition":
            caps = self.CLASS_NAME_QUERY.captures(n).get("name", [])
            if not caps:
                return None
            name = caps[0].text.decode("utf-8") if caps[0].text is not None else ""
            return CodeSectionType.class_, name

        if n.type == "enum_declaration":
            caps = self.ENUM_NAME_QUERY.captures(n).get("name", [])
            if not caps:
                return None
            name = caps[0].text.decode("utf-8") if caps[0].text is not None else ""
            return CodeSectionType.enum, name

        if n.type in {"function_signature", "method_signature"}:
            caps = self.FUNCTION_NAME_QUERY.captures(n).get("name", [])
            if not caps:
                return None
            fn_name = caps[0].text.decode("utf-8") if caps[0].text is not None else ""

            # Qualify with enclosing class if present.
            cur = n.parent
            while cur is not None:
                if cur.type == "class_definition":
                    cls_caps = self.CLASS_NAME_QUERY.captures(cur).get("name", [])
                    if cls_caps:
                        cls_name = cls_caps[0].text.decode("utf-8") if cls_caps[0].text is not None else ""
                        return CodeSectionType.function, f"{cls_name}.{fn_name}"
                    break
                cur = cur.parent
            return CodeSectionType.function, fn_name

        return None

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        # Use byte range as stable identifier
        return (f"{parent}." if parent else "") + f"comment@{node.byte_start}-{node.byte_end}"
