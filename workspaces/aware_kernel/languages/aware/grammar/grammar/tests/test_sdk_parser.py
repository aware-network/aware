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


def test_tree_sitter_parses_sdk_blocks() -> None:
    source = """\
sdk workspace_client {
    api workspace;

    operation load_status {
        "Load the current workspace status."
        endpoint workspace.status.get;
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    sdk_defs = _find_nodes(root, "sdk_def")
    assert len(sdk_defs) == 1
    sdk_def = sdk_defs[0]
    assert (
        _text(source_bytes, sdk_def.child_by_field_name("name")) == "workspace_client"
    )

    api_decls = _find_nodes(sdk_def, "sdk_api_decl")
    assert len(api_decls) == 1
    assert _text(source_bytes, api_decls[0].child_by_field_name("api")) == "workspace"

    operation_defs = _find_nodes(sdk_def, "sdk_operation_def")
    assert len(operation_defs) == 1
    assert (
        _text(source_bytes, operation_defs[0].child_by_field_name("operation_name"))
        == "load_status"
    )

    endpoint_defs = _find_nodes(sdk_def, "sdk_operation_endpoint_def")
    assert len(endpoint_defs) == 1
    assert (
        _text(source_bytes, endpoint_defs[0].child_by_field_name("endpoint"))
        == "workspace.status.get"
    )


def test_tree_sitter_parses_sdk_operation_dependency() -> None:
    source = """\
sdk aware_dev_sdk {
    api workspace;

    operation publish_workspace {
        endpoint workspace.publish.publish;
        operation workspace_sdk.materialize_workspace;
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    dependency_defs = _find_nodes(root, "sdk_operation_dependency_def")
    assert len(dependency_defs) == 1
    assert _text(source_bytes, dependency_defs[0].child_by_field_name("operation")) == (
        "workspace_sdk.materialize_workspace"
    )


def test_tree_sitter_parses_sdk_surface_method_policy() -> None:
    source = """\
sdk workspace_client {
    api workspace;

    surface local_status {
        "Local status operations."
        method retrieve {
            "Read local status."
            operation load_status;
            method_family retrieve;
            effect read;
            mutation_scope none;
            confirmation_policy none;
            execution_mode request_response;
            runtime_binding_kind local_handler;
        }
    }

    operation load_status {
        endpoint workspace.status.get;
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    surface_defs = _find_nodes(root, "sdk_surface_def")
    assert len(surface_defs) == 1
    assert _text(source_bytes, surface_defs[0].child_by_field_name("surface_name")) == (
        "local_status"
    )

    method_defs = _find_nodes(root, "sdk_surface_method_def")
    assert len(method_defs) == 1
    assert _text(source_bytes, method_defs[0].child_by_field_name("method_name")) == (
        "retrieve"
    )

    operation_decls = _find_nodes(root, "sdk_surface_method_operation_decl")
    assert len(operation_decls) == 1
    assert _text(source_bytes, operation_decls[0].child_by_field_name("operation")) == (
        "load_status"
    )

    method_family_decls = _find_nodes(root, "sdk_surface_method_family_decl")
    assert len(method_family_decls) == 1
    assert (
        _text(
            source_bytes,
            method_family_decls[0].child_by_field_name("method_family"),
        )
        == "retrieve"
    )


def test_tree_sitter_parses_pane_sdk_operation_and_raw_endpoint() -> None:
    source = """\
pane workspace_status {
    kind status_panel;
    view workspace_revision.default {
        "Workspace status view."
    }
    operation workspace_client.load_status;
    endpoint workspace.status.get;
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    pane_defs = _find_nodes(root, "pane_def")
    assert len(pane_defs) == 1
    pane_def = pane_defs[0]

    operation_defs = _find_nodes(pane_def, "pane_operation_def")
    assert len(operation_defs) == 1
    assert (
        _text(source_bytes, operation_defs[0].child_by_field_name("operation"))
        == "workspace_client.load_status"
    )

    endpoint_defs = _find_nodes(pane_def, "pane_endpoint_def")
    assert len(endpoint_defs) == 1
    assert (
        _text(source_bytes, endpoint_defs[0].child_by_field_name("endpoint"))
        == "workspace.status.get"
    )
