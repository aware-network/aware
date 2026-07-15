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


def test_tree_sitter_parses_authored_app_screen_blocks() -> None:
    source = """\
app aware_home {
    title "Aware Home"
    description "Control-first Home app."

    screen control {
        projection aware_control_identity layout personal
    }

    screen home {
        projection home_story layout configuration_map
    }

    screen actor {
        projection aware_actor_roles layout actor.home
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    app_defs = _find_nodes(root, "app_def")
    assert len(app_defs) == 1
    assert _text(source_bytes, app_defs[0].child_by_field_name("name")) == "aware_home"

    title_decls = _find_nodes(root, "app_title_decl")
    assert len(title_decls) == 1
    assert (
        _text(source_bytes, title_decls[0].child_by_field_name("title"))
        == '"Aware Home"'
    )

    screen_defs = _find_nodes(root, "app_screen_def")
    assert len(screen_defs) == 3
    assert (
        _text(source_bytes, screen_defs[0].child_by_field_name("screen_key"))
        == "control"
    )
    assert (
        _text(source_bytes, screen_defs[1].child_by_field_name("screen_key")) == "home"
    )

    projection_layouts = _find_nodes(root, "app_screen_projection_layout_decl")
    assert len(projection_layouts) == 3
    assert (
        _text(source_bytes, projection_layouts[0].child_by_field_name("projection"))
        == "aware_control_identity"
    )
    assert (
        _text(source_bytes, projection_layouts[0].child_by_field_name("layout"))
        == "personal"
    )
    assert (
        _text(source_bytes, projection_layouts[1].child_by_field_name("projection"))
        == "home_story"
    )
    assert (
        _text(source_bytes, projection_layouts[1].child_by_field_name("layout"))
        == "configuration_map"
    )
    assert (
        _text(source_bytes, projection_layouts[2].child_by_field_name("projection"))
        == "aware_actor_roles"
    )
    assert (
        _text(source_bytes, projection_layouts[2].child_by_field_name("layout"))
        == "actor.home"
    )
