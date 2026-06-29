from __future__ import annotations

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


def _text(source_bytes: bytes, node: Node | None) -> str:
    assert node is not None
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8")


def _find_nodes(node: Node, node_type: str) -> list[Node]:
    matches: list[Node] = []
    if node.type == node_type:
        matches.append(node)
    for child in node.named_children:
        matches.extend(_find_nodes(child, node_type))
    return matches


def test_tree_sitter_parses_authored_pane_interface_blocks() -> None:
    source = """\
pane door_control {
    kind door

    view home_story.security.door default {
        \"\"\"Door state and operator actions.\"\"\"
    }

    endpoint home_devices.unlock_door
    endpoint home_devices.lock_door
}

interface aware_app {
    api home_devices

    window main {
        layout configuration_map default {
            section workspace
            section inspector
        }

        layout scene_view {
            section scene
            section overlay_left
        }
    }

    pane door_control {
        mount home_story.security.door main.configuration_map.workspace
        mount home_story.security.door main.scene_view.overlay_left
        narrative security.control
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    pane_defs = _find_nodes(root, "pane_def")
    assert len(pane_defs) == 1
    assert _text(source_bytes, pane_defs[0].child_by_field_name("name")) == "door_control"

    pane_view_defs = _find_nodes(root, "pane_view_def")
    assert len(pane_view_defs) == 1
    assert _text(source_bytes, pane_view_defs[0].child_by_field_name("view")) == "home_story.security.door"
    assert _text(source_bytes, pane_view_defs[0].child_by_field_name("default_marker")) == "default"

    interface_defs = _find_nodes(root, "interface_def")
    assert len(interface_defs) == 1
    assert _text(source_bytes, interface_defs[0].child_by_field_name("name")) == "aware_app"

    window_defs = _find_nodes(root, "interface_window_def")
    assert len(window_defs) == 1
    assert _text(source_bytes, window_defs[0].child_by_field_name("window_name")) == "main"

    layout_defs = _find_nodes(root, "interface_layout_def")
    assert len(layout_defs) == 2
    assert _text(source_bytes, layout_defs[0].child_by_field_name("layout_name")) == "configuration_map"
    assert _text(source_bytes, layout_defs[0].child_by_field_name("default_marker")) == "default"

    pane_mount_defs = _find_nodes(root, "interface_pane_mount_def")
    assert len(pane_mount_defs) == 2
    assert _text(source_bytes, pane_mount_defs[0].child_by_field_name("target")) == "main.configuration_map.workspace"

    narratives = _find_nodes(root, "interface_pane_narrative_def")
    assert len(narratives) == 1
    assert _text(source_bytes, narratives[0].child_by_field_name("narrative")) == "security.control"
