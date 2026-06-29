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


def test_tree_sitter_parses_skill_blocks() -> None:
    source = '''\
skill door_control {
    api home_devices;

    endpoint open_door home_devices.door.open {
        "Open one door."
    }

    step 1 open_door {
        """
        Read the requested door state before acting.
        """
    }
}
'''
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    skill_defs = _find_nodes(root, "skill_def")
    assert len(skill_defs) == 1
    skill_def = skill_defs[0]
    assert _text(source_bytes, skill_def.child_by_field_name("name")) == "door_control"

    api_decls = _find_nodes(skill_def, "skill_api_decl")
    assert len(api_decls) == 1
    assert _text(source_bytes, api_decls[0].child_by_field_name("api")) == "home_devices"

    endpoint_defs = _find_nodes(skill_def, "skill_endpoint_def")
    assert len(endpoint_defs) == 1
    assert _text(source_bytes, endpoint_defs[0].child_by_field_name("endpoint_name")) == "open_door"
    assert _text(source_bytes, endpoint_defs[0].child_by_field_name("endpoint")) == "home_devices.door.open"

    step_defs = _find_nodes(skill_def, "skill_step_def")
    assert len(step_defs) == 1
    assert _text(source_bytes, step_defs[0].child_by_field_name("position")) == "1"
    assert _text(source_bytes, step_defs[0].child_by_field_name("endpoint_name")) == "open_door"
