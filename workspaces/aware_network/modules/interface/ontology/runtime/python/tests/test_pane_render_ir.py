from __future__ import annotations

import pytest

from aware_interface.pane_render import (
    PaneRenderParseError,
    PaneRenderValidationError,
    parse_pane_render_specs,
)


IDENTITY_ADMISSION_SOURCE = '''\
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

        node public_handle_input text_input parent root order 5 role input {
            label "Public handle";
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
'''


def test_parse_pane_render_specs_extracts_identity_admission_ir() -> None:
    specs = parse_pane_render_specs(IDENTITY_ADMISSION_SOURCE)

    assert len(specs) == 1
    spec = specs[0]
    assert spec.pane_name == "identity_admission"
    assert spec.name == "default"
    assert spec.view == "aware_control_identity.identity.admission.v1"
    assert spec.version == "0.1.0"
    assert spec.root == "root"
    assert [(req.capability_kind, req.capability_key) for req in spec.requirements] == [
        ("node_kind", "column"),
        ("node_kind", "text_input"),
        ("action_binding", "view_action"),
    ]

    nodes = {node.key: node for node in spec.nodes}
    assert set(nodes) == {
        "root",
        "title",
        "status",
        "display_name_input",
        "public_handle_input",
        "submit",
    }

    title = nodes["title"]
    assert title.kind == "text"
    assert title.parent_key == "root"
    assert title.order == 0
    assert title.semantic_role == "heading"
    assert title.text == "Identity admission"
    assert [(token.token, token.value) for token in title.style_tokens] == [("emphasis", "primary")]

    status = nodes["status"]
    assert len(status.state_bindings) == 2
    text_binding = status.state_bindings[0]
    assert text_binding.target_property == "text"
    assert text_binding.state_path == "state.status"
    assert text_binding.state_attribute == "status"
    assert text_binding.transform == "text"
    assert text_binding.fallback == "Ready"
    tone_binding = status.state_bindings[1]
    assert tone_binding.target_property == "tone"
    assert tone_binding.state_path == "state.status_tone"
    assert tone_binding.state_attribute == "status_tone"
    assert tone_binding.transform == "text"
    assert tone_binding.fallback is None

    submit = nodes["submit"]
    assert submit.label == "Admit identity"
    assert len(submit.action_bindings) == 1
    action_binding = submit.action_bindings[0]
    assert action_binding.event == "activate"
    assert action_binding.action_kind == "view"
    assert action_binding.action == "admit_identity"
    assert action_binding.receipt_policy == "show_receipt"
    assert [(binding.payload_path, binding.source) for binding in action_binding.input_bindings] == [
        ("profile.display_name", "display_name_input"),
        ("profile.public_handle", "public_handle_input"),
        ("profile.bio", "state.profile.bio"),
    ]


def test_parse_pane_render_specs_accepts_compact_node_and_bind_ir() -> None:
    specs = parse_pane_render_specs(
        '''\
pane network_territory {
    render default {
        view aware_network.territory.discovery.v1;

        node root scroll pane;
        node header section_header heading {
            text "Network territory";
        }
        node summary field metadata {
            label "Summary";
            bind text summary;
        }
        node nodes repeat section {
            bind items nodes;
        }
        node nodes.node_card list_item section {
            bind text item.node.hostname::nodes fallback "unknown node";
        }
        node nodes.node_card.environment_count metric metric {
            label "environments";
            bind text item.environments::nodes count fallback "0";
        }
        node empty_message text paragraph {
            bind visible nodes is_empty;
        }
    }
}
'''
    )

    spec = specs[0]
    assert spec.root is None
    nodes = {node.key: node for node in spec.nodes}

    assert nodes["root"].semantic_role == "pane"
    assert nodes["header"].parent_key is None
    assert nodes["header"].semantic_role == "heading"
    assert nodes["nodes.node_card"].parent_key is None
    assert nodes["nodes.node_card"].semantic_role == "section"
    assert nodes["nodes.node_card.environment_count"].semantic_role == "metric"

    summary_binding = nodes["summary"].state_bindings[0]
    assert summary_binding.target_property == "text"
    assert summary_binding.state_path == "state.summary"
    assert summary_binding.state_attribute is None
    assert summary_binding.transform is None

    node_title_binding = nodes["nodes.node_card"].state_bindings[0]
    assert node_title_binding.state_path == "state.item.node.hostname"
    assert node_title_binding.state_attribute == "nodes"
    assert node_title_binding.transform is None

    count_binding = nodes["nodes.node_card.environment_count"].state_bindings[0]
    assert count_binding.state_path == "state.item.environments"
    assert count_binding.state_attribute == "nodes"
    assert count_binding.transform == "count"


def test_parse_pane_render_specs_extracts_component_ports() -> None:
    specs = parse_pane_render_specs(
        '''\
pane identity_admission {
    render default {
        root root;
        require render_component aware.content.markdown_viewer;

        node root column pane;
        node bio_preview component parent root order 1 role paragraph {
            component aware.content.markdown_viewer;
            fallback_node_kind text;
            fallback_text "Bio preview unavailable";
            bind text from state.bio attr bio transform text port markdown;
        }
    }
}
'''
    )

    spec = specs[0]
    assert [(req.capability_kind, req.capability_key) for req in spec.requirements] == [
        ("render_component", "aware.content.markdown_viewer"),
    ]
    preview = {node.key: node for node in spec.nodes}["bio_preview"]
    assert preview.kind == "component"
    assert preview.component_ref == "aware.content.markdown_viewer"
    assert preview.fallback_node_kind == "text"
    assert preview.fallback_text == "Bio preview unavailable"
    binding = preview.state_bindings[0]
    assert binding.target_property == "text"
    assert binding.state_path == "state.bio"
    assert binding.state_attribute == "bio"
    assert binding.transform == "text"
    assert binding.component_input_port_key == "markdown"


@pytest.mark.parametrize(
    ("source", "match"),
    [
        (
            '''\
pane p {
    render default {
        root root;
        node root column;
    }
    render default {
        root root;
        node root column;
    }
}
''',
            "duplicate render 'default'",
        ),
        (
            '''\
pane p {
    render default {
        root root;
        node root column;
        node root text;
    }
}
''',
            "duplicate node 'root'",
        ),
        (
            '''\
pane p {
    render default {
        node root.header column;
    }
}
''',
            "missing root",
        ),
        (
            '''\
pane p {
    render default {
        node root column;
        node root.header text parent other;
    }
}
''',
            "path implies parent 'root'",
        ),
        (
            '''\
pane p {
    render default {
        node root column;
        node node_title text {
            bind text item.node.hostname;
        }
    }
}
''',
            "requires explicit state attribute authority",
        ),
        (
            '''\
pane p {
    render default {
        root root;
        node root column parent missing;
    }
}
''',
            "missing parent 'missing'",
        ),
        (
            '''\
pane p {
    render default {
        root submit;
        node submit button {
            action activate view identity_submit {
                input profile.name from missing_input;
            }
        }
    }
}
''',
            "missing local source 'missing_input'",
        ),
        (
            '''\
pane p {
    render default {
        root root;
        node root column;
        node preview component parent root;
    }
}
''',
            "requires component ref",
        ),
    ],
)
def test_parse_pane_render_specs_rejects_invalid_local_structure(source: str, match: str) -> None:
    with pytest.raises(PaneRenderValidationError, match=match):
        parse_pane_render_specs(source)


def test_parse_pane_render_specs_rejects_syntax_errors() -> None:
    with pytest.raises(PaneRenderParseError, match="syntax errors"):
        parse_pane_render_specs(
            '''\
pane p {
    render default {
        root root;
        node root column {
            bind text from state.status status;
        }
    }
}
'''
        )
