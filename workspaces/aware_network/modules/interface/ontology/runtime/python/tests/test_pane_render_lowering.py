from __future__ import annotations

import json

import pytest

from aware_interface.pane_render import (
    PaneRenderLoweringError,
    lower_pane_render_spec_to_payload,
    parse_pane_render_specs,
)


IDENTITY_ADMISSION_AUTHORED_RENDER = """\
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

        node root column role pane;

        node title text parent root order 0 role heading {
            text "Identity admission";
            style emphasis = "primary";
        }

        node status status parent root order 1 role status {
            bind text from state.status attr status transform text;
            bind tone from state.status_tone attr status_tone transform text;
        }

        node display_name text parent root order 2 role paragraph {
            bind text from state.display_name attr display_name transform text fallback "No display name configured";
        }

        node display_name_input text_input parent root order 4 role input {
            label "Display name";
            bind value from state.display_name attr display_name transform text;
        }

        node bio_input text_input parent root order 6 role input {
            label "Bio";
            bind value from state.bio attr bio transform text;
        }

        node submit button parent root order 7 role action {
            label "Admit identity";
            action activate view admit_identity {
                input profile.display_name from display_name_input;
                input profile.bio from bio_input;
                input profile.status from state.status;
                receipt show_receipt;
            }
        }
    }
}
"""


def test_lower_pane_render_spec_to_compatibility_payload() -> None:
    spec = parse_pane_render_specs(IDENTITY_ADMISSION_AUTHORED_RENDER)[0]

    payload = lower_pane_render_spec_to_payload(spec)

    assert payload["name"] == "identity_admission_default"
    assert payload["pane_name"] == "identity_admission"
    assert payload["spec_version"] == "0.1.0"
    assert payload["view_ref"] == "aware_control_identity.identity.admission.v1"
    assert payload["root_node_key"] == "root"
    assert "spec_id" not in payload
    assert "pane_kind" not in payload
    assert "state_model_id" not in payload

    assert payload["renderer_requirements"] == [
        {
            "capability_kind": "node_kind",
            "capability_key": "column",
            "is_required": True,
        },
        {
            "capability_kind": "node_kind",
            "capability_key": "text_input",
            "is_required": True,
        },
        {
            "capability_kind": "action_binding",
            "capability_key": "view_action",
            "is_required": True,
        },
    ]

    nodes = {node["node_key"]: node for node in payload["nodes"] if isinstance(node, dict)}
    assert nodes["root"] == {
        "node_key": "root",
        "node_kind": "column",
        "order": 0,
        "semantic_role": "pane",
    }
    assert nodes["title"]["style_tokens"] == [
        {
            "token_key": "emphasis",
            "token_value": "primary",
        }
    ]

    assert nodes["status"]["state_bindings"] == [
        {
            "binding_key": "status_text",
            "target_property": "text",
            "json_path": "$.status",
            "state_attribute_ref": "status",
            "transform": "text",
        },
        {
            "binding_key": "status_tone",
            "target_property": "tone",
            "json_path": "$.status_tone",
            "state_attribute_ref": "status_tone",
            "transform": "text",
        },
    ]
    assert nodes["display_name"]["state_bindings"] == [
        {
            "binding_key": "display_name_text",
            "target_property": "text",
            "json_path": "$.display_name",
            "state_attribute_ref": "display_name",
            "transform": "text",
            "fallback_value": "No display name configured",
        }
    ]

    action = nodes["submit"]["action_bindings"][0]
    assert action == {
        "binding_key": "admit_identity",
        "event": "activate",
        "action_key": "admit_identity",
        "action_kind": "view_action",
        "label": "Admit identity",
        "receipt_policy": "show_receipt",
        "view_action_key": "admit_identity",
        "input_bindings": [
            {
                "payload_path": "profile.display_name",
                "source_node_key": "display_name_input",
            },
            {
                "payload_path": "profile.bio",
                "source_node_key": "bio_input",
            },
            {
                "payload_path": "profile.status",
                "source_json_path": "$.status",
            },
        ],
    }


def test_lower_pane_render_spec_is_deterministic() -> None:
    spec = parse_pane_render_specs(IDENTITY_ADMISSION_AUTHORED_RENDER)[0]

    first = json.dumps(lower_pane_render_spec_to_payload(spec), sort_keys=True)
    second = json.dumps(lower_pane_render_spec_to_payload(spec), sort_keys=True)

    assert first == second


def test_lower_pane_render_spec_maps_component_ports() -> None:
    spec = parse_pane_render_specs(
        """\
pane identity_admission {
    render default {
        root root;
        node root column pane;
        node bio_preview component parent root order 1 role paragraph {
            component aware.content.markdown_viewer;
            fallback_node_kind text;
            fallback_text "Bio preview unavailable";
            bind text from state.bio attr bio transform text port markdown;
        }
    }
}
"""
    )[0]

    payload = lower_pane_render_spec_to_payload(spec)
    nodes = {node["node_key"]: node for node in payload["nodes"] if isinstance(node, dict)}

    assert nodes["bio_preview"] == {
        "node_key": "bio_preview",
        "node_kind": "component",
        "order": 1,
        "parent_node_key": "root",
        "semantic_role": "paragraph",
        "component_ref": "aware.content.markdown_viewer",
        "fallback_node_kind": "text",
        "fallback_text": "Bio preview unavailable",
        "state_bindings": [
            {
                "binding_key": "bio_text",
                "target_property": "text",
                "json_path": "$.bio",
                "state_attribute_ref": "bio",
                "transform": "text",
                "component_input_port_key": "markdown",
            }
        ],
    }


def test_storage_media_ref_target_is_materialization_supported() -> None:
    from aware_interface.builder import _PANE_RENDER_STATE_TARGETS

    spec = parse_pane_render_specs(
        """\
pane media_gallery {
    render default {
        root hero_image;
        node hero_image component section {
            component aware.media.image;
            bind media_ref hero.image::hero_image;
        }
    }
}
"""
    )[0]

    payload = lower_pane_render_spec_to_payload(spec)
    binding = payload["nodes"][0]["state_bindings"][0]

    assert "media_ref" in _PANE_RENDER_STATE_TARGETS
    assert binding == {
        "binding_key": "hero_image_media_ref",
        "target_property": "media_ref",
        "json_path": "$.hero.image",
        "state_attribute_ref": "hero_image",
        "transform": "raw",
    }


def test_lower_pane_render_spec_maps_repeat_nodes_and_count_transform() -> None:
    spec = parse_pane_render_specs(
        """\
pane network_territory {
    render default {
        root root;
        require node_kind repeat;

        node root column role pane;
        node nodes repeat parent root order 0 role section {
            bind items from state.nodes attr nodes transform raw;
        }
        node node_card box parent nodes order 0 role section;
        node node_title text parent node_card order 0 role heading {
            bind text from state.item.node.hostname attr nodes transform text fallback "unknown node";
        }
        node environment_count status parent node_card order 1 role status {
            bind text from state.item.environments attr nodes transform count fallback "0";
        }
        node environments repeat parent node_card order 2 role section {
            bind items from state.item.environments attr nodes transform raw;
        }
        node environment_title text parent environments order 0 role paragraph {
            bind text from state.item.environment_title attr nodes transform text fallback "environment";
        }
        node inspect_environment button parent environments order 1 role action {
            label "Inspect environment";
            action activate view inspect_environment {
                input selection.node_id from state.parent.node.node_id;
                input selection.environment_id from state.item.environment_id;
                input selection.node_index from state.parent_index;
                input selection.environment_index from state.item_index;
            }
        }
    }
}
"""
    )[0]

    payload = lower_pane_render_spec_to_payload(spec)
    nodes = {node["node_key"]: node for node in payload["nodes"] if isinstance(node, dict)}

    assert nodes["nodes"]["node_kind"] == "repeat"
    assert nodes["nodes"]["state_bindings"] == [
        {
            "binding_key": "nodes_items",
            "target_property": "items",
            "json_path": "$.nodes",
            "state_attribute_ref": "nodes",
            "transform": "raw",
        }
    ]
    assert nodes["node_title"]["state_bindings"] == [
        {
            "binding_key": "nodes_text",
            "target_property": "text",
            "json_path": "$.item.node.hostname",
            "state_attribute_ref": "nodes",
            "transform": "text",
            "fallback_value": "unknown node",
        }
    ]
    assert nodes["environment_count"]["state_bindings"] == [
        {
            "binding_key": "nodes_text",
            "target_property": "text",
            "json_path": "$.item.environments",
            "state_attribute_ref": "nodes",
            "transform": "count",
            "fallback_value": "0",
        }
    ]
    assert nodes["environments"]["state_bindings"] == [
        {
            "binding_key": "nodes_items",
            "target_property": "items",
            "json_path": "$.item.environments",
            "state_attribute_ref": "nodes",
            "transform": "raw",
        }
    ]
    assert nodes["environment_title"]["state_bindings"] == [
        {
            "binding_key": "nodes_text",
            "target_property": "text",
            "json_path": "$.item.environment_title",
            "state_attribute_ref": "nodes",
            "transform": "text",
            "fallback_value": "environment",
        }
    ]
    assert nodes["inspect_environment"]["action_bindings"] == [
        {
            "binding_key": "inspect_environment",
            "event": "activate",
            "action_key": "inspect_environment",
            "action_kind": "view_action",
            "label": "Inspect environment",
            "receipt_policy": "none",
            "view_action_key": "inspect_environment",
            "input_bindings": [
                {
                    "payload_path": "selection.node_id",
                    "source_json_path": "$.parent.node.node_id",
                },
                {
                    "payload_path": "selection.environment_id",
                    "source_json_path": "$.item.environment_id",
                },
                {
                    "payload_path": "selection.node_index",
                    "source_json_path": "$.parent_index",
                },
                {
                    "payload_path": "selection.environment_index",
                    "source_json_path": "$.item_index",
                },
            ],
        }
    ]


def test_lower_pane_render_spec_derives_compact_root_nodes_and_bindings() -> None:
    spec = parse_pane_render_specs(
        """\
pane network_territory {
    render default {
        view aware_network.territory.discovery.v1;
        require node_kind repeat;

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
"""
    )[0]

    payload = lower_pane_render_spec_to_payload(spec)
    assert payload["root_node_key"] == "root"
    nodes = {node["node_key"]: node for node in payload["nodes"] if isinstance(node, dict)}

    assert nodes["root"] == {
        "node_key": "root",
        "node_kind": "scroll",
        "order": 0,
        "semantic_role": "pane",
    }
    assert nodes["header"]["parent_node_key"] == "root"
    assert nodes["header"]["order"] == 0
    assert nodes["summary"]["parent_node_key"] == "root"
    assert nodes["summary"]["order"] == 1
    assert nodes["nodes"]["parent_node_key"] == "root"
    assert nodes["nodes"]["order"] == 2
    assert nodes["empty_message"]["parent_node_key"] == "root"
    assert nodes["empty_message"]["order"] == 3
    assert nodes["nodes.node_card"]["parent_node_key"] == "nodes"
    assert nodes["nodes.node_card"]["order"] == 0
    assert nodes["nodes.node_card.environment_count"]["parent_node_key"] == "nodes.node_card"
    assert nodes["nodes.node_card.environment_count"]["order"] == 0

    assert nodes["summary"]["state_bindings"] == [
        {
            "binding_key": "summary_text",
            "target_property": "text",
            "json_path": "$.summary",
            "state_attribute_ref": "summary",
            "transform": "text",
        }
    ]
    assert nodes["nodes"]["state_bindings"] == [
        {
            "binding_key": "nodes_items",
            "target_property": "items",
            "json_path": "$.nodes",
            "state_attribute_ref": "nodes",
            "transform": "raw",
        }
    ]
    assert nodes["nodes.node_card"]["state_bindings"] == [
        {
            "binding_key": "nodes_text",
            "target_property": "text",
            "json_path": "$.item.node.hostname",
            "state_attribute_ref": "nodes",
            "transform": "text",
            "fallback_value": "unknown node",
        }
    ]
    assert nodes["nodes.node_card.environment_count"]["state_bindings"] == [
        {
            "binding_key": "nodes_text",
            "target_property": "text",
            "json_path": "$.item.environments",
            "state_attribute_ref": "nodes",
            "transform": "count",
            "fallback_value": "0",
        }
    ]
    assert nodes["empty_message"]["state_bindings"] == [
        {
            "binding_key": "nodes_visible",
            "target_property": "visible",
            "json_path": "$.nodes",
            "state_attribute_ref": "nodes",
            "transform": "is_empty",
        }
    ]


def test_lower_pane_render_spec_rejects_non_state_dotted_input_source() -> None:
    spec = parse_pane_render_specs(
        """\
pane p {
    render default {
        root submit;
        node submit button {
            action activate view submit {
                input payload.value from focus.current;
            }
        }
    }
}
"""
    )[0]

    with pytest.raises(PaneRenderLoweringError, match="unsupported non-state source"):
        lower_pane_render_spec_to_payload(spec)


def test_lower_pane_render_spec_accepts_dotted_local_input_source() -> None:
    spec = parse_pane_render_specs(
        """\
pane profile_editor {
    render default {
        node root column pane;
        node root.form column section;
        node root.form.display_name_input text_input input;
        node submit button action {
            action activate view submit {
                input profile.display_name from root.form.display_name_input;
            }
        }
    }
}
"""
    )[0]

    payload = lower_pane_render_spec_to_payload(spec)
    nodes = {node["node_key"]: node for node in payload["nodes"] if isinstance(node, dict)}

    assert nodes["submit"]["action_bindings"] == [
        {
            "binding_key": "submit",
            "event": "activate",
            "action_key": "submit",
            "action_kind": "view_action",
            "label": "Submit",
            "receipt_policy": "none",
            "view_action_key": "submit",
            "input_bindings": [
                {
                    "payload_path": "profile.display_name",
                    "source_node_key": "root.form.display_name_input",
                }
            ],
        }
    ]


def test_lower_pane_render_spec_maps_operational_primitives_and_is_empty() -> None:
    spec = parse_pane_render_specs(
        """\
pane network_territory {
    render default {
        root root;
        require node_kind metric;
        require node_kind field;

        node root column role pane;
        node empty_message text parent root order 0 role paragraph {
            bind visible from state.nodes attr nodes transform is_empty;
            bind text from state.empty_message attr empty_message transform text fallback "No territory has been published yet";
        }
        node territory_header section_header parent root order 1 role heading {
            text "Territory";
        }
        node node_metric metric parent root order 2 role metric {
            label "nodes";
            bind text from state.nodes attr nodes transform count fallback "0";
        }
        node source field parent root order 3 role metadata {
            label "Source";
            bind text from state.authority_source_url attr authority_source_url transform text;
            style tone = "provenance";
        }
        node node_item list_item parent root order 4 role section {
            text "Network node";
        }
    }
}
"""
    )[0]

    payload = lower_pane_render_spec_to_payload(spec)
    nodes = {node["node_key"]: node for node in payload["nodes"] if isinstance(node, dict)}

    assert nodes["empty_message"]["state_bindings"] == [
        {
            "binding_key": "nodes_visible",
            "target_property": "visible",
            "json_path": "$.nodes",
            "state_attribute_ref": "nodes",
            "transform": "is_empty",
        },
        {
            "binding_key": "empty_message_text",
            "target_property": "text",
            "json_path": "$.empty_message",
            "state_attribute_ref": "empty_message",
            "transform": "text",
            "fallback_value": "No territory has been published yet",
        },
    ]
    assert nodes["territory_header"]["node_kind"] == "section_header"
    assert nodes["node_metric"]["node_kind"] == "metric"
    assert nodes["node_metric"]["semantic_role"] == "metric"
    assert nodes["source"]["node_kind"] == "field"
    assert nodes["source"]["semantic_role"] == "metadata"
    assert nodes["source"]["style_tokens"] == [
        {
            "token_key": "tone",
            "token_value": "provenance",
        }
    ]
    assert nodes["node_item"]["node_kind"] == "list_item"
