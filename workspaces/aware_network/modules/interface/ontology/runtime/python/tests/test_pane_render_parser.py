from __future__ import annotations

from pathlib import Path

import pytest
from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_grammar.formatter import format_aware_source
from aware_interface.pane_render import PaneRenderParseError, parse_pane_render_specs


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


IDENTITY_ADMISSION_RENDER_SOURCE = """\
pane identity_admission {
    kind identity_admission;
    view aware_control_identity.identity.admission.v1 {
        "Identity admission."
    }

    render default {
        view aware_control_identity.identity.admission.v1;
        version "0.1.0";
        root root;
        require node_kind column;
        require node_kind text_input;
        require action_binding view_action;

        node root column role panel;

        node title text parent root order 0 role heading {
            text "Identity admission";
            style emphasis = "primary";
        }

        node status status parent root order 1 role status {
            bind text from state.status attr status transform text fallback "Ready";
            bind tone from state.status_tone attr status_tone transform text;
        }

        node display_name_input text_input parent root order 4 role input {
            label "Display name";
            placeholder "Name";
            bind value from state.display_name attr display_name transform text;
        }

        node submit button parent root order 7 role action {
            label "Admit identity";
            action activate view admit_identity {
                input profile.display_name from display_name_input;
                input profile.public_handle from public_handle_input;
                input profile.bio from state.profile.bio;
                receipt show_receipt;
            }
        }
    }
}
"""


def test_tree_sitter_parses_pane_render_spec() -> None:
    source_bytes = IDENTITY_ADMISSION_RENDER_SOURCE.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    render_defs = _find_nodes(root, "pane_render_def")
    assert len(render_defs) == 1
    render_def = render_defs[0]
    assert _text(source_bytes, render_def.child_by_field_name("name")) == "default"

    view_decls = _find_nodes(render_def, "pane_render_view_decl")
    assert len(view_decls) == 1
    assert _text(source_bytes, view_decls[0].child_by_field_name("view")) == (
        "aware_control_identity.identity.admission.v1"
    )

    require_decls = _find_nodes(render_def, "pane_render_require_decl")
    assert len(require_decls) == 3

    node_defs = _find_nodes(render_def, "pane_render_node_def")
    assert len(node_defs) == 5
    assert _text(source_bytes, node_defs[0].child_by_field_name("node_key")) == "root"
    assert _text(source_bytes, node_defs[0].child_by_field_name("node_kind")) == "column"

    state_bindings = _find_nodes(render_def, "pane_render_state_binding_stmt")
    assert len(state_bindings) == 3
    assert _text(source_bytes, state_bindings[0].child_by_field_name("target_property")) == "text"
    assert _text(source_bytes, state_bindings[0].child_by_field_name("state_path")) == "state.status"
    assert _text(source_bytes, state_bindings[0].child_by_field_name("state_attribute")) == "status"
    assert _text(source_bytes, state_bindings[1].child_by_field_name("target_property")) == "tone"
    assert _text(source_bytes, state_bindings[1].child_by_field_name("state_path")) == "state.status_tone"
    assert _text(source_bytes, state_bindings[1].child_by_field_name("state_attribute")) == "status_tone"

    action_bindings = _find_nodes(render_def, "pane_render_action_binding_def")
    assert len(action_bindings) == 1
    assert _text(source_bytes, action_bindings[0].child_by_field_name("event")) == "activate"
    assert _text(source_bytes, action_bindings[0].child_by_field_name("action_kind")) == "view"
    assert _text(source_bytes, action_bindings[0].child_by_field_name("action")) == "admit_identity"

    input_bindings = _find_nodes(render_def, "pane_render_input_binding_stmt")
    assert len(input_bindings) == 3
    assert _text(source_bytes, input_bindings[0].child_by_field_name("payload_path")) == "profile.display_name"
    assert _text(source_bytes, input_bindings[0].child_by_field_name("source")) == "display_name_input"

    receipt_stmts = _find_nodes(render_def, "pane_render_receipt_stmt")
    assert len(receipt_stmts) == 1
    assert _text(source_bytes, receipt_stmts[0].child_by_field_name("policy")) == "show_receipt"


def test_parser_rejects_direct_api_action_binding() -> None:
    source = """\
pane identity_admission {
    render default {
        root submit;
        node submit button {
            action activate api identity.admission.submit {
                input request.identity_id from state.identity.id;
            }
        }
    }
}
"""

    with pytest.raises(PaneRenderParseError, match="Experience view actions"):
        parse_pane_render_specs(source)


def test_tree_sitter_parses_compact_node_and_bind_syntax() -> None:
    source = """\
pane network_territory {
    render default {
        view aware_network.territory.discovery.v1;

        node root scroll pane;
        node header section_header heading {
            text "Network territory";
        }
        node summary field metadata {
            bind text summary;
        }
        node nodes repeat section {
            bind items nodes;
        }
        node nodes.node_card list_item section {
            bind text item.node.hostname::nodes fallback "unknown node";
        }
        node nodes.node_card.environment_count metric metric {
            bind text item.environments::nodes count fallback "0";
        }
        node empty_message text paragraph {
            bind visible nodes is_empty;
        }
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    node_defs = _find_nodes(root, "pane_render_node_def")
    assert len(node_defs) == 7
    assert _text(source_bytes, node_defs[0].child_by_field_name("node_key")) == "root"
    assert _text(source_bytes, node_defs[0].child_by_field_name("implicit_semantic_role")) == "pane"
    assert _text(source_bytes, node_defs[4].child_by_field_name("node_key")) == "nodes.node_card"
    assert _text(source_bytes, node_defs[4].child_by_field_name("implicit_semantic_role")) == "section"

    state_bindings = _find_nodes(root, "pane_render_state_binding_stmt")
    assert len(state_bindings) == 5
    assert _text(source_bytes, state_bindings[0].child_by_field_name("state_path")) == "summary"
    assert state_bindings[0].child_by_field_name("state_attribute") is None
    assert _text(source_bytes, state_bindings[2].child_by_field_name("state_path")) == "item.node.hostname"
    assert _text(source_bytes, state_bindings[2].child_by_field_name("state_attribute")) == "nodes"
    assert _text(source_bytes, state_bindings[3].child_by_field_name("transform")) == "count"
    assert _text(source_bytes, state_bindings[4].child_by_field_name("transform")) == "is_empty"


def test_parse_disclosure_node_with_summary_detail_slots_and_identity_binding() -> None:
    source = """\
pane goal {
    render default {
        view aware_goals.workflow.goal.v1;

        node root column pane;
        node lanes repeat section {
            bind items lanes;
        }
        node lanes.lane disclosure section {
            bind identity item.lane_key::lanes fallback "lane";
        }
        node lanes.lane.summary row metadata slot summary {
        }
        node lanes.lane.summary.title text heading {
            bind text item.lane_key::lanes fallback "lane";
        }
        node lanes.lane.summary.issue_count text metadata {
            label "issue";
            bind text item.issues::lanes plural_count fallback "0 issues";
        }
        node lanes.lane.detail column section slot detail {
        }
        node lanes.lane.detail.owner field metadata {
            label "Owner";
            bind text item.owner_execution_id::lanes fallback "Unassigned";
        }
    }
}
"""

    specs = parse_pane_render_specs(source)

    assert len(specs) == 1
    spec = specs[0]
    nodes = {node.key: node for node in spec.nodes}
    assert nodes["lanes.lane"].kind == "disclosure"
    assert nodes["lanes.lane"].state_bindings[0].target_property == "identity"
    assert nodes["lanes.lane"].state_bindings[0].state_path == "state.item.lane_key"
    assert nodes["lanes.lane"].state_bindings[0].state_attribute == "lanes"
    assert nodes["lanes.lane.summary"].slot == "summary"
    assert nodes["lanes.lane.summary.issue_count"].state_bindings[0].transform == "plural_count"
    assert nodes["lanes.lane.detail"].slot == "detail"


def test_interface_admission_authored_pane_render_source_parses() -> None:
    repo_root = Path(__file__).resolve().parents[8]
    source = (
        repo_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "interface"
        / "interfaces"
        / "panes"
        / "interface_admission"
        / "interface_admission.aware"
    ).read_text(encoding="utf-8")

    specs = parse_pane_render_specs(source)

    assert len(specs) == 1
    spec = specs[0]
    assert spec.pane_name == "interface_admission"
    assert spec.view == "aware_interface.admission.v1"
    assert spec.root is None
    assert spec.nodes[0].key == "root"
    assert spec.nodes[0].kind == "scroll"
    assert spec.nodes[0].semantic_role == "pane"
    assert {requirement.capability_key for requirement in spec.requirements} >= {
        "scroll",
        "button",
        "host_capability",
    }
    assert [node.label for node in spec.nodes if node.kind == "button"] == [
        "Create Interface",
        "Select Interface",
        "Pair Device",
        "Resume Interface",
    ]


def test_tree_sitter_rejects_invalid_pane_render_bind_syntax() -> None:
    source = """\
pane identity_admission {
    render default {
        root status;
        node status text {
            bind text from state.status status;
        }
    }
}
"""
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source.encode("utf-8"))

    assert tree.root_node.has_error


def test_formatter_preserves_pane_render_spec_deterministically() -> None:
    formatted = format_aware_source(text=IDENTITY_ADMISSION_RENDER_SOURCE, indent_size=4)

    assert formatted == IDENTITY_ADMISSION_RENDER_SOURCE
