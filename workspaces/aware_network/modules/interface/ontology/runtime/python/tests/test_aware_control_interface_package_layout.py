from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import warnings
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest
from aware_interface.builder import (
    ApiViewActionTruth,
    ApiViewStateTruth,
    PaneRenderSpecCompatibilityWarning,
    build_interface_compile_plan,
    build_interface_config_bundle,
    build_projection_identity_catalog_from_ocg,
    build_state_model_catalog_from_ocg,
    emit_interface_config_bundle_artifact,
    emit_interface_dart_pane_registrar_bundle_artifact,
    emit_interface_pane_render_spec_materialization_artifact,
    _hydrate_projection_view_invocation_actions,
    _normalize_dart_pane_state_bindings,
    _resolve_dart_pane_action_binding,
    _resolve_state_attribute_config_id,
)
from aware_interface.manifest import (
    AwareInterfaceTomlSpec,
    load_aware_interface_toml_spec,
)
from aware_interface.workspace import InterfaceWorkspace
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
    InterfacePaneConfigBundle,
    InterfacePaneProjectionExperienceViewBundle,
)
from aware_interface_ontology.stable_ids import (
    stable_interface_config_id,
    stable_interface_package_id,
)
from aware_experience.compiler.models import (
    ExperienceProjectionViewInvocationActionOwnership,
    ExperienceProjectionViewOwnership,
)
from aware_meta_ontology.stable_ids import stable_attribute_config_id
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from _interface_runtime_test_paths import REPO_ROOT


@dataclass(frozen=True, slots=True)
class _AwareControlBundleFixture:
    repo_root: Path
    package_root: Path
    spec_path: Path
    spec: AwareInterfaceTomlSpec
    config_bundle_path: Path


def _aware_control_paths() -> tuple[Path, Path]:
    repo_root = REPO_ROOT.resolve()
    return (
        repo_root,
        repo_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "interface"
        / "interfaces"
        / "aware_control"
        / "aware.interface.toml",
    )


def _load_bundle() -> tuple[_AwareControlBundleFixture, InterfaceConfigBundle]:
    repo_root, interface_toml_path = _aware_control_paths()
    workspace = InterfaceWorkspace.from_toml(
        toml_path=interface_toml_path,
        repo_root=repo_root,
    )
    spec = load_aware_interface_toml_spec(toml_path=interface_toml_path)
    config_bundle_path = (
        workspace.package_root / spec.build.config_bundle_path
    ).resolve()
    bundle = InterfaceConfigBundle.model_validate_json(
        config_bundle_path.read_text(encoding="utf-8")
    )
    return (
        _AwareControlBundleFixture(
            repo_root=workspace.repo_root,
            package_root=workspace.package_root,
            spec_path=workspace.spec_path,
            spec=spec,
            config_bundle_path=config_bundle_path,
        ),
        bundle,
    )


def _build_projection_identity_ocg() -> ObjectConfigGraph:
    projection_specs = (
        ("Identity", "aware_identity.identity.Identity"),
        ("aware_control_identity", "aware_identity.identity.Identity"),
        ("CodePackage", "aware_code.package.CodePackage"),
        ("aware_hub", "aware_code.package.CodePackage"),
        ("NetworkNode", "aware_network.network.NetworkNode"),
        ("aware_network", "aware_network.network.NetworkNode"),
        ("Workspace", "aware_workspace.workspace.Workspace"),
        ("aware_workspace", "aware_workspace.workspace.Workspace"),
        ("Agent", "aware_agent.agent.Agent"),
        ("aware_agent_terminal", "aware_agent.agent.Agent"),
    )
    ocg_id = uuid5(NAMESPACE_URL, "aware://interface-clean-rail/test-ocg")
    identities: list[dict[str, object]] = []
    graphs: list[dict[str, object]] = []
    for projection_name, class_fqn in projection_specs:
        graph_id = uuid5(
            NAMESPACE_URL,
            f"aware://interface-clean-rail/test-opg/{projection_name}",
        )
        identities.append(
            {
                "id": str(
                    uuid5(
                        NAMESPACE_URL,
                        f"aware://interface-clean-rail/test-opgi/{projection_name}",
                    )
                ),
                "projection_name": projection_name,
                "label": f"opg:{projection_name}",
                "is_branchable": True,
                "object_config_graph_identity_id": str(ocg_id),
                "object_projection_graph_id": str(graph_id),
            }
        )
        class_id = uuid5(
            NAMESPACE_URL,
            f"aware://interface-clean-rail/test-class/{class_fqn}",
        )
        graphs.append(
            {
                "id": str(graph_id),
                "object_config_graph_id": str(ocg_id),
                "name": projection_name,
                "projection_hash": f"sha256:{graph_id.hex}",
                "language": "aware",
                "object_projection_graph_nodes": [
                    {
                        "id": str(
                            uuid5(
                                NAMESPACE_URL,
                                "aware://interface-clean-rail/test-opg-node/"
                                + projection_name,
                            )
                        ),
                        "object_projection_graph_id": str(graph_id),
                        "class_config_id": str(class_id),
                        "is_root": True,
                        "class_config": {
                            "id": str(class_id),
                            "class_fqn": class_fqn,
                            "name": class_fqn.rsplit(".", 1)[-1],
                        },
                    }
                ],
            }
        )
    return ObjectConfigGraph.model_validate(
        {
            "id": str(ocg_id),
            "name": "Interface clean rail test projection identities",
            "hash": "sha256:interface-clean-rail-test-projection-identities",
            "fqn_prefix": "aware_interface_clean_rail_tests",
            "language": "aware",
            "object_config_graph_identity_id": str(ocg_id),
            "object_config_graph_identity": {
                "id": str(ocg_id),
                "key": "aware_interface_clean_rail_tests",
                "label": "Interface clean rail test projection identities",
                "object_projection_graph_identities": identities,
            },
            "object_projection_graphs": graphs,
        }
    )


def _api_view_action_truth(
    *,
    view_ref: str,
    action_key: str,
    endpoint_ref: str,
) -> ApiViewActionTruth:
    return ApiViewActionTruth(
        action_key=action_key,
        endpoint_ref=endpoint_ref,
        api_view_capability_endpoint_id=uuid5(
            NAMESPACE_URL,
            f"aware://tests/aware-control/api-view-capability-endpoint/{view_ref}/{action_key}",
        ),
        api_capability_endpoint_id=uuid5(
            NAMESPACE_URL,
            f"aware://tests/aware-control/api-capability-endpoint/{endpoint_ref}",
        ),
    )


def _api_view_state_truth(
    *,
    view_ref: str,
    state_model_ref: str,
    actions: tuple[ApiViewActionTruth, ...] = (),
) -> ApiViewStateTruth:
    return ApiViewStateTruth(
        view_ref=view_ref,
        state_model_ref=state_model_ref,
        state_model_id=uuid5(
            NAMESPACE_URL,
            f"aware://tests/aware-control/api-view-state-model/{view_ref}",
        ),
        action_endpoints_by_key={
            action.action_key.casefold(): action for action in actions
        },
    )


def _aware_control_api_view_catalog() -> dict[str, ApiViewStateTruth]:
    return {
        "identity.identity_admission": _api_view_state_truth(
            view_ref="identity.identity_admission",
            state_model_ref="aware_identity_service_dto.identity.IdentityAdmissionViewStateV1",
            actions=(
                _api_view_action_truth(
                    view_ref="identity.identity_admission",
                    action_key="admit_identity",
                    endpoint_ref="identity.signup_via_profile.signup_via_profile",
                ),
            ),
        ),
        "hub.channel_heads": _api_view_state_truth(
            view_ref="hub.channel_heads",
            state_model_ref="aware_hub_service_dto.hub.view.HubPublicDiscoveryViewStateV1",
            actions=(
                _api_view_action_truth(
                    view_ref="hub.channel_heads",
                    action_key="describe_package",
                    endpoint_ref="hub.code_package.describe",
                ),
                _api_view_action_truth(
                    view_ref="hub.channel_heads",
                    action_key="discover_channel_heads",
                    endpoint_ref="hub.code_package.discover_channel_heads",
                ),
                _api_view_action_truth(
                    view_ref="hub.channel_heads",
                    action_key="download_package",
                    endpoint_ref="hub.code_package.download",
                ),
                _api_view_action_truth(
                    view_ref="hub.channel_heads",
                    action_key="resolve_deployment_artifact",
                    endpoint_ref="hub.deployment_artifact.resolve",
                ),
                _api_view_action_truth(
                    view_ref="hub.channel_heads",
                    action_key="resolve_package",
                    endpoint_ref="hub.code_package.resolve",
                ),
                _api_view_action_truth(
                    view_ref="hub.channel_heads",
                    action_key="search_packages",
                    endpoint_ref="hub.code_package.search",
                ),
            ),
        ),
        "network.territory_discovery": _api_view_state_truth(
            view_ref="network.territory_discovery",
            state_model_ref="aware_network_service_dto.comms.view.NetworkTerritoryDiscoveryViewStateV1",
            actions=(
                _api_view_action_truth(
                    view_ref="network.territory_discovery",
                    action_key="discover_territory",
                    endpoint_ref="network.discovery.discover_territory",
                ),
                _api_view_action_truth(
                    view_ref="network.territory_discovery",
                    action_key="list_environments",
                    endpoint_ref="network.environment.list",
                ),
                _api_view_action_truth(
                    view_ref="network.territory_discovery",
                    action_key="list_hosted_services",
                    endpoint_ref="network.hosted_service.list",
                ),
                _api_view_action_truth(
                    view_ref="network.territory_discovery",
                    action_key="list_peers",
                    endpoint_ref="network.peer.list",
                ),
            ),
        ),
    }


def _aware_control_state_attribute_catalog() -> dict[str, dict[str, UUID]]:
    identity_state_model_ref = (
        "aware_identity_service_dto.identity.IdentityAdmissionViewStateV1"
    )
    network_state_model_ref = (
        "aware_network_service_dto.comms.view.NetworkTerritoryDiscoveryViewStateV1"
    )
    return {
        identity_state_model_ref: _state_attribute_ids(
            owner_key=identity_state_model_ref,
            attribute_names=(
                "status",
                "status_tone",
                "display_name",
                "public_handle",
                "bio",
                "provenance",
            ),
        ),
        network_state_model_ref: _state_attribute_ids(
            owner_key=network_state_model_ref,
            attribute_names=(
                "status",
                "summary",
                "error",
                "nodes",
                "empty_message",
                "authority_source_url",
            ),
        ),
    }


def _state_attribute_ids(
    *,
    owner_key: str,
    attribute_names: tuple[str, ...],
) -> dict[str, UUID]:
    return {
        attribute_name.casefold(): stable_attribute_config_id(
            owner_key=owner_key,
            name=attribute_name,
        )
        for attribute_name in attribute_names
    }


def _view_action_target_refs(
    bundle: InterfaceConfigBundle, pane_name: str
) -> tuple[str, ...]:
    view = _projection_view(bundle, pane_name)
    return tuple(str(action.target_ref) for action in view.invocation_actions)


def _projection_view(
    bundle: InterfaceConfigBundle,
    pane_name: str,
) -> InterfacePaneProjectionExperienceViewBundle:
    pane = next(pane for pane in bundle.pane_configs if pane.name == pane_name)
    assert len(pane.projection_experience_views) == 1
    return pane.projection_experience_views[0]


def _pane_config(
    bundle: InterfaceConfigBundle,
    pane_name: str,
) -> InterfacePaneConfigBundle:
    return next(pane for pane in bundle.pane_configs if pane.name == pane_name)


def test_pane_render_builder_preserves_equals_transform() -> None:
    bindings = _normalize_dart_pane_state_bindings(
        raw_bindings=[
            {
                "binding_key": "status_equals",
                "target_property": "visible",
                "json_path": "$.status",
                "transform": "equals",
            }
        ],
        state_model_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        state_model_ref="test.state",
        state_attribute_ids_by_ref={},
        source_path=Path("pane.render.json"),
        node_key="root",
    )

    assert bindings[0]["binding_key"] == "status_equals"
    assert bindings[0]["transform"] == "equals"


def _assert_dart_package_codegen_outputs_exist(package_root: Path) -> None:
    missing_outputs: list[str] = []
    part_pattern = re.compile(r"^part '([^']+\.(?:freezed|g)\.dart)';$")

    for source_path in sorted((package_root / "lib").rglob("*.dart")):
        if source_path.name.endswith((".freezed.dart", ".g.dart")):
            continue
        for line in source_path.read_text(encoding="utf-8").splitlines():
            match = part_pattern.match(line.strip())
            if match is None:
                continue
            output_path = source_path.parent / match.group(1)
            if not output_path.exists():
                missing_outputs.append(str(output_path.relative_to(package_root)))

    assert missing_outputs == []


def test_aware_control_interface_package_loads_canonical_bundle() -> None:
    repo_root, interface_toml_path = _aware_control_paths()
    snapshot, bundle = _load_bundle()

    assert snapshot.repo_root == repo_root
    assert (
        snapshot.package_root
        == (
            repo_root
            / "workspaces"
            / "aware_network"
            / "modules"
            / "interface"
            / "interfaces"
            / "aware_control"
        ).resolve()
    )
    assert snapshot.spec_path == interface_toml_path.resolve()
    assert snapshot.spec.interface.package_name == "aware-control-interface"
    assert snapshot.spec.interface.fqn_prefix == "aware_control_interface"
    assert (
        snapshot.config_bundle_path
        == (
            repo_root
            / "workspaces"
            / "aware_network"
            / "modules"
            / "interface"
            / "interfaces"
            / "aware_control"
            / "bundles"
            / "interface.config.bundle.json"
        ).resolve()
    )

    assert bundle.interface_package_id == stable_interface_package_id(
        name="aware-control-interface"
    )
    assert bundle.interface_package_name == "aware-control-interface"
    assert bundle.interface_config_id == stable_interface_config_id(
        name="aware_control"
    )
    assert bundle.name == "aware_control"
    assert bundle.apis == []
    assert [pane.name for pane in bundle.pane_configs] == [
        "identity_admission",
        "hub_package_selector",
        "network_territory",
    ]
    assert tuple(
        _projection_view(bundle, pane_name).view_ref
        for pane_name in [
            "identity_admission",
            "hub_package_selector",
            "network_territory",
        ]
    ) == (
        "aware_control_identity.identity.admission.v1",
        "aware_hub.home.channel_heads.v1",
        "aware_network.territory.discovery.v1",
    )


def test_aware_control_interface_pubspec_uses_api_view_state_packages() -> None:
    repo_root, _ = _aware_control_paths()
    pubspec_path = (
        repo_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "interface"
        / "interfaces"
        / "aware_control"
        / "dart"
        / "aware_control_interface"
        / "pubspec.yaml"
    )
    pubspec = pubspec_path.read_text(encoding="utf-8")

    assert "aware_hub_service_api:" in pubspec
    assert "path: ../../../../../hub/apis/hub/dart/aware_hub_service_api" in pubspec
    assert "aware_network_service_api:" in pubspec
    assert (
        "path: ../../../../../network/apis/network/dart/aware_network_service_api"
        in pubspec
    )
    assert "aware_control:" not in pubspec
    assert "aware_hub:" not in pubspec
    assert "aware_network_experience:" not in pubspec


def test_aware_control_interface_compile_emits_provider_backed_view_contract(
    tmp_path: Path,
) -> None:
    repo_root, interface_toml_path = _aware_control_paths()
    snapshot = InterfaceWorkspace.from_toml(
        toml_path=interface_toml_path,
        repo_root=repo_root,
    ).build_snapshot()
    plan = build_interface_compile_plan(snapshot=snapshot)
    projection_identity_ocg = _build_projection_identity_ocg()
    projection_catalog = build_projection_identity_catalog_from_ocg(
        ocg=projection_identity_ocg,
    )
    state_model_catalog = build_state_model_catalog_from_ocg(
        ocg=projection_identity_ocg,
    )
    api_view_catalog = _aware_control_api_view_catalog()
    state_attribute_catalog = _aware_control_state_attribute_catalog()

    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        render_spec_materialization_artifact = (
            emit_interface_pane_render_spec_materialization_artifact(
                snapshot=snapshot,
                plan=plan,
                runtime_package_dir=tmp_path / "runtime" / "aware-control-interface",
                repo_root=tmp_path,
                projection_catalog=projection_catalog,
                state_model_catalog=state_model_catalog,
                api_view_catalog=api_view_catalog,
                state_attribute_catalog=state_attribute_catalog,
            )
        )
        config_bundle = build_interface_config_bundle(
            snapshot=snapshot,
            plan=plan,
            projection_catalog=projection_catalog,
            state_model_catalog=state_model_catalog,
            api_view_catalog=api_view_catalog,
            state_attribute_catalog=state_attribute_catalog,
        )
        config_bundle_artifact = emit_interface_config_bundle_artifact(
            bundle=config_bundle,
            config_bundle_path=tmp_path / "bundles" / "interface.config.bundle.json",
            repo_root=tmp_path,
        )
        dart_registrar_bundle_artifact = emit_interface_dart_pane_registrar_bundle_artifact(
            snapshot=snapshot,
            plan=plan,
            dart_package_dir=tmp_path / "dart" / "aware_control_interface",
            repo_root=tmp_path,
            projection_catalog=projection_catalog,
            state_model_catalog=state_model_catalog,
            api_view_catalog=api_view_catalog,
            state_attribute_catalog=state_attribute_catalog,
            render_spec_materialization_path=render_spec_materialization_artifact.path,
        )

    assert not [
        warning
        for warning in caught_warnings
        if issubclass(warning.category, PaneRenderSpecCompatibilityWarning)
    ]
    assert snapshot.pane_render_spec_files == ()

    materialized = json.loads(
        render_spec_materialization_artifact.path.read_text(encoding="utf-8")
    )
    assert materialized["schema_version"] == 2
    assert (
        materialized["materialization_kind"]
        == "aware.interface.pane-render-spec.materialization.v1"
    )
    assert len(materialized["materialization_commit_id"]) == 36
    assert len(materialized["materialization_content_hash_sha256"]) == 64
    identity_render = next(
        item
        for item in materialized["render_specs"]
        if item["pane_name"] == "identity_admission"
    )
    assert identity_render["source_kind"] == "authored_aware"
    assert (
        identity_render["source_path"]
        == "workspaces/aware_network/modules/identity/interfaces/panes/"
        "identity_admission/identity_admission.aware#render:default"
    )
    assert identity_render["render_spec_id"] == identity_render["payload"]["spec_id"]
    assert len(identity_render["render_spec_content_hash_sha256"]) == 64
    assert (
        identity_render["semantic_object_ids"]["pane_render_spec_id"]
        == identity_render["payload"]["spec_id"]
    )
    assert identity_render["payload"]["name"] == "identity_admission_default"
    identity_nodes = {
        node["node_key"]: node for node in identity_render["payload"]["nodes"]
    }
    status_bindings = identity_nodes["status"]["state_bindings"]
    assert [binding["target_property"] for binding in status_bindings] == [
        "text",
        "tone",
    ]
    assert status_bindings[1]["binding_key"] == "status_tone"
    assert status_bindings[1]["json_path"] == "$.status_tone"
    assert status_bindings[1]["state_attribute_ref"] == "status_tone"
    network_render = next(
        item
        for item in materialized["render_specs"]
        if item["pane_name"] == "network_territory"
    )
    assert network_render["source_kind"] == "authored_aware"
    assert (
        network_render["source_path"]
        == "workspaces/aware_network/modules/network/interfaces/panes/"
        "network_territory/network_territory.aware#render:default"
    )
    network_nodes = {
        node["node_key"]: node for node in network_render["payload"]["nodes"]
    }
    assert network_nodes["root.summary"]["node_kind"] == "field"
    network_refresh_action = network_nodes["root.refresh"]["action_bindings"][0]
    assert network_refresh_action["action_key"] == "discover_territory"
    assert network_refresh_action["action_kind"] == "api"
    assert network_refresh_action["view_action_key"] == "discover_territory"
    assert network_refresh_action["target_ref"] == (
        "network.discovery.discover_territory"
    )
    assert network_refresh_action["endpoint_ref"] == (
        "network.discovery.discover_territory"
    )
    empty_visible_binding = network_nodes["root.empty_message"]["state_bindings"][0]
    assert empty_visible_binding["binding_key"] == "nodes_visible"
    assert empty_visible_binding["target_property"] == "visible"
    assert empty_visible_binding["json_path"] == "$.nodes"
    assert empty_visible_binding["state_attribute_ref"] == "nodes"
    assert empty_visible_binding["transform"] == "is_empty"
    assert network_nodes["root.nodes"]["node_kind"] == "repeat"
    assert (
        network_nodes["root.nodes"]["state_bindings"][0]["target_property"] == "items"
    )
    assert (
        network_nodes["root.nodes"]["state_bindings"][0]["state_attribute_ref"]
        == "nodes"
    )
    assert network_nodes["root.nodes.card"]["node_kind"] == "list_item"
    assert (
        network_nodes["root.nodes.card.metrics.environments"]["state_bindings"][0][
            "transform"
        ]
        == "count"
    )
    assert (
        network_nodes["root.nodes.card.metrics.environments"]["node_kind"] == "metric"
    )
    assert (
        network_nodes["root.nodes.card.environments_header"]["node_kind"]
        == "section_header"
    )
    assert network_nodes["root.nodes.card.environments"]["node_kind"] == "repeat"
    assert (
        network_nodes["root.nodes.card.environments"]["state_bindings"][0]["json_path"]
        == "$.item.environments"
    )
    assert (
        network_nodes["root.nodes.card.environments.row"]["state_bindings"][0][
            "json_path"
        ]
        == "$.item.environment_title"
    )
    assert network_nodes["root.nodes.card.hosted_services"]["node_kind"] == "repeat"
    assert (
        network_nodes["root.nodes.card.hosted_services"]["state_bindings"][0][
            "json_path"
        ]
        == "$.item.hosted_services"
    )
    assert (
        network_nodes["root.nodes.card.hosted_services.row"]["state_bindings"][0][
            "json_path"
        ]
        == "$.item.service_name"
    )
    assert network_nodes["root.nodes.card.peers"]["node_kind"] == "repeat"
    assert (
        network_nodes["root.nodes.card.peers"]["state_bindings"][0]["json_path"]
        == "$.item.peers"
    )
    assert (
        network_nodes["root.nodes.card.peers.row"]["state_bindings"][0]["json_path"]
        == "$.item.peer_base_url"
    )
    bundle = InterfaceConfigBundle.model_validate_json(
        config_bundle_artifact.path.read_text(encoding="utf-8")
    )
    identity_view = _projection_view(bundle, "identity_admission")
    assert identity_view.view_ref == "aware_control_identity.identity.admission.v1"
    assert identity_view.projection_view_key == "identity.admission.v1"
    assert identity_view.state_model_id is not None
    hub_view = _projection_view(bundle, "hub_package_selector")
    assert hub_view.view_ref == "aware_hub.home.channel_heads.v1"
    assert hub_view.projection_view_key == "home.channel_heads.v1"
    assert hub_view.state_model_id is not None
    network_view = _projection_view(bundle, "network_territory")
    assert network_view.view_ref == "aware_network.territory.discovery.v1"
    assert network_view.projection_view_key == "territory.discovery.v1"
    assert network_view.state_model_id is not None
    dart_payload = dart_registrar_bundle_artifact.path.read_text(encoding="utf-8")
    assert "viewRef: 'aware_control_identity.identity.admission.v1'" in dart_payload
    assert "projectionViewKey: 'identity.admission.v1'" in dart_payload
    assert "viewRef: 'aware_hub.home.channel_heads.v1'" in dart_payload
    assert "projectionViewKey: 'home.channel_heads.v1'" in dart_payload
    assert "viewRef: 'aware_network.territory.discovery.v1'" in dart_payload
    assert "projectionViewKey: 'territory.discovery.v1'" in dart_payload
    assert "renderSpecs: <PaneRenderSpec>[" in dart_payload
    assert '"name": "identity_admission_default"' in dart_payload
    assert '"pane_kind": "identity_admission"' in dart_payload
    assert '"name": "network_territory_default"' in dart_payload
    assert '"pane_kind": "network_territory"' in dart_payload
    assert '"node_kind": "repeat"' in dart_payload
    assert '"node_kind": "field"' in dart_payload
    assert '"node_kind": "list_item"' in dart_payload
    assert '"node_kind": "metric"' in dart_payload
    assert '"node_kind": "section_header"' in dart_payload
    assert '"node_kind": "component"' in dart_payload
    assert '"component_ref": "aware.content.markdown_viewer"' in dart_payload
    assert '"component_input_port_key": "markdown"' in dart_payload
    assert '"target_property": "items"' in dart_payload
    assert '"transform": "count"' in dart_payload
    assert '"transform": "is_empty"' in dart_payload
    assert '"json_path": "\\$.item.environments"' in dart_payload
    assert '"json_path": "\\$.item.hosted_services"' in dart_payload
    assert '"json_path": "\\$.item.peers"' in dart_payload
    assert '"json_path": "\\$.item.peer_base_url"' in dart_payload
    assert f'"state_model_id": "{identity_view.state_model_id}"' in dart_payload
    state_model_ref = "aware_identity_service_dto.identity.IdentityAdmissionViewStateV1"
    for attribute_name in (
        "status",
        "status_tone",
        "display_name",
        "public_handle",
        "bio",
        "provenance",
    ):
        assert f'"state_attribute_ref": "{attribute_name}"' in dart_payload
        assert (
            f'"state_attribute_config_id": '
            f'"{stable_attribute_config_id(owner_key=state_model_ref, name=attribute_name)}"'
            in dart_payload
        )
    assert '"action_key": "admit_identity"' in dart_payload
    assert '"action_kind": "api"' in dart_payload
    assert (
        '"endpoint_ref": "identity.signup_via_profile.signup_via_profile"'
        in dart_payload
    )
    assert '"view_action_key": "admit_identity"' in dart_payload
    assert '"action_key": "discover_territory"' in dart_payload
    assert '"action_kind": "api"' in dart_payload
    assert '"view_action_key": "discover_territory"' in dart_payload
    assert '"target_ref": "network.discovery.discover_territory"' in dart_payload
    assert "sdk_operation_id" not in dart_payload
    assert "api_capability_endpoint_id" not in dart_payload
    assert "pane_config_sdk_operation_id" not in dart_payload
    assert "pane_config_api_capability_endpoint_id" not in dart_payload
    assert "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa" not in dart_payload
    assert (
        "package:aware_hub_service_api/aware_hub_service_api.dart"
        in dart_payload
    )
    assert (
        "package:aware_network_service_api/aware_network_service_api.dart"
        in dart_payload
    )
    assert "aware_hub.awareHubViewModelDecoders" not in dart_payload
    assert (
        "aware_network_experience.awareNetworkExperienceViewModelDecoders"
        not in dart_payload
    )
    assert (
        '"aware_hub.home.channel_heads.v1": '
        "aware_hub_service_api.HubPublicDiscoveryViewStateV1.fromJson"
        in dart_payload
    )
    assert (
        '"home.channel_heads.v1": '
        "aware_hub_service_api.HubPublicDiscoveryViewStateV1.fromJson"
        in dart_payload
    )
    assert (
        '"hub.channel_heads": '
        "aware_hub_service_api.HubPublicDiscoveryViewStateV1.fromJson"
        in dart_payload
    )
    assert (
        '"aware_network.territory.discovery.v1": '
        "aware_network_service_api.NetworkTerritoryDiscoveryViewStateV1.fromJson"
        in dart_payload
    )
    assert (
        '"territory.discovery.v1": '
        "aware_network_service_api.NetworkTerritoryDiscoveryViewStateV1.fromJson"
        in dart_payload
    )
    assert (
        '"network.territory_discovery": '
        "aware_network_service_api.NetworkTerritoryDiscoveryViewStateV1.fromJson"
        in dart_payload
    )
    assert "aware_content_render_components.registerRenderComponents" in dart_payload
    assert "aware_control.identity_admission.main" not in dart_payload
    assert "package:aware_api/aware_api.dart" not in dart_payload
    assert "package:aware_identity_service_api/" not in dart_payload
    assert "apiPackages:" not in dart_payload
    assert "apiClientFactories:" not in dart_payload


def test_pane_render_spec_state_attribute_ref_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="unknown state attribute"):
        _resolve_state_attribute_config_id(
            source_path=Path("pane.render_spec.json"),
            binding_key="missing",
            state_model_ref=(
                "aware_control.views.identity.admission.v1."
                "IdentityAdmissionViewStateV1"
            ),
            state_attribute_ref="missing_attribute",
            state_attribute_config_id=None,
            state_attribute_ids_by_ref={
                "status": UUID("0f345d90-ed11-57e3-b894-e0e234afc051")
            },
        )


def test_pane_render_spec_rejects_direct_action_without_view_action() -> None:
    projection_experience_id = UUID("aaaaaaaa-aaaa-5aaa-9aaa-aaaaaaaaaaa0")
    projection_experience_view_id = UUID("aaaaaaaa-aaaa-5aaa-9aaa-aaaaaaaaaaa1")

    with pytest.raises(ValueError, match="without view_action_key"):
        _resolve_dart_pane_action_binding(
            action_key="admit_identity",
            view_action_key=None,
            sdk_operation_ref=None,
            api_endpoint_ref=None,
            projection_view_actions={},
            api_view_truth=_identity_admission_api_view_truth(),
            projection_experience_id=projection_experience_id,
            projection_experience_view_id=projection_experience_view_id,
            source_path=Path("pane.render_spec.json"),
            binding_key="direct_action_key",
        )


def test_pane_render_spec_rejects_direct_api_target() -> None:
    projection_experience_id = UUID("aaaaaaaa-aaaa-5aaa-9aaa-aaaaaaaaaaa0")
    projection_experience_view_id = UUID("aaaaaaaa-aaaa-5aaa-9aaa-aaaaaaaaaaa2")

    with pytest.raises(ValueError, match="direct API/SDK pane targets"):
        _resolve_dart_pane_action_binding(
            action_key="admit_identity",
            view_action_key=None,
            sdk_operation_ref=None,
            api_endpoint_ref="identity.signup_via_profile.signup_via_profile",
            projection_view_actions={},
            api_view_truth=_identity_admission_api_view_truth(),
            projection_experience_id=projection_experience_id,
            projection_experience_view_id=projection_experience_view_id,
            source_path=Path("pane.render_spec.json"),
            binding_key="admit_identity",
        )


def test_api_view_action_truth_hydrates_experience_view_action_for_panes() -> None:
    projection_experience_id = UUID("aaaaaaaa-aaaa-5aaa-9aaa-aaaaaaaaaaa0")
    projection_experience_view_id = UUID("aaaaaaaa-aaaa-5aaa-9aaa-aaaaaaaaaaa4")
    actions = _hydrate_projection_view_invocation_actions(
        view=ExperienceProjectionViewOwnership(
            key="admission.v1",
            is_default=True,
            source_path="identity/experiences/aware_actor/experiences.aware",
            api_view_ref="identity.identity_admission",
        ),
        api_view_truth=_identity_admission_api_view_truth(),
        view_ref="aware_control_identity.identity.admission.v1",
    )
    assert tuple(action.key for action in actions) == ("admit_identity",)

    binding = _resolve_dart_pane_action_binding(
        action_key=None,
        view_action_key="admit_identity",
        sdk_operation_ref=None,
        api_endpoint_ref=None,
        projection_view_actions={action.key.casefold(): action for action in actions},
        api_view_truth=_identity_admission_api_view_truth(),
        projection_experience_id=projection_experience_id,
        projection_experience_view_id=projection_experience_view_id,
        source_path=Path("pane.render_spec.json"),
        binding_key="admit_identity",
    )

    assert binding["action_key"] == "admit_identity"
    assert binding["action_kind"] == "api"
    assert binding["view_action_key"] == "admit_identity"
    assert binding["target_ref"] == "identity.signup_via_profile.signup_via_profile"
    assert binding["endpoint_ref"] == "identity.signup_via_profile.signup_via_profile"
    assert "projection_experience_view_invocation_action_id" in binding


def test_target_bearing_experience_action_still_hydrates_api_view_identity() -> None:
    api_view_truth = _identity_admission_api_view_truth()
    actions = _hydrate_projection_view_invocation_actions(
        view=ExperienceProjectionViewOwnership(
            key="admission.v1",
            is_default=True,
            source_path="identity/experiences/aware_actor/experiences.aware",
            api_view_ref="identity.identity_admission",
            invocation_actions=(
                ExperienceProjectionViewInvocationActionOwnership(
                    key="admit_identity",
                    source_path="identity/experiences/aware_actor/experiences.aware",
                    endpoint_ref="identity.signup_via_profile.signup_via_profile",
                ),
            ),
        ),
        api_view_truth=api_view_truth,
        view_ref="aware_control_identity.identity.admission.v1",
    )

    assert len(actions) == 1
    assert actions[0].api_view_capability_endpoint_id == (
        api_view_truth.action_endpoints_by_key[
            "admit_identity"
        ].api_view_capability_endpoint_id
    )


def _identity_admission_api_view_truth() -> ApiViewStateTruth:
    return ApiViewStateTruth(
        view_ref="identity.identity_admission",
        state_model_ref="aware_identity_service_dto.identity.IdentityAdmissionViewStateV1",
        state_model_id=UUID("bbbbbbbb-bbbb-5bbb-9bbb-bbbbbbbbbbb0"),
        action_endpoints_by_key={
            "admit_identity": ApiViewActionTruth(
                action_key="admit_identity",
                endpoint_ref="identity.signup_via_profile.signup_via_profile",
                api_view_capability_endpoint_id=UUID(
                    "bbbbbbbb-bbbb-5bbb-9bbb-bbbbbbbbbbb1"
                ),
                api_capability_endpoint_id=UUID("bbbbbbbb-bbbb-5bbb-9bbb-bbbbbbbbbbb2"),
            )
        },
    )


def test_production_panes_do_not_declare_direct_api_or_sdk_actions() -> None:
    repo_root, _ = _aware_control_paths()
    direct_action_pattern = re.compile(r"\baction\s+\w+\s+(api|sdk)\s+")
    offenders: list[str] = []
    source_roots = (
        repo_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "identity"
        / "interfaces"
        / "panes",
        repo_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "hub"
        / "interfaces"
        / "panes",
        repo_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "network"
        / "interfaces"
        / "panes",
        repo_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "meta"
        / "interfaces"
        / "panes",
    )

    for source_root in source_roots:
        for source_path in sorted(source_root.rglob("*.aware")):
            lines = source_path.read_text(encoding="utf-8").splitlines()
            for line_number, line in enumerate(lines, start=1):
                if direct_action_pattern.search(line):
                    offenders.append(
                        f"{source_path.relative_to(repo_root)}:{line_number}: {line.strip()}"
                    )

    assert offenders == []


def test_aware_control_discovery_uses_api_view_mounted_panes_with_experience_actions() -> (
    None
):
    _, bundle = _load_bundle()

    assert _view_action_target_refs(bundle, "network_territory") == (
        "network.discovery.discover_territory",
        "network.environment.list",
        "network.hosted_service.list",
        "network.peer.list",
    )
    assert _view_action_target_refs(bundle, "identity_admission") == (
        "identity.signup_via_profile.signup_via_profile",
    )
    hub_targets = _view_action_target_refs(bundle, "hub_package_selector")
    assert "hub.code_package.discover_channel_heads" in hub_targets
    assert "hub.code_package.search" in hub_targets

    identity_pane = _pane_config(bundle, "identity_admission")
    identity_view = _projection_view(bundle, "identity_admission")
    assert identity_pane.pane_package_name == "aware-identity-admission-pane"
    assert identity_view.view_ref == "aware_control_identity.identity.admission.v1"
    assert identity_view.projection_view_key == "identity.admission.v1"
    assert identity_view.state_model_id is not None
    hub_pane = _pane_config(bundle, "hub_package_selector")
    hub_view = _projection_view(bundle, "hub_package_selector")
    assert hub_pane.pane_package_name == "aware-hub-package-selector-pane"
    assert hub_view.view_ref == "aware_hub.home.channel_heads.v1"
    assert hub_view.projection_view_key == "home.channel_heads.v1"
    assert hub_view.state_model_id is not None
    network_pane = _pane_config(bundle, "network_territory")
    network_view = _projection_view(bundle, "network_territory")
    assert network_pane.pane_package_name == "aware-network-territory-pane"
    assert network_view.view_ref == "aware_network.territory.discovery.v1"
    assert network_view.projection_view_key == "territory.discovery.v1"
    assert network_view.state_model_id is not None
