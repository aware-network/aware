"""Aware implementation of the CodeSectionProjectionAdapter."""

from __future__ import annotations

from collections.abc import Iterable
import re
from typing import final
from typing_extensions import override

from tree_sitter import Node
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_code.node.node import CodeNode
from aware_code.section.projection.adapter import (
    CodeSectionProjectionAdapter,
    ProjectionOptionSpec,
    ProjectionViewSpec,
)


@final
class AwareProjectionAdapter(CodeSectionProjectionAdapter[Node]):
    """Extract `projection` declarations (OPG) from Aware sources."""

    PROJECTION_QUERY = AWARE_LANGUAGE.query(
        """
        (projection_def) @projection
        """
    )

    ROOT_QUERY = AWARE_LANGUAGE.query(
        """
        (projection_root
          type: (qualified_name) @type)
        """
    )

    EDGE_QUERY = AWARE_LANGUAGE.query(
        """
        (projection_edge) @edge
        """
    )

    VIEW_DEF_QUERY = AWARE_LANGUAGE.query(
        """
        (projection_view_def) @view
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        captures = self.PROJECTION_QUERY.captures(root)
        for projection_node in captures.get("projection", []):
            yield CodeNode(
                node=projection_node,
                byte_start=projection_node.start_byte,
                byte_end=projection_node.end_byte,
            )

    def _node_text(self, node: Node | None) -> str:
        if node is None or not node.text:
            return ""
        return node.text.decode("utf-8")

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        name = self.get_name(node).node_text().strip()
        if not name:
            return "projection:<unknown>"
        return f"projection:{name}"

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        return self.qualname(node, parent)

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        node_bytes = source[node.byte_start:node.byte_end]

        normalized = re.sub(
            b"//[^\n]*",
            b"",
            node_bytes,
            flags=re.MULTILINE,
        )
        normalized = re.sub(b"\\s+", b" ", normalized)
        return normalized.strip()

    @override
    def get_name(self, projection_node: CodeNode[Node]) -> CodeNode[Node]:
        name_node = projection_node.node.child_by_field_name("name")
        if name_node is None:
            raise ValueError("projection_def missing name")
        return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

    @override
    def get_options(self, projection_node: CodeNode[Node]) -> list[ProjectionOptionSpec[Node]]:
        options_node = projection_node.node.child_by_field_name("options")
        if options_node is None:
            return []

        out: list[ProjectionOptionSpec[Node]] = []
        for opt in options_node.named_children:
            if opt.type != "projection_option":
                continue
            projection_id_node = opt.child_by_field_name("projection_id")
            if projection_id_node is not None:
                out.append(
                    ProjectionOptionSpec(
                        keyword="name",
                        value_node=CodeNode(
                            node=projection_id_node,
                            byte_start=projection_id_node.start_byte,
                            byte_end=projection_id_node.end_byte,
                        ),
                    )
                )
                continue

            label_node = opt.child_by_field_name("label")
            if label_node is not None:
                out.append(
                    ProjectionOptionSpec(
                        keyword="label",
                        value_node=CodeNode(
                            node=label_node,
                            byte_start=label_node.start_byte,
                            byte_end=label_node.end_byte,
                        ),
                    )
                )
                continue

            branchable_node = opt.child_by_field_name("is_branchable")
            if branchable_node is not None:
                out.append(ProjectionOptionSpec(keyword="is_branchable", value_node=None))
                continue

        return out

    @override
    def get_root_type(self, projection_node: CodeNode[Node]) -> CodeNode[Node] | None:
        captures = self.ROOT_QUERY.captures(projection_node.node)
        types = captures.get("type", [])
        if not types:
            return None
        types = sorted(types, key=lambda n: n.start_byte)
        n = types[0]
        return CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)

    @override
    def get_edges(self, projection_node: CodeNode[Node]) -> list[CodeNode[Node]]:
        captures = self.EDGE_QUERY.captures(projection_node.node)
        edges = captures.get("edge", [])
        out: list[CodeNode[Node]] = []
        for e in edges:
            out.append(CodeNode(node=e, byte_start=e.start_byte, byte_end=e.end_byte))
        out.sort(key=lambda n: n.byte_start)
        return out

    @override
    def get_edge_type(self, edge_node: CodeNode[Node]) -> CodeNode[Node]:
        n = edge_node.node.child_by_field_name("type")
        if n is None:
            raise ValueError("projection_edge missing type")
        return CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)

    @override
    def get_edge_member(self, edge_node: CodeNode[Node]) -> CodeNode[Node]:
        n = edge_node.node.child_by_field_name("member")
        if n is None:
            raise ValueError("projection_edge missing member")
        return CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)

    @override
    def get_edge_target(self, edge_node: CodeNode[Node]) -> CodeNode[Node] | None:
        n = edge_node.node.child_by_field_name("target")
        if n is None:
            return None
        return CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)

    @override
    def get_views(self, projection_node: CodeNode[Node]) -> list[ProjectionViewSpec[Node]]:
        captures = self.VIEW_DEF_QUERY.captures(projection_node.node)
        view_nodes = captures.get("view", [])
        if not view_nodes:
            return []

        out: list[ProjectionViewSpec[Node]] = []

        for view in view_nodes:
            key_node = view.child_by_field_name("view_key")
            kind_node = view.child_by_field_name("kind")
            body_node = view.child_by_field_name("body")
            if key_node is None or kind_node is None or body_node is None:
                continue

            key_raw = self._node_text(key_node).strip()
            kind = self._node_text(kind_node).strip().lower()

            is_default = any(child.type == "default" for child in view.children)

            # Collect group prefixes by walking up to the owning projection.
            prefixes: list[str] = []
            cur: Node | None = view.parent
            while cur is not None and cur.type != "projection_def":
                if cur.type == "projection_view_group":
                    prefix_node = cur.child_by_field_name("prefix")
                    prefix = self._node_text(prefix_node).strip()
                    if prefix:
                        prefixes.append(prefix)
                cur = cur.parent
            prefixes.reverse()

            prefix_segments: list[str] = []
            for p in prefixes:
                prefix_segments.extend([seg for seg in p.split(".") if seg])
            combined_prefix = ".".join(prefix_segments)

            if combined_prefix and (
                key_raw == combined_prefix or key_raw.startswith(combined_prefix + ".")
            ):
                full_key = key_raw
            elif combined_prefix:
                full_key = f"{combined_prefix}.{key_raw}" if key_raw else combined_prefix
            else:
                full_key = key_raw

            out.append(
                ProjectionViewSpec(
                    key_node=CodeNode(
                        node=key_node,
                        byte_start=key_node.start_byte,
                        byte_end=key_node.end_byte,
                    ),
                    full_key=full_key,
                    kind_node=CodeNode(
                        node=kind_node,
                        byte_start=kind_node.start_byte,
                        byte_end=kind_node.end_byte,
                    ),
                    kind=kind,
                    is_default=is_default,
                    body_node=CodeNode(
                        node=body_node,
                        byte_start=body_node.start_byte,
                        byte_end=body_node.end_byte,
                    ),
                )
            )

        out.sort(key=lambda v: v.key_node.byte_start)
        return out
