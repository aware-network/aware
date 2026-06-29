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


def test_tree_sitter_parses_node_blocks() -> None:
    source = """\
node kernel_host {
    include aware.local_agent_kernel;
    environment home-story {
        profile os.default package aware-workspace-environment-profile
    }
    ontology storage-ontology;
    service aware_attention;
    interface aware_workspace;
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    node_defs = _find_nodes(root, "node_def")
    assert len(node_defs) == 1
    node_def = node_defs[0]
    assert _text(source_bytes, node_def.child_by_field_name("name")) == "kernel_host"

    include_decls = _find_nodes(node_def, "node_include_decl")
    assert len(include_decls) == 1
    assert (
        _text(source_bytes, include_decls[0].child_by_field_name("target"))
        == "aware.local_agent_kernel"
    )

    environment_decls = _find_nodes(node_def, "node_environment_decl")
    assert len(environment_decls) == 1
    assert (
        _text(source_bytes, environment_decls[0].child_by_field_name("target"))
        == "home-story"
    )

    experience_decls = _find_nodes(node_def, "node_environment_experience_decl")
    assert experience_decls == []

    profile_decls = _find_nodes(node_def, "node_environment_profile_decl")
    assert len(profile_decls) == 1
    assert (
        _text(source_bytes, profile_decls[0].child_by_field_name("profile"))
        == "os.default"
    )
    assert (
        _text(source_bytes, profile_decls[0].child_by_field_name("package"))
        == "aware-workspace-environment-profile"
    )

    service_decls = _find_nodes(node_def, "node_service_decl")
    assert len(service_decls) == 1
    assert (
        _text(source_bytes, service_decls[0].child_by_field_name("target"))
        == "aware_attention"
    )

    ontology_decls = _find_nodes(node_def, "node_ontology_decl")
    assert len(ontology_decls) == 1
    assert (
        _text(source_bytes, ontology_decls[0].child_by_field_name("target"))
        == "storage-ontology"
    )

    interface_decls = _find_nodes(node_def, "node_interface_decl")
    assert len(interface_decls) == 1
    assert (
        _text(source_bytes, interface_decls[0].child_by_field_name("target"))
        == "aware_workspace"
    )


def test_tree_sitter_parses_service_code_package_activation() -> None:
    source = """\
node kernel_services_host {
    service aware_experience {
        package experience aware-workspace-experience;
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    service_decls = _find_nodes(root, "node_service_decl")
    assert len(service_decls) == 1
    assert (
        _text(source_bytes, service_decls[0].child_by_field_name("target"))
        == "aware_experience"
    )

    package_decls = _find_nodes(root, "node_service_code_package_decl")
    assert len(package_decls) == 1
    assert (
        _text(source_bytes, package_decls[0].child_by_field_name("slot"))
        == "experience"
    )
    assert (
        _text(source_bytes, package_decls[0].child_by_field_name("package"))
        == "aware-workspace-experience"
    )
