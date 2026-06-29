"""Aware implementation of the CodeSectionMirrorAdapter."""

from collections.abc import Iterable
from typing_extensions import override
from typing import final

from tree_sitter import Node
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.node import CodeNode
from aware_code.section.mirror.adapter import CodeSectionMirrorAdapter


@final
class AwareMirrorAdapter(CodeSectionMirrorAdapter[Node]):
    """Extract `mirror` statements from Aware sources."""

    MIRROR_QUERY = AWARE_LANGUAGE.query(
        """
        (mirror_stmt) @mirror
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        captures = self.MIRROR_QUERY.captures(root)
        for mirror_node in captures.get("mirror", []):
            yield CodeNode(node=mirror_node, byte_start=mirror_node.start_byte, byte_end=mirror_node.end_byte)

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.mirror

    def _node_text(self, node: Node | None) -> str:
        if node is None or not node.text:
            return ""
        return node.text.decode("utf-8")

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        target = self._node_text(node.node.child_by_field_name("target")).strip()
        return f"mirror:{target}"

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        return source[node.byte_start:node.byte_end]

    @override
    def get_target(self, mirror_node: CodeNode[Node]) -> CodeNode[Node]:
        target = mirror_node.node.child_by_field_name("target")
        if target is None:
            raise ValueError("Mirror statement missing target")
        return CodeNode(node=target, byte_start=target.start_byte, byte_end=target.end_byte)
