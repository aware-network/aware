from __future__ import annotations

from pathlib import Path
import tomllib
from uuid import uuid4

from aware_attention.compile import compile_attention_workspace
from aware_experience.environment_profile.compiler import (
    load_environment_profile_ownership_from_sources,
)
from aware_experience.projection.compiler import (
    load_projection_experience_ownership_from_sources,
)
from aware_interface.ontology.materialization.render import (
    _pane_action_binding_runtime_payload,
)
from aware_interface.pane_render import lower_pane_render_spec_to_payload
from aware_interface.pane_render import parse_pane_render_specs
from aware_interface_ontology.render.pane_action_binding import PaneActionBinding
from aware_interface_ontology.render.pane_render_enums import PaneActionEvent


NETWORK_ROOT = Path(__file__).resolve().parents[6]
META_MODULE_ROOT = NETWORK_ROOT / "modules" / "meta"
META_GRAPH_ATTENTION_ROOT = META_MODULE_ROOT / "attentions" / "aware_meta_graph_attention"
META_GRAPH_PANE_ROOT = META_MODULE_ROOT / "interfaces" / "panes" / "aware_meta_graph_panes"
META_EXPERIENCE_ROOT = META_MODULE_ROOT / "experiences" / "aware_meta_experience"


def _meta_graph_authored_render() -> str:
    return (META_GRAPH_PANE_ROOT / "meta_graph_canvas.aware").read_text(encoding="utf-8")


def test_meta_graph_pane_render_spec_binds_canvas_component_inputs() -> None:
    spec = parse_pane_render_specs(_meta_graph_authored_render())[0]

    payload = lower_pane_render_spec_to_payload(spec)

    assert payload["view_ref"] == "aware_meta.graph.canvas.v1"
    assert payload["renderer_requirements"] == [
        {
            "capability_kind": "render_component",
            "capability_key": "aware.meta.graph.canvas",
            "is_required": True,
        }
    ]
    canvas = payload["nodes"][0]
    assert canvas["node_kind"] == "component"
    assert canvas["component_ref"] == "aware.meta.graph.canvas"
    assert canvas["fallback_node_kind"] == "text"
    assert canvas["fallback_text"] == "Meta graph unavailable"
    ports = {binding["component_input_port_key"]: binding for binding in canvas["state_bindings"]}
    assert sorted(ports) == [
        "graph_snapshot",
        "object_config_graph_ref",
        "object_instance_graph_branch_ref",
        "object_instance_graph_commit_ref",
        "object_instance_graph_ref",
        "object_projection_graph_ref",
        "selected_identity",
        "viewport_state",
    ]
    assert ports["graph_snapshot"]["json_path"] == "$.graph_snapshot"
    assert ports["graph_snapshot"]["transform"] == "raw"
    assert ports["selected_identity"]["target_property"] == "text"
    assert ports["selected_identity"]["transform"] == "text"
    assert canvas["action_bindings"] == [
        {
            "binding_key": "select_identity",
            "event": "activate",
            "action_key": "select_identity",
            "action_kind": "view_action",
            "label": "Select Identity",
            "receipt_policy": "none",
            "view_action_key": "select_identity",
            "input_bindings": [],
        }
    ]


def test_meta_graph_action_port_survives_runtime_payload_materialization() -> None:
    binding = PaneActionBinding.model_construct(
        pane_render_node_id=uuid4(),
        binding_key="select_identity",
        event=PaneActionEvent.activate,
        action_key="select_identity",
        component_action_port_key="select_identity",
        label="Select identity",
        receipt_policy="none",
        input_bindings=[],
    )

    payload = _pane_action_binding_runtime_payload(binding)

    assert payload["binding_key"] == "select_identity"
    assert payload["view_action_key"] == "select_identity"
    assert payload["component_action_port_key"] == "select_identity"


def test_meta_graph_attention_profile_and_pane_are_module_owned() -> None:
    module_spec = tomllib.loads((META_MODULE_ROOT / "aware.module.toml").read_text(encoding="utf-8"))
    packages = {package["id"]: package for package in module_spec["packages"]}
    assert packages["meta_graph_attention"] == {
        "id": "meta_graph_attention",
        "kind": "attention",
        "manifest": "attentions/aware_meta_graph_attention/aware.attention.toml",
        "visibility": "module",
    }
    assert packages["meta_graph_panes"] == {
        "id": "meta_graph_panes",
        "kind": "pane",
        "manifest": "interfaces/panes/aware_meta_graph_panes/aware.pane.toml",
        "visibility": "module",
    }

    attention_result = compile_attention_workspace(
        toml_path=META_GRAPH_ATTENTION_ROOT / "aware.attention.toml",
        repo_root=META_MODULE_ROOT,
    )
    assert attention_result.package_name == "aware_meta_graph_attention"
    layout = attention_result.compile_plan.layout_ontology[0]
    assert layout.layout_key == "graph_canvas"
    assert [section.section_key for section in layout.sections] == ["graph"]

    projection_ownership = load_projection_experience_ownership_from_sources(
        package_root=META_EXPERIENCE_ROOT,
        source_files=(Path("experiences.aware"),),
    )
    profiles = load_environment_profile_ownership_from_sources(
        package_root=META_EXPERIENCE_ROOT,
        source_files=(Path("profiles.aware"),),
        projection_experience_ownership=projection_ownership,
    )
    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.experience_name == "aware_meta"
    assert profile.key == "graph.default"

    thread = profile.process_configs[0].thread_configs[0]
    assert [projection.view_key for projection in thread.projection_experiences] == ["graph.canvas.v1"]
    layout_config = thread.layout_configs[0]
    assert layout_config.layout_key == "graph_canvas"
    section = layout_config.sections[0]
    assert section.section_key == "graph"
    assert section.projection_experience_name == "aware_meta"
    assert section.view_key == "graph.canvas.v1"
    assert section.section_graph_binding_key == "meta.graph.canvas"

    authored_profile = (META_EXPERIENCE_ROOT / "profiles.aware").read_text(encoding="utf-8")
    assert "surface meta.graph" not in authored_profile
    assert "apps/interface_flutter/aware_graph" not in _meta_graph_authored_render()
