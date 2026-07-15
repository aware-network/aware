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


def test_tree_sitter_parses_api_view_capability_endpoint_binding() -> None:
    source = """\
api code {
    view package_selector on CodePackage.codes state aware_code.CodePackageSelectorViewStateV1 {
        stream snapshot
        endpoint select_code view_action.select_code
    }

    capability view_action {
        endpoint select_code aware_code.SelectCodeViewActionRequest {
            response aware_code.SelectCodeViewActionResponse
        }
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    endpoint_bindings = _find_nodes(root, "api_view_capability_endpoint_def")
    assert len(endpoint_bindings) == 1
    binding = endpoint_bindings[0]
    assert _text(source_bytes, binding.child_by_field_name("action_key")) == (
        "select_code"
    )
    assert _text(source_bytes, binding.child_by_field_name("endpoint")) == (
        "view_action.select_code"
    )
