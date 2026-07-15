from __future__ import annotations

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


def _text(source_bytes: bytes, node: Node | None) -> str:
    assert node is not None
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8")


def _find_nodes(node: Node, node_type: str) -> list[Node]:
    matches: list[Node] = []
    if node.type == node_type:
        matches.append(node)
    for child in node.named_children:
        matches.extend(_find_nodes(child, node_type))
    return matches


def test_tree_sitter_parses_attention_layout_blocks() -> None:
    source = """\
layout ide_workbench default {
    section orchestration
    section primary
    section inspector
    section console
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    layout_defs = _find_nodes(root, "attention_layout_def")
    assert len(layout_defs) == 1
    assert (
        _text(source_bytes, layout_defs[0].child_by_field_name("layout_name"))
        == "ide_workbench"
    )
    assert (
        _text(source_bytes, layout_defs[0].child_by_field_name("default_marker"))
        == "default"
    )

    section_defs = _find_nodes(root, "attention_section_def")
    assert [
        _text(source_bytes, node.child_by_field_name("section_name"))
        for node in section_defs
    ] == [
        "orchestration",
        "primary",
        "inspector",
        "console",
    ]


def test_tree_sitter_parses_attention_section_config_blocks() -> None:
    source = """\
layout coordination_center default {
    section conversation {
        title "Conversation"
        order 0
        flex 0.9
        visible true
    }

    section goal {
        title "Goal / Lane / Issue"
        description "Shared goal structure"
        order 1
        flex 2.4
        is_visible true
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    section_defs = _find_nodes(root, "attention_section_def")
    assert [
        _text(source_bytes, node.child_by_field_name("section_name"))
        for node in section_defs
    ] == [
        "conversation",
        "goal",
    ]
    assert len(_find_nodes(root, "attention_section_title_stmt")) == 2
    assert len(_find_nodes(root, "attention_section_order_stmt")) == 2
    assert len(_find_nodes(root, "attention_section_flex_stmt")) == 2
    assert len(_find_nodes(root, "attention_section_visible_stmt")) == 2
