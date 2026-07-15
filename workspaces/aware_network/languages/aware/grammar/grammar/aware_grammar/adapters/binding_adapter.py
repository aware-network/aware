"""Aware implementation of the CodeSectionBindingAdapter."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import final
from typing_extensions import override

from tree_sitter import Node
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_code.node.node import CodeNode
from aware_code.section.binding.adapter import (
    BindingMapSpec,
    CodeSectionBindingAdapter,
)


@final
class AwareBindingAdapter(CodeSectionBindingAdapter[Node]):
    """Extract `binding` declarations from Aware sources."""

    BINDING_QUERY = AWARE_LANGUAGE.query(
        """
        (binding_def) @binding
        """
    )

    MAP_QUERY = AWARE_LANGUAGE.query(
        """
        (binding_map_def) @map
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        captures = self.BINDING_QUERY.captures(root)
        for binding_node in captures.get("binding", []):
            yield CodeNode(
                node=binding_node,
                byte_start=binding_node.start_byte,
                byte_end=binding_node.end_byte,
            )

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        _ = parent
        source_graph = self.get_source_graph(node).node_text().strip()
        target_graph = self.get_target_graph(node).node_text().strip()
        return f"binding:{source_graph}->{target_graph}"

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        return self.qualname(node, parent)

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        node_bytes = source[node.byte_start : node.byte_end]
        normalized = re.sub(
            b"//[^\\n]*",
            b"",
            node_bytes,
            flags=re.MULTILINE,
        )
        normalized = re.sub(b"\\s+", b" ", normalized)
        return normalized.strip()

    @override
    def get_source_graph(self, binding_node: CodeNode[Node]) -> CodeNode[Node]:
        source_graph_node = binding_node.node.child_by_field_name("source_graph")
        if source_graph_node is None:
            raise ValueError("binding_def missing source_graph")
        return CodeNode(
            node=source_graph_node,
            byte_start=source_graph_node.start_byte,
            byte_end=source_graph_node.end_byte,
        )

    @override
    def get_target_graph(self, binding_node: CodeNode[Node]) -> CodeNode[Node]:
        target_graph_node = binding_node.node.child_by_field_name("target_graph")
        if target_graph_node is None:
            raise ValueError("binding_def missing target_graph")
        return CodeNode(
            node=target_graph_node,
            byte_start=target_graph_node.start_byte,
            byte_end=target_graph_node.end_byte,
        )

    @override
    def get_maps(self, binding_node: CodeNode[Node]) -> list[BindingMapSpec[Node]]:
        captures = self.MAP_QUERY.captures(binding_node.node)
        maps = captures.get("map", [])
        out: list[BindingMapSpec[Node]] = []
        for map_node in sorted(maps, key=lambda n: n.start_byte):
            name_node = map_node.child_by_field_name("name")
            source_node = map_node.child_by_field_name("source")
            target_node = map_node.child_by_field_name("target")
            body_node = map_node.child_by_field_name("body")
            template_value_node: Node | None = None
            if body_node is not None:
                for child in body_node.named_children:
                    if child.type != "binding_map_template_def":
                        continue
                    template_body_node = child.child_by_field_name("body")
                    if template_body_node is None:
                        continue
                    template_value_node = template_body_node.child_by_field_name("value")
                    if template_value_node is not None:
                        break
            if name_node is None or source_node is None or target_node is None:
                continue
            out.append(
                BindingMapSpec(
                    name_node=CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte),
                    source_node=CodeNode(
                        node=source_node,
                        byte_start=source_node.start_byte,
                        byte_end=source_node.end_byte,
                    ),
                    target_node=CodeNode(
                        node=target_node,
                        byte_start=target_node.start_byte,
                        byte_end=target_node.end_byte,
                    ),
                    body_node=(
                        CodeNode(node=body_node, byte_start=body_node.start_byte, byte_end=body_node.end_byte)
                        if body_node is not None
                        else None
                    ),
                    template_value_node=(
                        CodeNode(
                            node=template_value_node,
                            byte_start=template_value_node.start_byte,
                            byte_end=template_value_node.end_byte,
                        )
                        if template_value_node is not None
                        else None
                    ),
                )
            )
        return out
